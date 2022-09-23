"""Code for EEIPU"""
from botorch.acquisition.analytic import AnalyticAcquisitionFunction
from botorch.acquisition.objective import  IdentityMCObjective, MCAcquisitionObjective, PosteriorTransform 
from botorch.models.model import Model
from botorch.sampling.samplers import MCSampler, SobolQMCNormalSampler
from botorch.utils.transforms import concatenate_pending_points, match_batch_shape, t_batch_mode_transform 

from torch import Tensor
from torch.distributions import Normal
from typing import Any, Dict, Optional, Union

import torch

class EIPUVariants(AnalyticAcquisitionFunction): 
    r"""Modification of Standard Expected Improvement Class defined in BoTorch
    See: https://botorch.org/api/_modules/botorch/acquisition/analytic.html#ExpectedImprovement
    """ 

    def __init__(
        self,
        model: Model,
        cost_model: Model,
        best_f: Union[float, Tensor],
        cost_sampler: Optional[MCSampler] = None,
        acq_objective: Optional[MCAcquisitionObjective] = None,
        posterior_transform: Optional[PosteriorTransform] = None,
        maximize: bool = True,
        acq_type: str = "", 
        cost_func = None,
        unnormalise_func = None,
        bounds: Tensor = None, # min, max
        cfg: Dict = None,
        **kwargs: Any,
    ) -> None:
        r"""q-Expected Improvement.

        Args:
            model: A fitted objective model.
            cost_model: A fitted cost model.
            best_f: The best objective value observed so far (assumed noiseless).  
            cost_sampler: The sampler used to draw base samples.  
            acq_objective: The MCAcquisitionObjective under which the samples are evaluated.
                Defaults to `IdentityMCObjective()`.
            posterior_transform: A PosteriorTransform (optional). 
            maximize: If True, consider the problem a maximization problem.
        """
        super().__init__(
            model=model,  
            posterior_transform=posterior_transform,
            **kwargs
        )
        self.maximize = maximize
        if not torch.is_tensor(best_f):
            best_f = torch.tensor(best_f)
        self.register_buffer("best_f", best_f)
        self.cost_model = cost_model
        self.cost_sampler = cost_sampler
        self.acq_obj = acq_objective  
        self.acq_type = acq_type
        self.cost_func = cost_func
        self.unnormalise_func = unnormalise_func
        self.bounds = bounds
        self.cfg = cfg

    def compute_expected_inverse_cost(self, X: Tensor) -> Tensor:
        r""" Custom function. 
        """
        cost_posterior = self.cost_model.posterior(X)
        cost_samples = self.cost_sampler(cost_posterior) 
        cost_samples = cost_samples.max(dim=2)[0]
        # Note: Unnormalize Sampled Cost Values Here
        if self.cfg['normalize_bit']['c']: # only unnormalize cost if we normalized it to fit the GP
            cost_samples = self.unnormalise_func(cost_samples, norm_type='c', orig_bounds=self.bounds['c']) 
        cost_obj = self.acq_obj(cost_samples)
        inv_cost =  1/cost_obj
        inv_cost =  inv_cost.mean(dim=0)
        return inv_cost


    def direct_expected_inverse_cost(self, X: Tensor) -> Tensor:
        r""" TO-DO.
        """
        cost_posterior = self.cost_model.posterior(X) 
        mean = cost_posterior.mean
        if self.cfg['normalize_bit']['1/c']: # only unnormalize cost if we normalized it to fit the GP
            mean = self.unnormalise_func(mean, norm_type='1/c', orig_bounds=self.bounds['1/c']) 
        return mean.squeeze()

    def compute_expected_cost(self, X: Tensor) -> Tensor:
        r""" Custom function.
        Used for debugging the return value of expected inverse cont function above.
        """
        cost_posterior = self.cost_model.posterior(X)
        cost_samples = self.cost_sampler(cost_posterior) 
        cost_samples = cost_samples.max(dim=2)[0]
        # Note: Unnormalize Sampled Cost Values Here
        if self.cfg['normalize_bit']['c']: # only unnormalize cost if we normalized it to fit the GP
            cost_samples = self.unnormalise_func(cost_samples, norm_type='c', orig_bounds=self.bounds['c']) 
        cost_obj = self.acq_obj(cost_samples) 
        return cost_obj.mean(dim=0)

    @t_batch_mode_transform(expected_q=1, assert_output_shape=False)
    def forward(self, X: Tensor) -> Tensor:
        r"""Evaluate qExpectedImprovement on the candidate set `X`.
        """ 
        self.best_f = self.best_f.to(X)
        posterior = self.model.posterior(
          X=X, posterior_transform=self.posterior_transform
        )
        mean = posterior.mean
        view_shape = mean.shape[:-2] if mean.shape[-2] == 1 else mean.shape[:-1]
        mean = mean.view(view_shape)
        sigma = posterior.variance.clamp_min(1e-9).sqrt().view(view_shape)
        u = (mean - self.best_f.expand_as(mean)) / sigma
        if not self.maximize:
            u = -u
        normal = Normal(torch.zeros_like(u), torch.ones_like(u))
        ucdf = normal.cdf(u)
        updf = torch.exp(normal.log_prob(u))
        ei = sigma * (updf + u * ucdf)
        if self.acq_type == "EIPU":
            if self.cfg['normalize_bit']['x']: # if X was normalized pre-GP-fit, unnormalize for true cost calculation
                X_new = self.unnormalise_func(X.squeeze(1) + 0, norm_type='x', orig_bounds=self.bounds['x'])   
                return ei / self.cost_func(X_new, cfg=self.cfg).squeeze()  
            return ei / self.cost_func(X.squeeze(1), cfg=self.cfg).squeeze() # otherwise just calculate cost straightup
     
        elif self.acq_type == "EEIPU":
            inv_cost =  self.compute_expected_inverse_cost(X)
            return ei * inv_cost
      
        elif self.acq_type == "EEIPU-INV":
            inv_cost = self.direct_expected_inverse_cost(X)
            return ei * inv_cost
        else:
            raise Exception("ERROR: Only EIPU, EEIPU, EEIPU-INV are supported!")