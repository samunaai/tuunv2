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
from argo_workflows.model.io_argoproj_workflow_v1alpha1_arguments import IoArgoprojWorkflowV1alpha1Arguments
from argo_workflows.model.io_argoproj_workflow_v1alpha1_parameter import IoArgoprojWorkflowV1alpha1Parameter
from argo_workflows.model.io_argoproj_workflow_v1alpha1_memoize import IoArgoprojWorkflowV1alpha1Memoize
from argo_workflows.model.io_argoproj_workflow_v1alpha1_cache import IoArgoprojWorkflowV1alpha1Cache
from argo_workflows.model.config_map_key_selector import ConfigMapKeySelector
from argo_workflows.model.io_argoproj_workflow_v1alpha1_outputs import IoArgoprojWorkflowV1alpha1Outputs
from argo_workflows.model.io_argoproj_workflow_v1alpha1_value_from import IoArgoprojWorkflowV1alpha1ValueFrom



parameter1 = "munachiso"
parameter2 = "DrQirong"

configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746", ssl_ca_cert=None) 
configuration.verify_ssl = False # notice how switch set ssl off here, since there is no parameter for this in the Configuration class https://github.com/argoproj/argo-workflows/blob/master/sdks/python/client/argo_workflows/configuration.py

manifest = IoArgoprojWorkflowV1alpha1Workflow(
    metadata=ObjectMeta(generate_name='memoized-simple-workflow-'),
    spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
        entrypoint='whalesay',
        arguments=IoArgoprojWorkflowV1alpha1Arguments(
            parameters=[
                IoArgoprojWorkflowV1alpha1Parameter(
                name="message", value="test-5")
            ]
        ),
        templates=[
            IoArgoprojWorkflowV1alpha1Template(
                name='whalesay',
                container=Container(
                    image='docker/whalesay:latest', 
                    command=['sh', '-c'], 
                    args=["cowsay {0} > /tmp/hello_world.txt".format(parameter1)]),
                memoize=IoArgoprojWorkflowV1alpha1Memoize(
                    key="{0}".format(parameter1),
                    max_age='2m',
                    cache=IoArgoprojWorkflowV1alpha1Cache(
                        config_map=ConfigMapKeySelector(key="{0}".format(parameter1), name="my-config"))   
                ),
                outputs=IoArgoprojWorkflowV1alpha1Outputs(
                    parameters=[
                        IoArgoprojWorkflowV1alpha1Parameter(
                            name="message", 
                            value_from=IoArgoprojWorkflowV1alpha1ValueFrom(
                                path="/tmp/hello_world.txt")
                        )
                    ]
                )
            )
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


 