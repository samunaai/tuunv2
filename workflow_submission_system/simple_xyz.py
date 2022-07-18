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

def define_workflow(parameter1, parameter2, parameter3, workflow_name):

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
                        args=["echo 'Function Value:' $(cat /mnt/vol/step3.txt); echo 'Total Duration:' {{inputs.parameters.priorStepsDuration}}; echo 'Total Duration:' {{workflow.duration}} "], 
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),   
                ),
            ]
        )
    )
    
    return manifest
     

def submit_workflow(parameter1, parameter2, parameter3, refresh_window):
    
    """
    This part is standard procedure for submitting argo workflow via SDK 
    See docs at https://github.com/argoproj/argo-workflows/tree/627597b5616f4d22e88b89a6d7017a67b6a4143d/sdks/python
    --
    use the usual api_instance.create_workflow method to submit workflow
    We directly query the url based api for workflow status and logs
    Alternative could be to use api_instance.get_workflow to check on workflow status - would need a 'sleep' period in-between
    get_workflow function is defined here:  https://github.com/argoproj/argo-workflows/blob/627597b5616f4d22e88b89a6d7017a67b6a4143d/sdks/python/client/argo_workflows/api/workflow_service_api.py
    """

    """
    Part A: Submit workflow
    -- 
    Simply producedure following the same pattern as Argo SDK docs
    """
    '''
    workflow_name = 'sdk-memoize-multistep-{0}-{1}-{2}'.format(parameter1,parameter2,parameter3)
    
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

    """Part B: Monitor workflow Status 
    --
    1 second lag is needed for Argo API to start to show the status of running/succeeded/failed
    Hence the use of time.sleep
    We use 'workflows.argoproj.io/phase' (under ['metadata']['labels']) instead of 'workflows.argoproj.io/completed' since the latter is only created at the end of WF lifecycle
    """    
    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name
    i=1;  
    while True:
        print("[TuunV2] API GET --> Waiting {0} secs pre-workflow completion check #{1}".format(refresh_window,i))
        time.sleep(refresh_window) # wait a predefined number of seconds to check workflow progress

        print("[TuunV2] API GET --> Waiting 1 sec before first workflow completion check")
        response = requests.get(url=url, verify=False)
        response_dict = response.json() 
        print("[TuunV2] TimeWindow{0} --> Status==".format(i), response_dict['metadata']['labels']['workflows.argoproj.io/phase'] ) 
        if response_dict['metadata']['labels']['workflows.argoproj.io/phase'] == "Succeeded":
            print("[TuunV2] --> Workflow has finished Running")
            break  
        i+=1  
    
    
    """
    Part C [Approach A]: Scrape workflow logs via Argo workflows wepAPI 
    Return the obj function value, Cost, and other necessary parameters
    """ 
    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name
    log_url = 'https://localhost:2746/api/v1/workflows/argo/sdk-memoize-multistep-3-6-2/'
    log_url += 'sdk-memoize-multistep-3-6-2-return-template-1755894561/log?logOptions.container=main'
    response = requests.get(url = log_url, verify=False)
    r = response.text # can't use response.json(): response for logs is not a valid JSON format
    for line in r.splitlines(): # instead parse the text files line-by-line
        print("LINE # I", line)
    # print("[TuunV2] Last Pod Log -->", type(response.text), response.text)
    # print("[TuunV2] Last Pod Log -->", type(r))
    # print("[TuunV2] Debug -->", response.json().keys())
    return_value = None
        
    return return_value 
    '''
    """
    Part C [Approach B]: Scrape workflow logs via Kunbernetes Python Client  
    Return same contents as Approach A above
    """ 
        
    # Configs can be set in Configuration class directly or using helper utility
    config.load_kube_config() 

    configuration = client.Configuration()
    # the below passes the API Key
    configuration.ssl_ca_cert = '/var/snap/microk8s/current/certs/ca.crt'
    configuration.cert_file = '/var/snap/microk8s/current/certs/server.crt'
    configuration.key_file = '/var/snap/microk8s/current/certs/server.key'
    # configuration.api_key['authorization'] = 'LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUREekNDQWZlZ0F3SUJBZ0lVZGhVS044UllPbUdEUStla3pEUmdMVUFsSGZZd0RRWUpLb1pJaHZjTkFRRUwKQlFBd0Z6RVZNQk1HQTFVRUF3d01NVEF1TVRVeUxqRTRNeTR4TUI0WERUSXlNRFV3TmpFNU1UTTFObG9YRFRNeQpNRFV3TXpFNU1UTTFObG93RnpFVk1CTUdBMVVFQXd3TU1UQXVNVFV5TGpFNE15NHhNSUlCSWpBTkJna3Foa2lHCjl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUExaDVMaFgvMHpoa0hDczB1UFZZQnAzcjNNK0ZyRGtQQ1lkdFIKdXc4V1AzS0oyZmsyRkl1a20zK0lGT2o2RURET01XaWZrWTNyTy8rOW1jek81VHE1UCtjcmxmRys1Yk9WR2VIRApTbUQvc1lqTkpxdk9QWUFsaEUzUWpxa2ZzNlg4ejhpQjd1bkUxSUM5ZS9veEM4R0xZYm1kQllhSU5mR0FEVE1SCjgycjM2Qk1wMmRlek05VGUrdmdhUTZZdU5EQ0hUZ2JrYVE0QmdiQWRSUzRVaUg5OS9hT1hRZmwwVThzanJSSmoKd2JqTDdOQXJxQ0F4SUtEdFhxM0ZzdERSN3cydC9xSnBLTEtoSkZ2YXd6MVI5WXA4eFRJVzJVUk1RTXBITmtZTgplem4zV3IvTE0zRGdZYndrd3VZQklSb25CNE8vRi80dHhyYTQyelhFV1Z2QldWNGVCd0lEQVFBQm8xTXdVVEFkCkJnTlZIUTRFRmdRVXEzK24ySmdDaGRUMkVkN3I3SmkxNDR4bXZsMHdId1lEVlIwakJCZ3dGb0FVcTMrbjJKZ0MKaGRUMkVkN3I3SmkxNDR4bXZsMHdEd1lEVlIwVEFRSC9CQVV3QXdFQi96QU5CZ2txaGtpRzl3MEJBUXNGQUFPQwpBUUVBUlNlVW43b3lMTys0OU1BZHdEdkhwL3FsZjBrKzZVaFNyQ0tpTkhFakJxaG9reDFuSW1pTUdoQStmWG9IClZLZm1KRkxwS0oyazl2OWFGVldlbFdSNkFvMWV4c0VZa1kxNlJDMGIveFB4aVU1cE94UkNFMllSSncvcWh5cXoKTmtNek1kaSsydElxY29oY2NOdkZhQVVBbmE5akVZckErakhaRUhsdEhUQTJxblNpRGt5K2wyZXVla08xT2FwNwpqZzRWdUo0Zklrckdob0c2RE1rSVlUQnUrZHNaRzlOdkJaU3FWY3IyZWVDa281WGU4TDU5bWVra1lwVkdBZmdtCjdmL1ZCdTc4eUphYTI3K1ZabGpJUWxZSWhpQWRzZ2d0T1RFdFBPR2RyUDdPNE8zejhDWFNQLzVzMVlVQ1RqYzMKa0tFK0VIbWVXRk5idmF5dzFrWGFQYnF5REE9PQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==' 
    # the below tells us where to check for kube system server
    configuration.host = 'https://127.0.0.1:16443'
    configuration.verify_ssl = False
    client.Configuration.set_default(configuration)

    v1 = client.CoreV1Api()
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for pod in ret.items:
        print("%s\t%s\t%s" % (pod.status.pod_ip, pod.metadata.namespace, pod.metadata.name))
        # break

    log_output = v1.read_namespaced_pod_log(name='sdk-memoize-multistep-7-6-2-return-template-2133450781',
                                        namespace='argo', container="main")

    print(log_output)
    return
     
  


