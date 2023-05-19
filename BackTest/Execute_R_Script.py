import subprocess

# File Directory to start when locating the correct R script to run, all R scripts should be placed in the 'R_Scripts' folder
FILEPATH = 'R_Scripts/'


# Executes a given R Script given the name of the file
# @Param scriptName: the name of the script to execute
def runScript(scriptName):
    print(FILEPATH + scriptName)
    subprocess.run(['RScript',FILEPATH + scriptName])