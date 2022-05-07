# Tuunv2

Our consists of 4 key architectural components, which need to be put together in order to run:
1. Docker: This is used at the fundamental tool for running containers. Each docker container is a self-contained operating system
2. Kubernetes/Microkubernetes (aka. K8s/microk8s): This serves as a resource provisioner to manage how computation resources are assigned to different container instances or collections, called pods
3. Argo (specifically Argo Workflows): This is used for executing pipelines, it's core advantage being its inbuilt support for memoisation of experimental results 
4. Katib: This serves as an experiment scheduler. In Katib you generally assign a range of parameters, and Katib will choose the best parameters to optimise your results - we extend its functionality by incorporating it into a pipeline tuning setting.
 

The diagram below shows a flow chart explaining our stack

## 1. Docker
Docker can installed using the [official instructions](https://docs.docker.com/engine/install/ubuntu/). 
- nvidia-docker2 is also required. It can be installed using official [nvidia instruction](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- Your goal should be to run an official nvidia docker container with a simple `nvidia-smi` command. For example, `sudo docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi` should display the output of `nvidia-smi`, run from within the docker container for cuda version 11.0.3. Other versions can be found at [nvidia/cuda on docker hub](https://hub.docker.com/r/nvidia/cuda)
- If installed correctly, your output will look like this (driver versions may differ):

    > <img width="400" alt="stack" src="https://user-images.githubusercontent.com/22077758/167271375-e9b31117-f699-4ee5-a44c-c86df9e8ec7b.png">


## 2. Kubernetes
We recommend 2 readily available option for Kubernetes usage:

A. Kubernetes: This is the full production ready version of Kubernetes. It be installed using the [official documentation](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/).

B. Microk8s: microkubernetes is a lightweight version of kubernetes. It is not suitable in production, but is quick to setup for rapid prototyping following [official documentation](https://microk8s.io/docs/getting-started).

Most kubernetes commands can be run with microk8s - you just need to add the keyword `microk8s` before the command. e.g `microk8s kubectl get nodes` should list the nodes in the cluster.

GPU support for kubernetes needs to be [enabled separately](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/). Likewise for microk8s. For microk8s, you need to work with precise software versions for GPU to work - we tested using microk8s 1.22, on Ubuntu 18.04. The nvidia drive was 470.103.01, with cuda 11.4


Points to note when setting up microk8s:
- `microk8s enable dns storage`: make sure to run these commands while installing microk8s as per the docs linked above. Otherwise argo will not install.
- `microk8s enable gpu`: This command enables gpu in microk8s. If run correctly, a number of pods under the namesapce `gpu-operator-resources` will be started and their status will be either "running" or "completed", after just a few minutes. Furthermore, when we run `microk8s kubectl describe node`, "nvidia.com/gpu" will be listed under the allocated resources, as shown below:

    > <img width="580" alt="stack" src="https://user-images.githubusercontent.com/22077758/167264785-3fea4514-103b-4efd-a600-7408afdf72e2.png">
 

## 3. Argo

The Argo project has several tools, but we use mainly Argo Workflows. Argo Workflows [quickstart page](https://github.com/argoproj/argo-workflows/blob/master/docs/quick-start.md) provides useful steps to get it up and running. Here are some helpful notes to provide you with additional installation advice:

- `kubectl create ns argo` && `kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo-workflows/master/manifests/quick-start-postgres.yaml` :  If Argo server is running correctly, when we run `kubectl get pods -A`, there should be 4 pods running under the namespaces argo like the image below. It is okay if these pods restart a few times, but they should all be up and running within ~2-5 minutes. Otherwise there may be an error.

    > <img width="800" alt="argo" src="https://user-images.githubusercontent.com/22077758/167264108-3b8f26ee-1be5-4362-a6c2-39e0a5ab09ce.png">

- `kubectl -n argo port-forward deployment/argo-server 2746:2746` : this will serve the argo dashboard on port 2746. If you are running the code on a remote server, make sure that you are port forwarding from the server to your computer i.e by adding  `-L 2746:localhost:2746` to your ssh command. The Argo dashboard looks like this:

    > <img width="650" alt="argo" src="https://user-images.githubusercontent.com/22077758/167265269-9f1fc5aa-8e78-4c67-a9d4-20ee1693ded7.png">



- `argo version`: When you download a version of argo from [the releases](https://github.com/argoproj/argo-workflows/releases), the output of this command should look like this:

    > <img width="500" alt="argo" src="https://user-images.githubusercontent.com/22077758/167265131-edb13cd3-2e12-43a5-b561-0da8feaf3136.png">


## 4. Katib

Katib supports experiment scheduling with several types of kubernetes custom resources, inluding Argo Workflows. The official docs explain how to integrate Argo with Katib. Verify your default runtime executor using `kubectl get ConfigMap -n argo workflow-controller-configmap -o yaml | grep containerRuntimeExecutor`. If it is not `emissary`, you will need to change it to `emissary` using `kubectl patch ConfigMap -n argo workflow-controller-configmap --type='merge' -p='{"data":{"containerRuntimeExecutor":"emissary"}}'`
