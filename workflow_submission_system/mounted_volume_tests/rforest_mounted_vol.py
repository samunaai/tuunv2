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

from argo_workflows.model.empty_dir_volume_source import EmptyDirVolumeSource
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

def define_workflow(param_dict, workflow_name):

    """
    Define Argo Workflow using Python SDK
    """
    data_in = "language_data/train.csv" 

    manifest = IoArgoprojWorkflowV1alpha1Workflow(
        # metadata=ObjectMeta(generate_name='sdk-memoize-multistep-'),
        metadata=ObjectMeta(name=workflow_name), 
        spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
            entrypoint='entry-template',
            volumes=[Volume(name="workdir", 
                        persistent_volume_claim=PersistentVolumeClaimVolumeSource(
                        claim_name="argo-pv-claim")
                    ), Volume(name="dshm", 
                    empty_dir=EmptyDirVolumeSource(
                    medium="Memory"))
            ], 
            templates=[
                # <--- TEMPLATE 0 --->
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
                                                    name="feature_artifact",_from="{{steps.generate-artifact.outputs.artifacts.feats_outdir}}"),
                                                   ]
                                        )
                                    )]), 
                            IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 3
                                
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="return-artifacts",
                                    template="return-template",
                                    arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                            name="scores_artifact",_from="{{steps.pass-artifact1.outputs.artifacts.postprocess_scores}}")
                                            ], 
                                        )
                                    )]), 
                    ]
                ),
                # <--- TEMPLATE 1 --->
                IoArgoprojWorkflowV1alpha1Template(

                    name='template1', 
                    memoize=IoArgoprojWorkflowV1alpha1Memoize(
                        key="{0}{1}{2}".format(str(param_dict['max_df']).replace('.','x'), param_dict['ngram_range'][0], param_dict['ngram_range'][1]),
                        max_age='1h',
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="{0}{1}{2}".format(str(param_dict['max_df']).replace('.','x'), param_dict['ngram_range'][0], param_dict['ngram_range'][1]), name="my-config1"))   
                    ),
                    container=Container(
                        image='munachisonwadike/random-forest-pipeline', 
                        command=['sh', '-c'], 
                        args=["python main.py action=vectorize data_in=/mnt/vol/{0} feat_outdir=/mnt/vol/{1} max_df={2} ngram_range=[{3},{4}]; ".format(data_in, \
                             param_dict["feat_outdir"], param_dict["max_df"], param_dict["ngram_range"][0], param_dict["ngram_range"][1])],
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="feats_outdir", 
                                path="/mnt/vol/{0}".format(param_dict["feat_outdir"])
                            ), 
                        ]
                    )
                ), 
                # <--- TEMPLATE 2 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='template2',
                    inputs=IoArgoprojWorkflowV1alpha1Inputs(
                        artifacts=[ IoArgoprojWorkflowV1alpha1Artifact(
                                    name="feature_artifact", 
                                    path="/tmp/feature_artifact"
                                    ), 
                        ] 
                    ), 
                    memoize=IoArgoprojWorkflowV1alpha1Memoize(
                        key="{0}{1}{2}x{3}{4}".format(str(param_dict['max_df']).replace('.','x'), param_dict['ngram_range'][0], param_dict['ngram_range'][1], \
                                                param_dict['min_samples_leaf'], param_dict['max_depth'] ),
                        max_age='1h',
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="{0}{1}{2}x{3}{4}".format(  str(param_dict['max_df']).replace('.','x'), param_dict['ngram_range'][0], param_dict['ngram_range'][1], \
                                                param_dict['min_samples_leaf'], param_dict['max_depth'] ), 
                                name="my-config2")
                            )   
                    ),
                    container=Container(
                        image='munachisonwadike/random-forest-pipeline', 
                        command=['sh', '-c'],  
                        args=["df -h | grep shm;  \
                        ls /mnt/vol/{1}; python main.py action=model \
                         data_in=/mnt/vol/{0} feat_outdir=/mnt/vol/{1} min_samples_leaf={2} max_depth={3}; \
                        ls /mnt/vol/".format( data_in, \
                             param_dict["feat_outdir"], param_dict["min_samples_leaf"], param_dict["max_depth"] )], 
                        volume_mounts=[VolumeMount(name="workdir", mount_path="/mnt/vol"), VolumeMount(name="dshm",mount_path="/dev/shm")]
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                name="postprocess_scores", 
                                path="/mnt/vol/{0}/out.txt".format(param_dict['feat_outdir'])
                        )]
                    )
                ),       
                # <--- TEMPLATE 3 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='return-template',
                    inputs=IoArgoprojWorkflowV1alpha1Inputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="scores_artifact", 
                                path="/mnt/vol/{0}/out.txt".format(param_dict['feat_outdir'])
                            )
                        ], 
                    ), 
                    container=Container(
                        image='munachisonwadike/simple-xyz-pipeline', 
                        command=['sh', '-c'], 
                        # args=["echo 'functionValue:' $(cat /mnt/vol/step3.txt); echo 'Total Duration:' {{inputs.parameters.priorStepsDuration}}; echo 'workflowDuration:' {{workflow.duration}} "], 
                        args=["echo 'funcVal:' $(cat /mnt/vol/{0}/out.txt);".format(param_dict['feat_outdir'])], 
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),   
                ),
            ]
        )
    )
    
    return manifest
  


