"""
This was a version of `cloud_seg.py` which I used for testing 
Here the artifacts from each stage are written to disk (i.e /mnt/vol)
Thus never get deleted even when the memoization cache expires.
In `cloud_seg.py`, we instead try to write to /tmp/ instead of mounted volume """

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
    images_dir_in = "datasets/understanding_cloud_organization/train_images"
    image_dir_out = "datasets/understanding_cloud_organization/resized_imgs_masks/" +str(param_dict['resize_h']) +'_'+ str(param_dict['resize_w'])  
    masks_csv_in = "datasets/understanding_cloud_organization/train.csv"
    masks_csv_out = "datasets/understanding_cloud_organization/resized_imgs_masks/" +str(param_dict['resize_h']) +'_'+ str(param_dict['resize_w']) + ".csv"

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
                                                    name="image_artifact",_from="{{steps.generate-artifact.outputs.artifacts.image_dir_out}}"),
                                                   IoArgoprojWorkflowV1alpha1Artifact(
                                                    name="masks_artifact",_from="{{steps.generate-artifact.outputs.artifacts.masks_csv_out}}") ]
                                        )
                                    )]),
                            IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 3
                                
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="pass-artifact2",
                                    template="template3",
                                    arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                            name="artifact2",_from="{{steps.pass-artifact1.outputs.artifacts.model_checkpoint}}")]
                                        )
                                    )]),
                            IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 4
                                
                                value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                    name="return-artifacts",
                                    template="return-template",
                                    arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                            name="artifact3",_from="{{steps.pass-artifact2.outputs.artifacts.postprocess_scores}}")
                                            ], 
                                        )
                                    )]), 
                    ]
                ),
                # <--- TEMPLATE 1 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='template1', 
                    memoize=IoArgoprojWorkflowV1alpha1Memoize(
                        key="{0}{1}".format(param_dict['resize_h'],param_dict['resize_w']),
                        max_age='10h',
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="{0}{1}".format(param_dict['resize_h'],param_dict['resize_w']), name="my-config1"))   
                    ),
                    container=Container(
                        image='munachisonwadike/cloud-segmentation-pipeline', 
                        command=['sh', '-c'], 
                        args=["python main.py action=preprocess images_dir_in=/mnt/vol/{0} masks_csv_in=/mnt/vol/{1} image_dir_out=/mnt/vol/{2} masks_csv_out=/mnt/vol/{3}; \
                         ls /mnt/vol/datasets/understanding_cloud_organization/resized_imgs_masks/".format(images_dir_in, masks_csv_in, image_dir_out, masks_csv_out)],
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="image_dir_out", 
                                path="/mnt/vol/{0}".format(image_dir_out)
                            ),
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="masks_csv_out", 
                                path="/mnt/vol/{0}".format(masks_csv_out)
                            )
                        ]
                    )
                ), 
                # <--- TEMPLATE 2 --->
                IoArgoprojWorkflowV1alpha1Template(
                    name='template2',
                    inputs=IoArgoprojWorkflowV1alpha1Inputs(
                        artifacts=[ IoArgoprojWorkflowV1alpha1Artifact(
                                    name="image_artifact", 
                                    path="/tmp/image_artifact"
                                    ),
                                    IoArgoprojWorkflowV1alpha1Artifact(
                                        name="masks_artifact", 
                                        path="/tmp/masks_artifact"
                                    )
                        ] 
                    ), 
                    memoize=IoArgoprojWorkflowV1alpha1Memoize(
                        key="{0}{1}x{2}{3}{4}{5}{6}{7}{8}{9}".format( param_dict['resize_h'], param_dict['resize_w'], 
                            str(param_dict["batch_size"]), str(param_dict["epochs"]), \
                         param_dict["optimizer"], param_dict["arch"], param_dict["encoder"], str(param_dict["lr_encoder"]).replace('.','x'), \
                          str(param_dict["lr_decoder"]).replace('.','x'), str(param_dict["num_workers"]) ),
                        max_age='5m',
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="{0}{1}x{2}{3}{4}{5}{6}{7}{8}{9}".format(param_dict['resize_h'], param_dict['resize_w'], 
                                str(param_dict["batch_size"]), str(param_dict["epochs"]), \
                                param_dict["optimizer"], param_dict["arch"], param_dict["encoder"], str(param_dict["lr_encoder"]).replace('.','x'), \
                                str(param_dict["lr_decoder"]).replace('.','x'), str(param_dict["num_workers"])), 
                                name="my-config2")
                            )   
                    ),
                    container=Container(
                        image='munachisonwadike/cloud-segmentation-pipeline', 
                        command=['sh', '-c'],  
                        args=["df -h | grep shm; ls /mnt/vol/{0} | wc -l; nvidia-smi; \
                        ls /mnt/vol/{1}; python main.py action=train \
                         image_dir_out=/mnt/vol/{0} masks_csv_out=/mnt/vol/{1} batch_size={2} \
                         checkpoint_dir=/mnt/vol/{3} epochs={4} optimizer={5}  encoder={6} \
                         lr_encoder={7} lr_decoder={8} num_workers={9} random_seed={10}; \
                        ls /mnt/vol/".format( image_dir_out, masks_csv_out, param_dict['batch_size'], param_dict['checkpoint_dir'], param_dict['epochs'], param_dict['optimizer'], param_dict['encoder'], param_dict['lr_encoder'], param_dict['lr_decoder'], param_dict['num_workers'], param_dict['random_seed'] )], 
                        volume_mounts=[VolumeMount(name="workdir", mount_path="/mnt/vol"),VolumeMount(name="dshm",mount_path="/dev/shm")]
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                name="model_checkpoint", 
                                path="/mnt/vol/{0}/best.pth".format(param_dict['checkpoint_dir'])
                        )]
                    )
                ),               
                # <--- TEMPLATE 3 --->
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
                        key="{0}{1}x{2}{3}{4}{5}{6}{7}{8}{9}x{10}{11}".format( param_dict['resize_h'], param_dict['resize_w'], 
                            str(param_dict["batch_size"]), str(param_dict["epochs"]), \
                            param_dict["optimizer"], param_dict["arch"], param_dict["encoder"], str(param_dict["lr_encoder"]).replace('.','x'), \
                            str(param_dict["lr_decoder"]).replace('.','x'), str(param_dict["num_workers"]), str(param_dict["threshold"]).replace('.','x'), str(param_dict["min_mask_size"]) ),
                        max_age='5m',
                        cache=IoArgoprojWorkflowV1alpha1Cache(
                            config_map=ConfigMapKeySelector(key="{0}{1}x{2}{3}{4}{5}{6}{7}{8}{9}x{10}{11}".format( param_dict['resize_h'], param_dict['resize_w'], 
                            str(param_dict["batch_size"]), str(param_dict["epochs"]), \
                            param_dict["optimizer"], param_dict["arch"], param_dict["encoder"], str(param_dict["lr_encoder"]).replace('.','x'), \
                            str(param_dict["lr_decoder"]).replace('.','x'), str(param_dict["num_workers"]), str(param_dict["threshold"]).replace('.','x'), str(param_dict["min_mask_size"]) ), name="my-config3"))   
                    ),
                    container=Container(
                        image='munachisonwadike/cloud-segmentation-pipeline', 
                        command=['sh', '-c'], 
                        args=["python main.py action=postprocess \
                         image_dir_out=/mnt/vol/{0} masks_csv_out=/mnt/vol/{1} batch_size={2} \
                         checkpoint_dir=/mnt/vol/{3} encoder={4} \
                         num_workers={5} threshold={6} min_mask_size={7} random_seed={8} out_dir_dice=/mnt/vol ; \
                        ls /mnt/vol/".format( image_dir_out, masks_csv_out, param_dict['batch_size'], param_dict['checkpoint_dir'], param_dict['encoder'], param_dict['num_workers'], param_dict['threshold'], param_dict['min_mask_size'], param_dict['random_seed'])], 
                        volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol"),VolumeMount(name="dshm",mount_path="/dev/shm")]
                    ),  
                    outputs=IoArgoprojWorkflowV1alpha1Outputs(
                        artifacts=[ 
                            IoArgoprojWorkflowV1alpha1Artifact(
                                name="postprocess_scores", 
                                path="/mnt/vol/out.txt" 
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
                                name="artifact3", 
                                path="/mnt/vol/out.txt"
                            )
                        ], 
                    ), 
                    container=Container(
                        image='munachisonwadike/simple-xyz-pipeline', 
                        command=['sh', '-c'], 
                        # args=["echo 'functionValue:' $(cat /mnt/vol/step3.txt); echo 'Total Duration:' {{inputs.parameters.priorStepsDuration}}; echo 'workflowDuration:' {{workflow.duration}} "], 
                        args=["echo 'funcVal:' $(cat /mnt/vol/out.txt);"], 
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

    workflow_name = 'cldsg-{0}{1}-{2}{3}{4}{5}{6}{7}{8}{9}-{10}{11}'.format(param_dict['resize_h'],param_dict['resize_w'], \
                                str(param_dict["batch_size"]), param_dict["optimizer"].lower(),  \
                                str(param_dict["epochs"]), param_dict["arch"].lower(), param_dict["encoder"].lower(), str(param_dict["lr_encoder"]), \
                                str(param_dict["lr_decoder"]), str(param_dict["num_workers"]), str(param_dict["threshold"]), str(param_dict["min_mask_size"]))

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
    
    

    param_dict = {"action": "preprocess", "random_seed": 0,
    "resize_h": 352, "resize_w": 576, "device": "gpu",   #w resize must be divisible by 32
    "batch_size": 16,  "checkpoint_dir":"checkpoints/", "epochs": 1, "optimizer": "Adam", "arch": "Unet", "encoder": "resnet18", "lr_encoder": 1e-3, "lr_decoder": 1e-2, "num_workers":4, # training
    "threshold": 0.3, "min_mask_size": 10000 # postprocess # "threshold": 0.4, "min_mask_size": 10000  
    } 
    
    param_dict["checkpoint_dir"] += str(param_dict["batch_size"])+'_'+str(param_dict["epochs"])+'_'+param_dict["optimizer"]+'_'+param_dict["arch"]+'_'+param_dict["encoder"]+'_'+str(param_dict["lr_encoder"])+'_'+str(param_dict["lr_decoder"])+'_'+str(param_dict["num_workers"])
    
    # print("****!!==>", param_dict["checkpoint_dir"]) 
    submit_cv_workflow(param_dict, refresh_window=10)
 

    # pprint(test_return_workflow('sdk-memoize-multistep-7v4lm'))
    # pprint(test_pod_logs('sdk-memoize-multistep-7v4lm','sdk-memoize-multistep-7v4lm-template3-1491687607'))
    # val  = test_workflow_logs('sdk-memoize-multistep-7v4lm')
    # print(type(val))


 
 
