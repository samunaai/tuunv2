"""

The core purpose of this Python file is to store "helper functions" ~
e.g functions which helps us monitor workflow logs and return objective values.

"""    
from datetime import datetime
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
        print("\t\t[TuunV2-WSS] .. Waiting {0} secs pre-workflow completion check #{1}".format(refresh_window,i))
        time.sleep(refresh_window) # wait a predefined number of seconds to check workflow progress
        response = requests.get(url=url, verify=False)
        response_dict = response.json() 
        print("\t\t[TuunV2-WSS] .. Status @ time window{0} ==".format(i), response_dict['metadata']['labels']['workflows.argoproj.io/phase'] ) 
        if response_dict['metadata']['labels']['workflows.argoproj.io/phase'] != "Running":
            print("\t\t\t\t[TuunV2-WSS] ++> Workflow has finished Running! ")
            break  
        i+=1  

    return response_dict['metadata']['labels']['workflows.argoproj.io/phase']

def time_difference(start_time, end_time):
    """Use python library datetime, to parse Argo timestamps properly"""
    dt_object1 = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    dt_object2 = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
    return (dt_object2 - dt_object1).total_seconds()

def calculate_duration(leaf_node_name, url, workflow_name):

    """
    Function that builds on the knowledge I gained playing with `print_stepgroups_pods_duration` function
    Should return both total pod durations and total stepgroup durations
    """
    response = requests.get(url=url, verify=False)
    response_dict = response.json() 

    ptr = workflow_name # pointer to root node name
    bit = 0
    wf_time = 0; pod_total = 0; sg_total = 0; # times to be returned from the parses
    pod_runtimes_list = []

    while True:
        '''---These first lines are concerned with collecting time at current node---'''
         
        node_type = response_dict['status']['nodes'][ptr]['type']
        start_time = response_dict['status']['nodes'][ptr]['startedAt']
        end_time = response_dict['status']['nodes'][ptr]['finishedAt']

        node_time = time_difference(start_time, end_time)
        
        if node_type == "Steps":
            wf_time = node_time
        elif node_type == "StepGroup":
            sg_total += node_time
        elif node_type == "Pod":
            pod_total += node_time  
            pod_runtimes_list.append(node_time)
        '''---The below lines are concerned with looping throught the workflow graph/tree correctly---'''
        if bit==1: break # (A) using this to make sure the loop stops at the last node 
        ptr = response_dict['status']['nodes'][ptr]['children'] # we are going to loop from root to leaf
        if len(ptr) > 1: raise ValueError("[TuunV2] --> Whoops ~(`_`)~  Seems the workflow isn't a Bamboo  ")
        ptr = ptr[0] # if we are safe and working with a bamboo, just take 1st (and thereby only) element in the list 
        if ptr==leaf_node_name: 
        	bit = 1; # (B) using this to make sure the loop stops at the last node
        	# print("[TuunV2] --> We Reached The Leaf!");  
        	
    return wf_time, pod_total, sg_total, pod_runtimes_list
 
def read_pod_logs_via_k8s(pod_name):

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

    # read a pod in a given namespace - see  https://raw.githubusercontent.com/kubernetes-client/python/master/kubernetes/docs/CoreV1Api.md
    log_output = v1.read_namespaced_pod_log(name=pod_name,
                                        namespace='argo', container="main")

    for line in log_output.splitlines():
    	if line[:8]=="funcVal:":
    		return float(line[8:])
    return None

def print_stepgroups_pods_duration(leaf_node_name, url, workflow_name):

    """
    Function that prints step durations for pods and for step groups separately
    Wrote this just to help us get a better sense of duration as reported by argo
    """
    response = requests.get(url=url, verify=False)
    response_dict = response.json() 

    ptr = workflow_name # pointer to root node name
    # print("LEAFYLEAFY",leaf_node_name)
    bit = 0
    while True:
        print("BLURB==>", ptr)   
        print("herbbb==>", response_dict['status']['nodes'][ptr]['type'])   
        # print("TOARBB==>", response_dict['status']['nodes'][ptr].keys(), "\n")   
        print("TOARBB==>", response_dict['status']['nodes'][ptr]['startedAt'], "~", response_dict['status']['nodes'][ptr]['finishedAt'],"\n")   
        
        if bit==1: break

        ptr = response_dict['status']['nodes'][ptr]['children'] # we are going to loop from root to leaf
        if len(ptr) > 1: raise ValueError("[TuunV2] --> Whoops ~(`_`)~  Seems the workflow isn't a Bamboo  ")
        ptr = ptr[0] # if we are safe and working with a bamboo, just take 1st (and thereby only) element in the list 
        
        if ptr==leaf_node_name: print("[TuunV2] --> We Reached The Leaf!"); bit = 1 
    return None

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
