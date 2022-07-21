from argo_workflows.api import workflow_service_api
from argo_workflows.model.container import Container
from argo_workflows.model.io_argoproj_workflow_v1alpha1_template import IoArgoprojWorkflowV1alpha1Template
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow import IoArgoprojWorkflowV1alpha1Workflow
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_create_request import IoArgoprojWorkflowV1alpha1WorkflowCreateRequest
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_spec import IoArgoprojWorkflowV1alpha1WorkflowSpec
from argo_workflows.model.object_meta import ObjectMeta

# new 
from argo_workflows.model.config_map_key_selector import ConfigMapKeySelector

from argo_workflows.model.io_argoproj_workflow_v1alpha1_arguments import IoArgoprojWorkflowV1alpha1Arguments
from argo_workflows.model.io_argoproj_workflow_v1alpha1_artifact import IoArgoprojWorkflowV1alpha1Artifact
from argo_workflows.model.io_argoproj_workflow_v1alpha1_cache import IoArgoprojWorkflowV1alpha1Cache
from argo_workflows.model.io_argoproj_workflow_v1alpha1_inputs import IoArgoprojWorkflowV1alpha1Inputs
from argo_workflows.model.io_argoproj_workflow_v1alpha1_memoize import IoArgoprojWorkflowV1alpha1Memoize
from argo_workflows.model.io_argoproj_workflow_v1alpha1_outputs import IoArgoprojWorkflowV1alpha1Outputs
from argo_workflows.model.io_argoproj_workflow_v1alpha1_parallel_steps import IoArgoprojWorkflowV1alpha1ParallelSteps
from argo_workflows.model.io_argoproj_workflow_v1alpha1_parameter import IoArgoprojWorkflowV1alpha1Parameter
from argo_workflows.model.io_argoproj_workflow_v1alpha1_value_from import IoArgoprojWorkflowV1alpha1ValueFrom
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_step import IoArgoprojWorkflowV1alpha1WorkflowStep

from argo_workflows.model.persistent_volume_claim_volume_source import PersistentVolumeClaimVolumeSource
from argo_workflows.model.volume import Volume
from argo_workflows.model.volume_mount import VolumeMount

from pprint import pprint
from utils import *

import argo_workflows
import json
import requests  
import time

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) # make sure to remove this later in production

def define_workflow(parameter1, parameter2, parameter3, workflow_name):

    """
    Define Argo Workflow using Python SDK
    """
    manifest = IoArgoprojWorkflowV1alpha1Workflow(
        # metadata=ObjectMeta(generate_name='sdk-memoize-multistep-'),
        metadata=ObjectMeta(name=workflow_name), 
        spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
            entrypoint='entry-template',
            volumes=[Volume(name="workdir", 
                persistent_volume_claim=PersistentVolumeClaimVolumeSource(
                    claim_name="argo-pv-claim")
                )
            ], 
            templates=[
                # <--- TEMPLATE 1 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='entry-template',
                    steps=[ IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 1
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="generate-artifact",
                                    template="template1")]),
                            IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 2
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="pass-artifact1",
                                    template="template2",
                                    arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                            # name="artifact1",_from="{0}".format(parameter2))]
                                            name="artifact1",_from="{{steps.generate-artifact.outputs.artifacts.hello}}")]
                                        )
                                    )]),
                            IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 3
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="pass-artifact2",
                                    template="template3",
                                    arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                            name="artifact2",_from="{{steps.pass-artifact1.outputs.artifacts.hello}}")]
                                        )
                                    )]),
                            IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 4
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="return-artifacts",
                                    template="return-template",
                                    arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                            name="artifact3",_from="{{steps.pass-artifact2.outputs.artifacts.hello}}")
                                            ],
                                        parameters=[
                                            IoArgoprojWorkflowV1alpha1Parameter(
                                                name="priorStepsDuration",
                                                value="{{steps.generate-artifact.startedAt}}~{{steps.generate-artifact.finishedAt}};{{steps.pass-artifact1.startedAt}}~{{steps.pass-artifact1.finishedAt}};{{steps.pass-artifact2.startedAt}}~{{steps.pass-artifact2.finishedAt}}")
                                            ]
                                        )
                                    )]), 
                    ]
                ),# <--- TEMPLATE 2 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='template1', 
                    memoize=IoArgoprojWorkflowV1alpha1Memoize(
                        key="{0}".format(parameter1),
                        max_age='10m',
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="{0}".format(parameter1), name="my-config1"))   
                    ),
                    container=Container(
                        image='munachisonwadike/simple-xyz-pipeline', 
                        command=['sh', '-c'], 
                        args=["python step1.py {0} /mnt/vol/; ls /mnt/vol/".format(parameter1)],
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="hello", 
                                path="/mnt/vol/step1.txt".format(parameter1)
                            )
                        ]
                    )
                ),
                # <--- TEMPLATE 3 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='template2',
                    inputs=IoArgoprojWorkflowV1alpha1Inputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="artifact1", 
                                path="/tmp/artifact1"
                            )
                        ]
                    ),
                    memoize=IoArgoprojWorkflowV1alpha1Memoize(
                        key="{0}{1}".format(parameter1,parameter2),
                        max_age='10m',
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="{0}".format(parameter1), name="my-config2"))   
                    ),
                    container=Container(
                        image='munachisonwadike/simple-xyz-pipeline', 
                        command=['sh', '-c'], 
                        # above line was just for debugging to be sure I can see mounted volume
                        args=["python step2.py {0} /mnt/vol/; ls /mnt/vol/".format(parameter2)],
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="hello", 
                                path="/mnt/vol/step2.txt".format(parameter2)
                            )
                        ]
                    )
                ),
                # <--- TEMPLATE 4 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='template3',
                    inputs=IoArgoprojWorkflowV1alpha1Inputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="artifact2", 
                                path="/tmp/artifact2"
                            )
                        ]
                    ),
                    memoize=IoArgoprojWorkflowV1alpha1Memoize(
                        key="{0}{1}{2}".format(parameter1,parameter2,parameter3),
                        max_age='10m',
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="{0}".format(parameter1), name="my-config3"))   
                    ),
                    container=Container(
                        image='munachisonwadike/simple-xyz-pipeline', 
                        command=['sh', '-c'], 
                        args=["python step3.py {0} /mnt/vol/; ls /mnt/vol/".format(parameter3)],
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="hello", 
                                path="/mnt/vol/step3.txt".format(parameter3)
                            )
                        ]
                    )
                ),
                # <--- TEMPLATE 5 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='return-template',
                    inputs=IoArgoprojWorkflowV1alpha1Inputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="artifact3", 
                                path="/mnt/vol/step3.txt"
                            )
                        ],
                        parameters=[
                            IoArgoprojWorkflowV1alpha1Parameter(
                                name="priorStepsDuration")]
                    ), 
                    container=Container(
                        image='munachisonwadike/simple-xyz-pipeline', 
                        command=['sh', '-c'], 
                        # args=["echo 'functionValue:' $(cat /mnt/vol/step3.txt); echo 'Total Duration:' {{inputs.parameters.priorStepsDuration}}; echo 'workflowDuration:' {{workflow.duration}} "], 
                        args=["echo 'funcVal:' $(cat /mnt/vol/step3.txt);"], 
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),   
                ),
            ]
        )
    )
    
    return manifest




