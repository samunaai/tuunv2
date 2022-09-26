"""
  Stage 3 in basic pipeline for f(x,y,z)=x^2 + y^2 + z^2 
  -- *insert my email address here*
"""
import os
import sys

def step3(out2, z):
	return out2 + z**2

if __name__ == "__main__":
	# sanity check that the input works
    print("Input to Step3:", sys.argv[1])

    # sanity check that the output directory is passed correctly
    print(sys.argv[2], type(sys.argv[2]))

    # read input from step2 file 
    in_file = open(os.path.join(sys.argv[2], "step2.txt"), "r")
    in_val = int(in_file.read())
    print("Sanity input Print: ~>{0}<~".format(in_val), type(in_val))

    # calculate new output correctly
    out_file = open(os.path.join(sys.argv[2], "step3.txt"), "w")    
    output_val = step3(in_val, int(sys.argv[1]))
    print("Answer for Step3:", output_val)

    # write output for step3 fxn to "step3" file
    out_file.write(str(output_val)); out_file.close()
