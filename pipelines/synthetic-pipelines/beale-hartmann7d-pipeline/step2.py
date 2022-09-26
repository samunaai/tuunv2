"""
  Stage 2 in basic pipeline simulating the 3D function f(x)=-beale2d(x1,x2)-hartmann3d(x3,x4,x5)-beale2d(x6,x7)
  This python file computes the second of the three branin functions
  x3, x4, x5 are passed in as the sys.argv 1, 2, 3
  Also reads in the input1, i.e. -beale2d(x1,x2), from that folder and adds that to branin for thus function
  The output artifact is =-beale2d(x1,x2)-hartmann3d(x3,x4,x5), and is written to the folder specified by sys.argv 3
  -- *insert my email address here*
"""
import os 
import sys
import torch

from botorch.test_functions import Hartmann

def step2(input1, x3, x4, x5):
    neg_hartmann3 = Hartmann(dim=3, negate=True)
    return input1 + neg_hartmann3(torch.tensor([x3, x4, x5])).item()

if __name__ == "__main__":
	# sanity check that the input works
    print("[Step2] Here's the inputs:", sys.argv[1], sys.argv[2], sys.argv[3])

    # sanity check that the output directory is passed correctly
    print("[Step2] Intended Output Directory =>", sys.argv[4], type(sys.argv[4]))

    # read input from step1 file 
    in_file = open(os.path.join(sys.argv[4], "step1.txt"), "r")
    in_val = float(in_file.read())
    print("[Step2] Input after Casting: =>{0}<=".format(in_val), type(in_val))

    # calculate new output correctly
    out_file = open(os.path.join(sys.argv[4], "step2.txt"), "w")    
    output_val = step2(in_val, float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]) )
    print("[Step2] Step2 Computed Answer: =>", output_val)

    # write output for step2 fxn to "step2" file
    out_file.write(str(output_val)); out_file.close()
