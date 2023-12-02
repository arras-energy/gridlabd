"""Convert AMI to GLM players

SYNOPSIS

	Shell: 
		$ gridlabd convert -i ami:AMI.csv,ami_key:AMI_KEYS.csv, network:NETWORK.csv 
			-o PLAYERS.csv -f xlsx-spida -t csv-geodata [OPTIONS ...]

	GLM: 
		#convert ami:AMI.csv,ami_key:AMI_KEYS.csv 
			-o PLAYERS.csv


OPTIONS:



DESCRIPTION

	This converter extracts AMI and formulates players files that associate AMI to the 
	nodes on the network.

	The output is always a GridLAB-D PLAYER file.
"""

import pandas as pd 
import string
import math
import re
import numpy as np
import os


default_options = {
	# "include_network" : None,
}

def string_clean(input_str):
	output_str = input_str.replace(" ", "_")
	output_str = output_str.replace(".", "_")
	output_str = output_str.replace('"', "")
	return output_str

include_network = False
ami_key = False

def convert(input_files, output_file, options={}):
	print('test')

	if type(input_files) is dict:
		for key in input_files:
			if not key in ["ami","ami_key","network"]:
				print(f"WARNING [csv-ami2glm-player]: input file spec '{key}' is not valid",file=sys.stderr)
		
		if not "ami" in input_files:
			raise Exception("AMI not specified among input files")
		else:
			input_ami_file = input_files["ami"]
		
		if not "ami_key" in input_files:
			input_ami_key_file = None
		else:
			input_ami_key_file = input_files["ami_key"]
			global ami_key
			ami_key = True

		if "network" in input_files:
			global include_network
			include_network = input_files["network"]


	elif type(input_files) is str:
		input_ami_file = input_files
	else:
		raise Exception("input_files is not dict or str")

	# read default options into globals
	for name, value in default_options.items():
		globals()[name] = value

	# read user options into globals
	for name, value in options.items():
		if name not in default_options.keys():
			raise Exception("option '{name}={value}' is not valid")
		globals()[name] = value

	df_ami = pd.read_csv(input_ami_file)

	node_ID_set = set(df_ami['transformer_structure'])

	with open(output_file, mode='w', newline='') as file :  
		writer = csv.writer(file)
		writer.writerow(['module tape;'])

		for node_ID in node_ID_set : 
			writer.writerow(['\n'])
			writer.writerow(['object player {\n'])
			writer.writerow(['\tproperty measured_real_energy;\n'])
			writer.writerow(['\tparent ' + node_ID + '\n'])
			writer.writerow(['\tfile ./player/' + node_ID + '.csv\n'])
			writer.writerow(['}\n'])




