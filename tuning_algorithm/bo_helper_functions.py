"""Code for EEIPU"""

from botorch.models import SingleTaskGP
from botorch.optim.optimize import optimize_acqf

from gpytorch.mlls import ExactMarginalLogLikelihood

import torch


def normalize(val, norm_type=None, bounds=None): 
    '''For X values: subtract the min bound and divide by the range to shift into (0,1)
       For Objective/Cost values: First shift into (0,1), then into (-1,1)'''
    if norm_type=='x': 
        X = val + 0 # neat computational copy of X 
        for dim in range(len(bounds[0])): # we want in (0,1)
            X[:, dim] = (X[:, dim] - bounds[0][dim].item()) / (bounds[1][dim].item() - bounds[0][dim].item() ) 
        return X

    elif norm_type=='y' or norm_type=='c' or norm_type=='1/c':
        Y = val + 0  # neat computational copy of val 
        for dim in range(len(bounds[0])): # we want in (-1,1)
            Y[:, dim] = (Y[:, dim] - bounds[0][dim].item()) / (bounds[1][dim].item() - bounds[0][dim].item() )
        Y  = (Y * 2) - 1 
        return Y 

    else:
        raise Exception("Sorry, ONLY x, y, or c values can be normalised")


def unnormalize(val, norm_type, orig_bounds=None):
    '''For X values: move from (0,1) to original bounds range
       For Objective/Cost values: Similar to X, but rememeber that we'll unnormalize in-between GP fitting and acq_fun optimisation'''
    if norm_type=='x': 
        X = val + 0 # neat computational copy of val 
        for dim in range(len(orig_bounds[0])): # from (0,1) to orig range
            X[:, dim] = X[:, dim] * (orig_bounds[1][dim].item() - orig_bounds[0][dim].item()) + (orig_bounds[0][dim].item()) 
        return X 

    elif norm_type=='y' or norm_type=='c' or norm_type=='1/c': # from (-1,1) to original bounds range; 
        Y = val + 0 # neat computational copy of val 
        Y = (Y + 1) / 2 # normalise from (-1,1) into (0,1)
        for dim in range(len(orig_bounds[0])): # from (-1,1) to orig range
            Y[:, dim] = Y[:, dim] * (orig_bounds[1][dim].item() - orig_bounds[0][dim].item()) + (orig_bounds[0][dim].item()) 
        return Y 
    else:
        raise Exception("Sorry, ONLY x, y, or c values can be UNnormalised")

                
def get_random_observations(batch_size, bounds):
    '''Build random observation one dimension at a time
     This allows us to use different bounds for each hyperparameter'''
    rand_x = torch.distributions.uniform.Uniform(bounds[0][0],bounds[1][0]).sample([batch_size,1])
    for dim in range(1,len(bounds[0])):
        temp = torch.distributions.uniform.Uniform(bounds[0][dim],bounds[1][dim]).sample([batch_size,1]) 
        rand_x = torch.cat((rand_x, temp), dim=1)
    return rand_x 


