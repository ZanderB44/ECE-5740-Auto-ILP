from typing import Dict, List
import random
import sys
import os

# test variable declarations, delete from here 
memory = 10
variableStrings = {}

for y in range(1, 4):  
    random_list = []
    for i in range(3):  
        z = random.randint(1, 10)
        random_string = f"x{y}_{z}"
        random_list.append(random_string)
    variableStrings[y] = random_list

dConstraint = ["const0", "const1", "const2", "const3", "const4"]
rConstraint = ["const5", "const6", "const7", "const8", "const9"]

# to here

# if ML-RC
objStatement = memory
constraintList = dConstraint + rConstraint

with open("formulations.lp", "w") as f:
    f.write(f"Minimize \nobj: {objStatement}")

    f.write("\n\nSubject To\n")
    for i, const in enumerate(constraintList):
        f.write(f"c{i+1}:{const}\n")
    
    for i, variableList in variableStrings.items():
        for variable in variableList:
            f.write(f"i{i}:{variable} >= 0\n")
    
    f.write("\nInteger\n")
    for variable in variableStrings.values():
        string_list = " ".join(variable)
        f.write(f"{string_list} ")

os.system("glpsol formulations.lp --lp -o solution.lp")
	
	
	
