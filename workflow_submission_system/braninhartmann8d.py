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

def define_workflow(x1, x2, x3, x4, x5, x6, x7, x8, workflow_name, cache_time):

    """
    Define Argo Workflow using Python SDK
    """
    manifest = IoArgoprojWorkflowV1alpha1Workflow(
        # metadata=ObjectMeta(generate_name='sdk-memoize-multistep-'),
        metadata=ObjectMeta(name=workflow_name), 
        spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
            entrypoint='entry-template',
            templates=[
                # <--- TEMPLATE 1 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='entry-template',
                    steps=[ IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 1
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="branin-part1",
                                    template="template1")]),
                            IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 2
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="branin-part2",
                                    template="template2",
                                    arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                            name="artifact1",_from="{{steps.branin-part1.outputs.artifacts.output1}}")]
                                        )
                                    )]), 
                            IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 3
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="return-artifacts",
                                    template="return-template",
                                    arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                            name="artifact2",_from="{{steps.branin-part2.outputs.artifacts.output2}}")
                                            ], 
                                        )
                                    )]), 
                    ]
                ),# <--- TEMPLATE 2 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='template1', 
                    memoize=IoArgoprojWorkflowV1alpha1Memoize(
                        key="brh8d{0}{1}".format( str(x1).replace('.','x'), str(x2).replace('.','x') ),
                        max_age=cache_time,
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="brh8d{0}{1}".format( str(x1).replace('.','x'), str(x2).replace('.','x') ), name="my-config1"))   
                    ),
                    container=Container(
                        image='munachisonwadike/branin-hartmann8d-pipeline', 
                        command=['sh', '-c'], 
                        args=["python step1.py {0} {1} /tmp/; ls /tmp/".format(x1, x2)],
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="output1", 
                                path="/tmp/step1.txt" 
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
                        key="brh8d{0}{1}{2}{3}{4}{5}".format( str(x3).replace('.','x'), str(x4).replace('.','x'),
                            str(x5).replace('.','x'), str(x6).replace('.','x'), str(x7).replace('.','x'), str(x8).replace('.','x') ),
                        max_age=cache_time,
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="brh8d{0}{1}{2}{3}{4}{5}".format( str(x3).replace('.','x'), str(x4).replace('.','x'),
                            str(x5).replace('.','x'), str(x6).replace('.','x'), str(x7).replace('.','x'), str(x8).replace('.','x') ), name="my-config2"))   
                    ),
                    container=Container(
                        image='munachisonwadike/branin-hartmann8d-pipeline', 
                        command=['sh', '-c'], 
                        # above line was just for debugging to be sure I can see mounted volume
                        args=["python step2.py {0} {1} /tmp/; ls /tmp/".format(x3, x4)],
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="output2", 
                                path="/tmp/step2.txt" 
                            )
                        ]
                    )
                ),
                # <--- TEMPLATE 4 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='return-template',
                    inputs=IoArgoprojWorkflowV1alpha1Inputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="artifact2", 
                                path="/tmp/step2.txt"
                            )
                        ], 
                    ), 
                    container=Container(
                        image='munachisonwadike/branin-hartmann8d-pipeline', 
                        command=['sh', '-c'], 
                        # args=["echo 'functionValue:' $(cat /tmp/step3.txt); echo 'Total Duration:' {{inputs.parameters.priorStepsDuration}}; echo 'workflowDuration:' {{workflow.duration}} "], 
                        args=["echo 'funcVal:' $(cat /tmp/step2.txt);"], 
                    ),   
                ),
            ]
        )
    )
    
    return manifest


def brh8d_cost(x1, x2, x3, x4):
    return

