from pprint import pprint

import argo_workflows
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

parameter1 = 7
parameter2 = 6
parameter3 = 2

configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746", ssl_ca_cert=None) 
configuration.verify_ssl = False # notice how switch set ssl off here, since there is no parameter for this in the Configuration class https://github.com/argoproj/argo-workflows/blob/master/sdks/python/client/argo_workflows/configuration.py

manifest = IoArgoprojWorkflowV1alpha1Workflow(
    metadata=ObjectMeta(generate_name='sdk-memoize-multistep-'),
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
                                template="whalesay1")]),
                        IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 2
                            value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                name="pass-artifact1",
                                template="whalesay2",
                                arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                    artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                        # name="artifact1",_from="{0}".format(parameter2))]
                                        name="artifact1",_from="{{steps.generate-artifact.outputs.artifacts.hello}}")]
                                    )
                                )]),
                        IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 3
                            value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                name="pass-artifact2",
                                template="whalesay3",
                                arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                    artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                        name="artifact2",_from="{{steps.pass-artifact1.outputs.artifacts.hello}}")]
                                    )
                                )]),
                        IoArgoprojWorkflowV1alpha1ParallelSteps( # STEP 4
                            value=[IoArgoprojWorkflowV1alpha1WorkflowStep(
                                name="print-artifacts",
                                template="print-whalesay",
                                arguments=IoArgoprojWorkflowV1alpha1Arguments(
                                    artifacts=[IoArgoprojWorkflowV1alpha1Artifact(
                                        name="artifact3",_from="{{steps.pass-artifact2.outputs.artifacts.hello}}")]
                                    )
                                )]), 
                ]
            ),# <--- TEMPLATE 2 --->
            IoArgoprojWorkflowV1alpha1Template(
                name='whalesay1', 
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
                name='whalesay2',
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
                name='whalesay3',
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
                name='print-whalesay',
                inputs=IoArgoprojWorkflowV1alpha1Inputs(
                    artifacts=[ 
                        IoArgoprojWorkflowV1alpha1Artifact(
                            name="artifact3", 
                            path="/mnt/vol/step3.txt"
                        )
                    ]
                ), 
                container=Container(
                    image='munachisonwadike/simple-xyz-pipeline', 
                    command=['sh', '-c'], 
                    args=["echo '======>>>>'; cat /mnt/vol/step3.txt"], # TO DO - ADD TO DOCKERFILE TO ALLOW ME TO WHALESAY THE OPTIMAL PARAMETER?
                    volume_mounts=[VolumeMount(name="workdir",mount_path="/mnt/vol")]
                ),   
            ),
        ]
    )
)

api_client = argo_workflows.ApiClient(configuration)
api_instance = workflow_service_api.WorkflowServiceApi(api_client)

if __name__ == '__main__':
    api_response = api_instance.create_workflow(
        namespace='argo',
        body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
        _check_return_type=False)
    pprint(api_response)


 