"""
  Stage 2 in basic pipeline simulating the 3D function f(x)=branin2d(x1,x2)+branin2d(x3,x4)
  This python file computes the first of the two branin functions
  x3 and x4 are passed in as the sys.argv 1 and 2,
  The output artifact is branin2d(x3,x4), and is written to the folder specified by sys.argv 3
  Also reads in the input1, i.e. branin2d(x1,x2), from that folder and adds that to branin for thus function
  -- *insert my email address here*
"""
import os 
import sys
import torch

from botorch.test_functions import Branin

def step2(input1, x3, x4):
    neg_branin2 = Branin(negate=True)
    return input1 + neg_branin2(torch.tensor([x3, x4])).item()

if __name__ == "__main__":
	# sanity check that the input works
    print("[Step2] Here's the inputs:", sys.argv[1], sys.argv[2])

    # sanity check that the output directory is passed correctly
    print("[Step2] Intended Output Directory =>", sys.argv[3], type(sys.argv[3]))

    # read input from step1 file 
    in_file = open(os.path.join(sys.argv[3], "step1.txt"), "r")
    in_val = float(in_file.read())
    print("[Step2] Input after Casting: =>{0}<=".format(in_val), type(in_val))

    # calculate new output correctly
    out_file = open(os.path.join(sys.argv[3], "step2.txt"), "w")    
    output_val = step2(in_val, float(sys.argv[1]), float(sys.argv[2]) )
    print("[Step2] Final Computed Answer: =>", output_val)

    # write output for step2 fxn to "step2" file
    out_file.write(str(output_val)); out_file.close()