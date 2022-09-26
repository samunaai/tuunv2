"""
  Stage 2 in basic pipeline simulating the 3D function f(x)=branin2d(x1,x2)+hartmann6d(x3,x4,x5,x6)
  This python file computes the first of the two functions
  x3 to x6 are passed in as the sys.argv 1 to 4,
  The output artifact is hartmann6d(x3,x4,x5,x6), and is written to the folder specified by sys.argv 5
  Also reads in the input1, i.e. branin2d(x1,x2), and adds to the hartmann output
  -- *insert my email address here*
"""
import os 
import sys
import torch

from botorch.test_functions import Hartmann

def step2(input1, x3, x4, x5, x6):
    neg_hartmann6 = Hartmann(negate=True)
    return input1 + neg_hartmann6(torch.tensor([x3, x4, x5, x6])).item()

if __name__ == "__main__":
	# sanity check that the input works
    print("[Step2] Here's the inputs:", sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

    # sanity check that the output directory is passed correctly
    print("[Step2] Intended Output Directory =>", sys.argv[5], type(sys.argv[5]))

    # read input from step1 file 
    in_file = open(os.path.join(sys.argv[5], "step1.txt"), "r")
    in_val = float(in_file.read())
    print("[Step2] Input after Casting: =>{0}<=".format(in_val), type(in_val))

    # calculate new output correctly
    out_file = open(os.path.join(sys.argv[5], "step2.txt"), "w")    
    output_val = step2(in_val, float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]) )
    print("[Step2] Final Computed Answer: =>", output_val)

    # write output for step2 fxn to "step2" file
    out_file.write(str(output_val)); out_file.close()