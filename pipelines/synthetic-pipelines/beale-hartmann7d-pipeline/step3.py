"""
  Stage 2 in basic pipeline simulating the 3D function f(x)=-beale2d(x1,x2)-hartmann3d(x3,x4,x5)-beale2d(x6,x7)
  This python file computes the first of the two branin functions
  x6 and x7 are passed in as the sys.argv 1 and 2,
  Also reads in the input1, i.e. -beale2d(x1,x2)-hartmann3d(x3,x4,x5) 
  The output artifact is written to the folder specified by sys.argv 3
  -- *insert my email address here*
"""
import os 
import sys
import torch

from botorch.test_functions import Beale

def step3(input2, x6, x7):
  neg_beale2 = Beale(negate=True)
  return input2 + neg_beale2(torch.tensor([x6, x7])).item()
        
if __name__ == "__main__":
	# sanity check that the input works
    print("[Step3] Here's the inputs:", sys.argv[1], sys.argv[2])

    # sanity check that the output directory is passed correctly
    print("[Step3] Intended Output Directory =>", sys.argv[3], type(sys.argv[3]))

    # read input from step1 file 
    in_file = open(os.path.join(sys.argv[3], "step2.txt"), "r")
    in_val = float(in_file.read())
    print("[Step3] Input after Casting: =>{0}<=".format(in_val), type(in_val))

    # calculate new output correctly
    out_file = open(os.path.join(sys.argv[3], "step3.txt"), "w")    
    output_val = step3(in_val, float(sys.argv[1]), float(sys.argv[2]) )
    print("[Step3] Step3 Final Answer: =>", output_val)

    # write output for step2 fxn to "step2" file
    out_file.write(str(output_val)); out_file.close()
