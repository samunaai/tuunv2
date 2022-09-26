"""
  Stage 1 in basic pipeline simulating the 3D function f(x,y,z)=x^2 + y^2 + z^2 
  -- *insert my email address here*
"""
import os 
import sys

# pass output path to the python file from SDK-based workflow submitter
def step1(x):
	return x**2
    
if __name__ == "__main__":
	# sanity check that the input works
    print("Here is the Answer:", step1(int(sys.argv[1])) )

    # sanity check that the output directory is passed correctly
    print(sys.argv[2], type(sys.argv[2]))

    # calculate output correctly
    out_file = open(os.path.join(sys.argv[2], "step1.txt"), "w")
    output_val = step1(int(sys.argv[1]))

    # write output for step2 fxn to "step2" file
    out_file.write(str(output_val)); out_file.close()