def submit_workflow(parameter1, parameter2, parameter3, refresh_window):
    
    
    """
    Part A: 
    Submit workflow Using same producedures following the same pattern as Argo SDK docs
    Note: api_instance.workflow_logs and api_instance.pod_logs are defunct [see: https://github.com/argoproj/argo-workflows/issues/7781#issuecomment-1094078152]
    """
    
    workflow_name = 'sdk-memoize-multistep-{0}-{1}-{2}'.format(parameter1,parameter2,parameter3)
 
    manifest = define_workflow(parameter1, parameter2, parameter3, workflow_name)
    
    configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746", ssl_ca_cert=None) 
    configuration.verify_ssl = False # notice how switch set ssl off here, since there is no parameter for this in the Configuration class https://github.com/argoproj/argo-workflows/blob/master/sdks/python/client/argo_workflows/configuration.py

    api_client = argo_workflows.ApiClient(configuration)
    api_instance = workflow_service_api.WorkflowServiceApi(api_client)
    begin_time =  time.time()
    try:
        api_response = api_instance.create_workflow( 
            namespace='argo',
            body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
            _check_return_type=False)
    except:
        refresh_window = 0 # just check the status of the workflow since its been run before
        print("\t\t[TuunV2-WSS] ~ Submitted Workflow Already Exists! Using Previous Values.") 

    # pprint(api_response) # pretty print yaml/manifest which gets submitted [just for debugging]

    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name


    """
    Part B: Monitor submitted worfklow & report if it's "succeeded" or "failed" 
    """
    workflow_final_state = monitor_workflow(url, refresh_window) 
    pythonDuration  = time.time() - begin_time
    print("\t\t\t\t[TuunV2-WSS] --> Final Workflow State == ", workflow_final_state)
     
 
     
    """
    Part C: Scrape workflow logs via Kunbernetes Python Client  
    Return the obj function value, Cost, etc
    """ 

    # Get pod name corresponding to the last workflow step (the pod whose logs we place the return values within)
    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name
    response = requests.get(url=url, verify=False); response_dict = response.json() 
    # pprint(response_dict) # Used this for testing
    leaf_node_name = response_dict['status']['nodes'][workflow_name]['outboundNodes'] # Among `response_dict['status']['nodes'].keys())`, the key which is exactly the same as workflow_name is our root node workflow tree
    if len(leaf_node_name) > 1:
        raise ValueError("\t\t[TuunV2-WSS] ~ Whoops! Looks like There's more than 1 leaf ")

    wf_time, pod_total, sg_total = caculate_duration(leaf_node_name[0], url, workflow_name) # Used this for testing

    log_name = response_dict['status']['nodes'][leaf_node_name[0]]['outputs']['artifacts'][0]['s3']['key']
    func_val = read_pod_logs_via_k8s(log_name.split('/')[1])
    # print_stepgroups_pods_duration(leaf_node_name[0], url, workflow_name) # Used this for testing
        
    print("\t\t\t\t[TuunV2-WSS] ++> F-val & WSS Times [Total, PodTotal, StepGroupTotal]:", func_val, "& ["+str(wf_time)+", "+str(pod_total)+", "+str(sg_total)+"]")
    return func_val, wf_time, pod_total, sg_total
     
   


if __name__ == '__main__':
    """
    This if statements allows us to run code that won't get run,
    if we import our functions defined within this file, from another python file 
    """
    submit_workflow(5, 4, 9, refresh_window=10)


    # pprint(test_return_workflow('sdk-memoize-multistep-7v4lm'))
    # pprint(test_pod_logs('sdk-memoize-multistep-7v4lm','sdk-memoize-multistep-7v4lm-template3-1491687607'))
    # val  = test_workflow_logs('sdk-memoize-multistep-7v4lm')
    # print(type(val))


 
 