"""
---------> HOW TO GET BEARER TOKENS TO WORK IN HERA <---------
Two example hera python files are shown below, the first works and submits a neat workflow in argo dashboard, 
while the second submits a workflow which throws an error; this python file is meant to document how I got tokens to work:
- In order to obtain the bearer token to pass into WorkflowService class to get hera to work, you will need
 a. To run  "microk8s kubectl get secret -n argo" to see the list of tokens 
 b. Find the correct token name from the list - the one starting with "argo-token" should be perfect
 c. Run "microk8s kubectl describe secret <token-name> -n argo" and copy paset the token into the token field as shown below
"""

"""
--> EXAMPLE 1 <--
Copy pasted the Hera hellow world example found in the link below, and added in token
https://github.com/argoproj-labs/hera-workflows/blob/69a996731ee0c7d10e12838b7e9e5d1fa3540dc4/examples/hello_hera.py
"""
from hera import Task, Workflow, WorkflowService
def hello():
    print('Hello, Hera!')

token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjBOaDJoR0hVS25meFhHMDJVNDVYZkFkekNTVHg1a2JFUk5fc0VMT2ZwaHMifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhcmdvIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImFyZ28tdG9rZW4teDQ5MnoiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiYXJnbyIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6Ijg5YTRjMzk4LTM4ZWUtNDhkYi1iYjcwLWFjNjhkMjM3YTdmNyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDphcmdvOmFyZ28ifQ.Z4YugHjkRdGrfl9oA_BrgTktnlyvbgAgyYAasxngpL-dV9FWi94CtTS6axLx1SpL8umOHI56GqTQhFBadbt_cbWNgRQXe7mv5EHGPBKSvdadYUfeNW655MZsI4Y_8ov_-3uQ-spvIYEXADYelwHHSh6dvomG4_TrOk9Jk5N5quc4zjCecR8jLpcKHLSsen1yDTnLjgSUPBjmjjNkvAaPE-Maphv80rwALZc6AOuZZlYUF4dJamGNptPqylyTKh8enzJCKltxI_UTra8-BiomasrsluOWBJXMR91YHvgyRAAko_C8fTcwWE04hwKN9qN_69UNLOZNRrjGl529uhppGg"
ws = WorkflowService(host='https://localhost:2746/', token=token, verify_ssl=False)
w = Workflow('hello-hera', service=ws, namespace="argo")
t = Task('t', hello)
w.add_task(t)
w.create()



""" 
--> EXAMPLE 2 <--
Attempted to modify the hera container example found in link below to have memoization
https://github.com/argoproj-labs/hera-workflows/blob/69a996731ee0c7d10e12838b7e9e5d1fa3540dc4/examples/container.py

At the time hera had no memoization example, links used to try to figure out how it works are:
- https://github.com/argoproj-labs/hera-workflows/blob/46334af45859e1301cd43bc87f2217a36b995bb0/tests/test_memoize.py
- https://github.com/argoproj-labs/hera-workflows/blob/69a996731ee0c7d10e12838b7e9e5d1fa3540dc4/src/hera/memoize.py
- https://github.com/argoproj-labs/hera-workflows/blob/69a996731ee0c7d10e12838b7e9e5d1fa3540dc4/src/hera/task.py#L172
- https://github.com/argoproj-labs/hera-workflows/blob/69a996731ee0c7d10e12838b7e9e5d1fa3540dc4/tests/test_task.py#L305
- https://github.com/argoproj-labs/hera-workflows/blob/69a996731ee0c7d10e12838b7e9e5d1fa3540dc4/examples/input_output.py

"""
from hera import (
	GlobalInputParameter, Input, Memoize, Task, Workflow, WorkflowService
	)


def say(a: str):
    print(a)


token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjBOaDJoR0hVS25meFhHMDJVNDVYZkFkekNTVHg1a2JFUk5fc0VMT2ZwaHMifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhcmdvIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImFyZ28tdG9rZW4teDQ5MnoiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiYXJnbyIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6Ijg5YTRjMzk4LTM4ZWUtNDhkYi1iYjcwLWFjNjhkMjM3YTdmNyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDphcmdvOmFyZ28ifQ.Z4YugHjkRdGrfl9oA_BrgTktnlyvbgAgyYAasxngpL-dV9FWi94CtTS6axLx1SpL8umOHI56GqTQhFBadbt_cbWNgRQXe7mv5EHGPBKSvdadYUfeNW655MZsI4Y_8ov_-3uQ-spvIYEXADYelwHHSh6dvomG4_TrOk9Jk5N5quc4zjCecR8jLpcKHLSsen1yDTnLjgSUPBjmjjNkvAaPE-Maphv80rwALZc6AOuZZlYUF4dJamGNptPqylyTKh8enzJCKltxI_UTra8-BiomasrsluOWBJXMR91YHvgyRAAko_C8fTcwWE04hwKN9qN_69UNLOZNRrjGl529uhppGg"
ws = WorkflowService(host='https://localhost:2746/', token=token, verify_ssl=False)
w = Workflow('container', service=ws, namespace="argo")

t = Task('cowsay', say, [{'a':1}], #also tried to pass "None" instead of say function since I just needed docker container commands to run
	image='docker/whalesay', 
	command=['cowsay', 'foo'], memoize=Memoize('a', 'cache1', '5m'))
w.add_task(t)
w.create()

 