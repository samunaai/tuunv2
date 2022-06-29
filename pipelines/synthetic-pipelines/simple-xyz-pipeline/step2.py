"""
  Stage 2 in basic pipeline for f(x,y,z)=x^2 + y^2 + z^2 
  -- munachiso.nwadike@mbzuai.ac.ae
"""
import os 
import sys

def step2(out1, y):
	return out1 + y**2

if __name__ == "__main__":
	# sanity check that the input works
    print("Here is the input:", sys.argv[1])

    # sanity check that the output directory is passed correctly
    print(sys.argv[2], type(sys.argv[2]))

    # read input from step1 file 
    in_file = open(os.path.join(sys.argv[2], "step1.txt"), "r")
    in_val = int(in_file.read())
    print("Tight Print: =>{0}<=".format(in_val), type(in_val))

    # calculate new output correctly
    out_file = open(os.path.join(sys.argv[2], "step2.txt"), "w")    
    output_val = step2(in_val, int(sys.argv[1]))
    print("Here is the answer:", output_val)

    # write output for step2 fxn to "step2" file
    out_file.write(str(output_val)); out_file.close()