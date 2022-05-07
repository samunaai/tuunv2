# Tuunv2

Our consists of 4 key architectural components, which need to be put together in order to run:
1. Docker: This is used at the fundamental tool for running containers. Each docker container is a self-contained operating system
2. Kubernetes/Microkubernetes (aka. K8s/microk8s): This serves as a resource provisioner to manage how computation resources are assigned to different container instances or collections, called pods
3. Argo (specifically Argo Workflows): This is used for executing pipelines, it's core advantage being its inbuilt support for memoisation of experimental results 
4. Katib: This serves as an experiment scheduler. In Katib you generally assign a range of parameters, and Katib will choose the best parameters to optimise your results - we extend its functionality by incorporating it into a pipeline tuning setting.
 
<img width="609" alt="stack" src="https://user-images.githubusercontent.com/22077758/167262999-decb132d-2bbb-410e-8806-b3bf50f0e420.PNG">


The diagram below shows a flow chart explaining our stack

# Docker

# Kubernetes
# Argo
# Katib