def submit_brh8d_workflow(params, refresh_window, cost_type=True, cache_time=''):
    
    
    """ 
    Submit workflow Using same producedures following the same pattern as Argo SDK docs
    Note: api_instance.workflow_logs and api_instance.pod_logs are defunct [see: https://github.com/argoproj/argo-workflows/issues/7781#issuecomment-1094078152]

    Then Monitor submitted worfklow & report if it's "succeeded" or "failed" 

    Lastly, if it's succeeded, scrape the logs to get the pod information
    """
    
    

    # 1. First Define Workflow Name based on input parameters
    x1, x2, x3, x4, x5, x6, x7, x8 = params
    workflow_name = 'branin-hartmamm-8d-{0}-{1}-{2}-{3}-{4}-{5}-{6}-{7}'.format(x1, x2, x3, x4, x5, x6, x7, x8)
    
    # 2. Then Create the Manifest
    manifest = define_workflow(x1, x2, x3, x4, x5, x6, x7, x8, workflow_name, cache_time)
    
    # 3. Configure API instance and submit the Manifest there via HTTP request    
    configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746", ssl_ca_cert=None) 
    configuration.verify_ssl = False # notice how switch set ssl off here, since there is no parameter for this in the Configuration class https://github.com/argoproj/argo-workflows/blob/master/sdks/python/client/argo_workflows/configuration.py
    api_client = argo_workflows.ApiClient(configuration)
    api_instance = workflow_service_api.WorkflowServiceApi(api_client)
    begin_time =  time.time()
    api_response = api_instance.create_workflow( 
        namespace='argo',
        body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
        _check_return_type=False) 
    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name


    # 4. Monitor submitted worfklow & report if it's "succeeded" or "failed" 
    workflow_final_state = monitor_workflow(url, refresh_window) 
    pythonDuration  = time.time() - begin_time
    print("\t\t\t\t[TuunV2-WSS] --> Final Workflow State == ", workflow_final_state)
     
 
     
    # 5. Scrape workflow logs via Kubernetes Python Client  Return the obj function value, Cost, etc
    # Get pod name corresponding to the last workflow step (the pod whose logs we place the return values within)
    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name
    response = requests.get(url=url, verify=False); response_dict = response.json() 
    # pprint(response_dict) # Used this for testing
    leaf_node_name = response_dict['status']['nodes'][workflow_name]['outboundNodes'] # Among `response_dict['status']['nodes'].keys())`, the key which is exactly the same as workflow_name is our root node workflow tree
    if len(leaf_node_name) > 1:
        raise ValueError("\t\t[TuunV2-WSS] ~ Whoops! Looks like There's more than 1 leaf ")
    wf_time, pod_total, sg_total, pod_runtimes_list = calculate_duration(leaf_node_name[0], url, workflow_name) # Used this for testing
    log_name = response_dict['status']['nodes'][leaf_node_name[0]]['outputs']['artifacts'][0]['s3']['key']
    func_val = read_pod_logs_via_k8s(log_name.split('/')[1])
    # print_stepgroups_pods_duration(leaf_node_name[0], url, workflow_name) # Used this for testing
    print("\t\t\t\t[TuunV2-WSS] ++> F-val:", str(func_val)+"; Total WF Time:", str(wf_time)+"s; Pod total time:", str(pod_total)+"s; Pod-wise times (seconds):", str(pod_runtimes_list) )
    
    if cost_type==True:
        return func_val, wf_time, pod_total, sg_total, pod_runtimes_list
    else:
        return func_val 
   


if __name__ == '__main__':
    """
    This if statements allows us to run code that won't get run,
    if we import our functions defined within this file, from another python file 
    """
    submit_brh8d_workflow([1, 1, 2, 0.5, 1.5, 1, 0.2, 0.2], refresh_window=5, cost_type=True, cache_time='5m')


    # pprint(test_return_workflow('sdk-memoize-multistep-7v4lm'))
    # pprint(test_pod_logs('sdk-memoize-multistep-7v4lm','sdk-memoize-multistep-7v4lm-template3-1491687607'))
    # val  = test_workflow_logs('sdk-memoize-multistep-7v4lm')
    # print(type(val))


 
 