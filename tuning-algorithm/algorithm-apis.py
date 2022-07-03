
class TuningAlgorithm()
  def __init__(self, name, age):
    self.name = name
    self.age = age

  def compute_next_eval_point(self, acq_function):
    self.compute 

  def wss_plugin_function():


  def run_algorithm_loop():

  	for i in range(query_budget):
  		(1) select_point
		(2) evaluate_point
			pass_x value to wss => y = wss_plugin_function(x)
			return the cost from wss (we might now use yet, qirong just wants us to have it for later)
		(3) update acquisition function
			in case of random search => pass
			in case of BO => update acquisition function (includes some mod to prior prob distribution inherently)

## RANDOM SEARCH
- Set a domain
- Check randomly in the range 
- Run algorithm for those values, repeat again

## BO
- Instead of random selection, we have acquisition function  
- Use AF to get new query points (best)
- Use function value (y) and query points (x) to update model (e.g GP) just so we can have better prior acq function




class RandomSearch()
  def __init__(self, name, age):
    self.name = name
    self.age = age

  def compute_next_eval_point(self, acq_function):
    self.compute 

  def pass_message_to_wss():




class GridSearch()
  def __init__(self, name, age):
    self.name = name
    self.age = age

  def compute_next_eval_point(self, acq_function):
    self.compute 

  def pass_message_to_wss():



class VanillaBayesianOptimisation()
  def __init__(self, name, age):
    self.name = name
    self.age = age

  def compute_next_eval_point(self, acq_function):
    self.compute 

  def pass_message_to_wss():



if name == __main__:
  run ta algorithm using class above
  and at each iteration, pass the new set of parameters to the python sdk file muna wrote

  outer loop
    inner loop
      pass parameters to sdk and get results back (objective function; cost)
