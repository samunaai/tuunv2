# Tuunv2

Our consists of 4 key architectural components, which need to be put together in order to run:
1. Docker: This is used at the fundamental tool for running containers. Each docker container is a self-contained operating system
2. Kubernetes/Microkubernetes (aka. K8s/microk8s): This serves as a resource provisioner to manage how computation resources are assigned to different container instances or collections, called pods
3. Argo (specifically Argo Workflows): This is used for executing pipelines, it's core advantage being its inbuilt support for memoisation of experimental results 
4. Katib: This serves as an experiment scheduler. In Katib you generally assign a range of parameters, and Katib will choose the best parameters to optimise your results - we extend its functionality by incorporating it into a pipeline tuning setting.
 
<img width="609" alt="stack" src="https://user-images.githubusercontent.com/22077758/167262999-decb132d-2bbb-410e-8806-b3bf50f0e420.PNG">


The diagram below shows a flow chart explaining our stack

## 1. Docker

## 2. Kubernetes
We recommend 2 readily available option for Kubernetes usage:

a) Kubernetes: This is the full production ready version of Kubernetes. It be installed using the [official documentation](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/).

b) Microk8s: microkubernets is a lightweight version of kubernetes. It is not suitable in production, but is quick to setup for rapid prototyping following [official documentation](https://microk8s.io/docs/getting-started).

GPU support for kubernetes needs to be [enabled separately](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/). Likewise for microk8s. For microk8s, you need to work with precise software versions for GPU to work - we tested using microk8s 1.22, on Ubuntu 18.04. The nvidia drive was 470.103.01, with cuda 11.4

- `microk8s enable dns storage`: make sure to run these commands while installing microk8s as per the docs linked above. Otherwise argo will not install.
- `microk8s enable gpu`: This command enables gpu in microk8s. If run correctly, a number of pods under the namesapce `gpu-operator-resources` will be started and their status will be either "running" or "completed", after just a few minutes. Furthermore, when we run `microk8s kubectl describe node`, "nvidia.com/gpu" will be listed under the allocated resources, as shown below:

    > <img width="609" alt="stack" src="https://user-images.githubusercontent.com/22077758/167264785-3fea4514-103b-4efd-a600-7408afdf72e2.png">
 

## 3. Argo

- `kubectl create ns argo` && `kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo-workflows/master/manifests/quick-start-postgres.yaml` :  If Argo server is running correctly, when we run `kubectl get pods -A`, there should be 4 pods running under the namespaces argo. It is okay if these pods restart a few times, but they should all be up and running within ~2-5 minutes. Otherwise there may be an error.

    > <img width="800" alt="argo" src="https://user-images.githubusercontent.com/22077758/167264108-3b8f26ee-1be5-4362-a6c2-39e0a5ab09ce.png">


## 4. Katib