def generate_cost(train_x, cfg={}):  
    if cfg['fxn_name']=='test':
        assert train_x.shape[1] == cfg['fxn_dim'] 
        ret = sigmoid(train_x[:,0], 5) 
    elif cfg['fxn_name']=='branin_4d':
        assert train_x.shape[1] == cfg['fxn_dim'] 
        # ret = CONSTANT + (train_x[:,0])**2 + (train_x[:,2])**2 +  torch.sqrt(torch.abs(train_x[:,3]))  # this one had numerical issuse due to sqrt-why?!!
        # ret = CONSTANT + (train_x[:,0])**2 + (train_x[:,2])**2  
        # print("TRAIN_X (Cost)", train_x.shape, train_x[:,0].shape, train_x[:,2].shape, train_x[:,3].shape)
        ret = cfg['CONSTANT'] + sigmoid(train_x[:,0],5) + (train_x[:,2]) + (train_x[:,3]) 
    elif cfg['fxn_name']=='branin_hartmann_8d':
        assert train_x.shape[1] == cfg['fxn_dim'] 
        # ret = train_x[:,0] + (train_x[:,1])**2 + CONSTANT + torch.sqrt(torch.abs(train_x[:,4])) + train_x[:,5] + (train_x[:,6])**2 # this one had numerical issuse due to sqrt-why?!!
        ret = train_x[:,0] + (train_x[:,1])**2 + cfg['CONSTANT'] + train_x[:,5] + (train_x[:,6])**2  
    elif cfg['fxn_name']=='beale_hartmann_7d':
        assert train_x.shape[1] == cfg['fxn_dim']  
        ret = cfg['CONSTANT'] + (train_x[:,0]) + (train_x[:,1]) + (train_x[:,2]) + (train_x[:,3])**2 + (train_x[:,4])**2 + cfg['CONSTANT'] + (train_x[:,5]) + (train_x[:,6]) 
    else:
        print("ERROR! NEED TO ASSIGN ONE OF THESE FUNCTIONS!")
        ret = None
    return ret.unsqueeze(-1)  


def generate_initial_data(n, bounds, trial_seed=None, cfg={}):
    ''' generates random initial data based on user specified bounds for each dimension (aka. for each hyperparameter)'''
    torch.manual_seed(seed=trial_seed) # uses random seed
    train_x = get_random_observations(batch_size=n, bounds=bounds)
    train_y = objective(train_x,cfg=cfg).unsqueeze(-1)  # add output dimension
    return train_x, train_y 

def initialize_model(train_x, train_y, state_dict=None, cost_kernel=None ):
    '''intialises a gaussian process model based on specified 
    hyperparameter combination and corresponding objective value'''
    init_x = train_x + 0
    init_y = train_y + 0
    model_obj = SingleTaskGP(init_x, init_y, covar_module=cost_kernel).to(init_x) # Just inheriting from PyTorch's module.to https://pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.to
    mll = ExactMarginalLogLikelihood(model_obj.likelihood, model_obj) 
    return mll, model_obj 
 


def objective(X, cfg={}):
    if cfg['fxn_name']=='test':
        assert X.shape[1] == cfg['fxn_dim'] 
        return -(torch.linalg.norm(X, dim=-1))  
    elif cfg['fxn_name']=='branin_4d':
        # print("X==>", X)
        assert X.shape[1] == cfg['fxn_dim'] 
        return cfg['neg_branin2'](X[:,:2]) + cfg['neg_branin2'](X[:,2:])
    elif cfg['fxn_name']=='branin_hartmann_8d':
        assert X.shape[1] == cfg['fxn_dim'] 
        return cfg['neg_branin2'](X[:,:2]) + cfg['neg_hartmann6'](X[:,2:]) 
    elif cfg['fxn_name']=='beale_hartmann_7d':
        assert X.shape[1] == cfg['fxn_dim']  
        return cfg['neg_beale2'](X[:,:2]) + cfg['neg_hartmann3'](X[:,2:5]) + cfg['neg_beale2'](X[:,5:])
    else:
        print("ERROR! NEED TO ASSIGN ONE OF THESE FUNCTIONS!") 
        


def optimize_acqf_and_get_observation(batch_size, acq_func, optim_bounds=None, r_seed=None):
    """Optimizes the acquisition function, and returns a new candidate and observation."""
    if acq_func=="RAND":
        new_x = get_random_observations(batch_size, optim_bounds)
        return new_x 

    candidates, _ = optimize_acqf( # https://github.com/pytorch/botorch/issues/371
        acq_function=acq_func, 
        bounds=optim_bounds,
        q=batch_size,
        num_restarts=10,
        raw_samples=500,  # used for intialization heuristic
        # batch_initial_conditions=initials,
        options={ 
            "seed": r_seed
        }
    )
    # observe new values 
    new_x = candidates.detach()
    return new_x 

def sigmoid(z, const):
    '''mathematical implementation of sigmoid function'''
    return 1./ (1 + torch.exp(-const*z))*10 + 1