if __name__ == '__main__':
    """
    This if statements allows us to run code that won't get run,
    if we import our functions defined within this file, from another python file 
    """
    submit_workflow(7, 6, 2, refresh_window=10)


    # pprint(test_return_workflow('sdk-memoize-multistep-7v4lm'))
    # pprint(test_pod_logs('sdk-memoize-multistep-7v4lm','sdk-memoize-multistep-7v4lm-template3-1491687607'))
    # val  = test_workflow_logs('sdk-memoize-multistep-7v4lm')
    # print(type(val))


 
# def test_pod_logs(workflow_name, pod_name):
#     configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746", ssl_ca_cert=None) 
#     configuration.verify_ssl = False # notice how switch set ssl off here, since there is no parameter for this in the Configuration class https://github.com/argoproj/argo-workflows/blob/master/sdks/python/client/argo_workflows/configuration.py

#     api_client = argo_workflows.ApiClient(configuration)
#     api_instance = workflow_service_api.WorkflowServiceApi(api_client)

#     return_val_log = api_instance.pod_logs(
#         namespace='argo',
#         name=workflow_name,
#         pod_name=pod_name)

#     return return_val_log

# def test_workflow_logs(workflow_name):
#     configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746", ssl_ca_cert=None) 
#     configuration.verify_ssl = False # notice how switch set ssl off here, since there is no parameter for this in the Configuration class https://github.com/argoproj/argo-workflows/blob/master/sdks/python/client/argo_workflows/configuration.py

#     api_client = argo_workflows.ApiClient(configuration)
#     api_instance = workflow_service_api.WorkflowServiceApi(api_client)

#     return_val_log = api_instance.workflow_logs(
#         namespace='argo',
#         name=workflow_name, _check_return_type=False)

#     return return_val_log