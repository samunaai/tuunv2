"""

The core purpose of this Python file is to store "helper functions" ~
e.g functions which helps us monitor workflow logs and return objective values.

"""    

from kubernetes import client, config

import requests  
import time

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
