"""

The core purpose of this Python file is to pick which workflow submitter we aim to use~
Each objective function has a different corresponding workflow submitter

"""    
import simple_xyz


def submit_workflow(param_dict={}, wf_type=""):
    if wf_type=="xyz":
        return simple_xyz.submit_workflow([param_dict['x'],param_dict['y'],param_dict['z']], param_dict['iters'])
    elif wf_type=="norm":
        pass
    else:
        raise Exception("ERROR: That Worklow Type is not supported!")
