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

from kubernetes import client, config
from pprint import pprint

import argo_workflows
import json
import requests # https://requests.readthedocs.io/en/latest/user/quickstart/#binary-response-content
import time


def read_pod_logs_via_argo():

    """
    DEPRECATED!
    ---
    Decided not to use this appraoch of reading logs via argo 
    Using K8S instead. Just kept this code in case I need later
    Also, the code here is incomplete, just reads logs without parsing! 
    """

    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name
    log_url = 'https://localhost:2746/api/v1/workflows/argo/sdk-memoize-multistep-3-6-2/'
    log_url += 'sdk-memoize-multistep-3-6-2-return-template-1755894561/log?logOptions.container=main'
    response = requests.get(url = log_url, verify=False)
    r = response.text # can't use response.json(): response for logs is not a valid JSON format
    for line in r.splitlines(): # instead parse the text files line-by-line
        print("LINE # I", line) 

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
                                                value="{{steps.generate-artifact.startedAt}}")
                                                # {{steps.generate-artifact.finishedAt}}
                                                # {{steps.pass-artifact1.startedAt}}
                                                # {{steps.pass-artifact1.finishedAt}}
                                                # {{steps.pass-artifact2.startedAt}}
                                                # {{steps.pass-artifact2.finishedAt}}
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
                        key="{0}{1}{2} w s".format(parameter1,parameter2,parameter3),
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
                        args=["echo 'Function Value:' $(cat /mnt/vol/step3.txt); echo 'Total Duration:' {{inputs.parameters.priorStepsDuration}}; echo 'Total Duration:' {{workflow.duration}} "], 
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),   
                ),
            ]
        )
    )
    
    return manifest

def monitor_workflow(url, refresh_window):

    """
    Monitor workflow Status 
    --
    1 second lag is needed for Argo API to start to show the status of running/succeeded/failed
    Hence the use of time.sleep
    We use 'workflows.argoproj.io/phase' (under ['metadata']['labels']) instead of 'workflows.argoproj.io/completed' since the latter is only created at the end of WF lifecycle
    """    

    i=1;  
    while True:
        print("[TuunV2] API GET --> Waiting {0} secs pre-workflow completion check #{1}".format(refresh_window,i))
        time.sleep(refresh_window) # wait a predefined number of seconds to check workflow progress
        response = requests.get(url=url, verify=False)
        response_dict = response.json() 
        print("[TuunV2] TimeWindow{0} --> Status ==".format(i), response_dict['metadata']['labels']['workflows.argoproj.io/phase'] ) 
        if response_dict['metadata']['labels']['workflows.argoproj.io/phase'] != "Running":
            print("[TuunV2] --> Workflow has finished Running")
            break  
        i+=1  

    return response_dict['metadata']['labels']['workflows.argoproj.io/phase']

def read_pod_logs_via_k8s():

    """
    Reads and Parses Pod logs using kubernetes python client
    Note: This requires parsing the correct certificates, otherwise k8s server will deny access
    """

    # Pass the correct configurations for python to access kubernetes server
    config.load_kube_config() 
    configuration = client.Configuration()
    # microk8s certificates usually stored in /var/snap/microk8s/current/certs/
    # for full k8s, certificatates may be stored in /etc/kubernetes/pki/
    configuration.ssl_ca_cert = '/var/snap/microk8s/current/certs/ca.crt'
    configuration.cert_file = '/var/snap/microk8s/current/certs/server.crt'
    configuration.key_file = '/var/snap/microk8s/current/certs/server.key'
    # host location/port - usually listed under cluster server in kubeconfig 
    configuration.host = 'https://127.0.0.1:16443' 
    configuration.verify_ssl = False
    client.Configuration.set_default(configuration)

    v1 = client.CoreV1Api()
    print("Listing pods with their IPs:")
    # ret = v1.list_pod_for_all_namespaces(watch=False)
    ret = v1.list_namespaced_pod(namespace='argo', watch=False)
    for pod in ret.items:
        print("%s\t%s\t%s" % (pod.status.pod_ip, pod.metadata.namespace, pod.metadata.name))
        # break

    log_output = v1.read_namespaced_pod_log(name='sdk-memoize-multistep-7-6-2-return-template-2133450781',
                                        namespace='argo', container="main")


    return log_output

def submit_workflow(parameter1, parameter2, parameter3, refresh_window):
    
     
    """
    Part A: 
    Submit workflow Using same producedures following the same pattern as Argo SDK docs
    Note: api_instance.workflow_logs and api_instance.pod_logs are defunct [see: https://github.com/argoproj/argo-workflows/issues/7781#issuecomment-1094078152]
    """
    
    workflow_name = 'sdk-memoize-multistep-{0}-{1}-{2}'.format(parameter1,parameter2,parameter3)
    '''
    manifest = define_workflow(parameter1, parameter2, parameter3, workflow_name)
    
    configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746", ssl_ca_cert=None) 
    configuration.verify_ssl = False # notice how switch set ssl off here, since there is no parameter for this in the Configuration class https://github.com/argoproj/argo-workflows/blob/master/sdks/python/client/argo_workflows/configuration.py

    api_client = argo_workflows.ApiClient(configuration)
    api_instance = workflow_service_api.WorkflowServiceApi(api_client)
    api_response = api_instance.create_workflow( 
        namespace='argo',
        body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
        _check_return_type=False)

    # pprint(api_response) # pretty print yaml/manifest which gets submitted [just for debugging]

    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name


    """
    Part B: Monitor submitted worfklow & report if it's "succeeded" or "failed" 
    """
    workflow_final_state = monitor_workflow(url, refresh_window) 
    print("[TuunV2] --> Final Workflow State == ", workflow_final_state)
     
    '''
    
    """
    Part C: Scrape workflow logs via Kunbernetes Python Client  
    Return the obj function value, Cost, etc
    """ 

    # First, we need to get the correct pod name
    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name
    response = requests.get(url=url, verify=False)
    response_dict = response.json() 
    # pprint(response_dict)
    for step in response_dict['status']['nodes']:
        print(response_dict['status']['nodes'][step])
        break
        # if response_dict['status']['nodes'] == 'Pod':
        #     response_dict['status']['nodes'].keys()
    pod_name = response_dict['status']['nodes'].keys()
    # print(pod_name)
    
    print(read_pod_logs_via_k8s())
  
    return_value = None
        
    return return_value
     
  




if __name__ == '__main__':
    """
    This if statements allows us to run code that won't get run,
    if we import our functions defined within this file, from another python file 
    """
    submit_workflow(10, 6, 6, refresh_window=10)


    # pprint(test_return_workflow('sdk-memoize-multistep-7v4lm'))
    # pprint(test_pod_logs('sdk-memoize-multistep-7v4lm','sdk-memoize-multistep-7v4lm-template3-1491687607'))
    # val  = test_workflow_logs('sdk-memoize-multistep-7v4lm')
    # print(type(val))


 
 