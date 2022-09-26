"""
  Stage 1 in basic pipeline simulating the 3D function f(x)=-beale2d(x1,x2)-hartmann3d(x3,x4,x5)-beale2d(x6,x7)
  This python file computes the first of the three branin functions
  x1 and x2 are passed in as the sys.argv 1 and 2,
  The output artifact is -beale2d(x1,x2), and is written to the folder specified by sys.argv 3
  -- *insert my email address here*
"""
import os 
import sys
import torch

from botorch.test_functions import Beale

# pass output path to the python file from SDK-based workflow submitter
def step1(x1, x2):
	neg_beale2 = Beale(negate=True)
	return neg_beale2(torch.tensor([x1, x2])).item()
    
if __name__ == "__main__":
		# sanity check that the input works
		print("[Step1] Here is the Inputs:",  float(sys.argv[1]), float(sys.argv[2]) ) 
		# sanity check that the output directory is passed correctly
		print("[Step1] Intended Output Directory =>", sys.argv[3], type(sys.argv[3]))

		# calculate output correctly
		out_file = open(os.path.join(sys.argv[3], "step1.txt"), "w")
		output_val = step1(  float(sys.argv[1]), float(sys.argv[2]) )
		print("[Step1] Here is the Output:", output_val)
		# write output for step2 fxn to "step2" file
		out_file.write(str(output_val)); out_file.close()