def submit_cv_workflow(param_dict, refresh_window):
    
    
    """
    Part A: 
    Submit workflow Using same producedures following the same pattern as Argo SDK docs
    Note: api_instance.workflow_logs and api_instance.pod_logs are defunct [see: https://github.com/argoproj/argo-workflows/issues/7781#issuecomment-1094078152]
    """

    workflow_name = 'rforest-{0}-{1}{2}-{3}-{4}'.format( str(param_dict["max_df"]), str(param_dict["ngram_range"][0]), str(param_dict["ngram_range"][1]), \
                                        str(param_dict["min_samples_leaf"]), str(param_dict["max_depth"]) )

    manifest = define_workflow(param_dict, workflow_name)
    
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
    except Exception as e:
        refresh_window = 1 # just check the status of the workflow after 1 sec since its been run before
        print("\t\t[TuunV2-WSS] ~ Either Workflow Already Exists (Using Previous Values) or the below error applies.")
        print("\n\n[TuunV2-WSS] **ERROR** ",e, "\n\n") 

    # pprint(api_response) # pretty print yaml/manifest which gets submitted [just for debugging]

    url = 'https://localhost:2746/api/v1/workflows/argo/' + workflow_name


    """
    Part B: Monitor submitted worfklow & report if it's "succeeded" or "failed" 
    """
    workflow_final_state = monitor_workflow(url, refresh_window) 
    pythonDuration  = time.time() - begin_time
    print("\t\t\t\t[TuunV2-WSS] --> Final Workflow State == ", workflow_final_state)
     
 
     
    """
    Part C: Scrape workflow logs via Kubernetes Python Client  
    Return the obj function value, Cost, etc
    """ 

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
    return func_val, wf_time, pod_total, sg_total, pod_runtimes_list
     
   


if __name__ == '__main__':
    """
    This if statements allows us to run code that won't get run,
    if we import our functions defined within this file, from another python file 
    """ 

    param_dict = {"max_df": 0.9, "ngram_range": [1,2],   # preprocessing
    "min_samples_leaf": 2, "max_depth": 2000, "feat_outdir": "output_feats_dir"  # training  
    } 
    
    param_dict["feat_outdir"] += str(param_dict["max_df"])+'_'+str(param_dict["ngram_range"][0])+str(param_dict["ngram_range"][1])+'_'+str(param_dict["min_samples_leaf"])+'_'+str(param_dict["max_depth"])
    
    submit_cv_workflow(param_dict, refresh_window=10)
  

 
 