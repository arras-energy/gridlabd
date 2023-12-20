"""Convert AMI to GLM players

SYNOPSIS

	Shell: 
		$ gridlabd convert -i ami:AMI.csv,ami_key:AMI_KEYS.csv, network:NETWORK.csv 
			-o PLAYERS.csv -f csv-ami -t glm-player [OPTIONS ...]

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
import csv


default_options = {
	# "include_network" : None,
	"folder_name" : "./player/"
}

def string_clean(input_str):
	output_str = input_str.replace(" ", "_")
	output_str = output_str.replace(".", "_")
	output_str = output_str.replace('"', "")
	return output_str

include_network = False
ami_key = False

def convert(input_files, output_file, options={}):

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

	df = pd.DataFrame({'class': ['player']*len(node_ID_set), 'parent' : list(node_ID_set), 'file' : ['player_' + str(node) + '.csv' for node in node_ID_set]})
	
	if "folder_name" in options : 
		player_folder = options["folder_name"]
	else : 
		player_folder = default_options["folder_name"]
	if not os.path.exists(player_folder):
		os.makedirs(player_folder)
	if os.path.splitext(output_file)[1]=='.csv' : 

			df.to_csv(player_folder+output_file, index=False)
	elif os.path.splitext(output_file)[1]=='.glm' :
		with open(output_file, mode='w') as file :  
			file.write('module tape;\n')

			for node_ID in node_ID_set : 
				file.write('object player {\n')
				file.write('\tparent "' + str(node_ID) + '";\n')
				file.write('\tfile "'+player_folder + str(node_ID) + '.csv";\n')
				file.write('}\n')

	new_column_names = {
		'reading_dttm': 'timestamp',
		'net_usage': 'power[kW]',
		'transformer_structure': 'customer_id'
	}
	df_ami.rename(columns=new_column_names,inplace=True)
	[df_ami.drop(x,axis=1,inplace=True) for x in ['interval_pcfc_date','interval_pcfc_hour']];
	df_ami.sort_index(inplace=True)

	# Iterate over unique customer IDs
	for customer_id in df_ami['customer_id'].unique():
	    # Create a new DataFrame for each customer ID
		customer_df = df_ami[df_ami['customer_id'] == customer_id].drop(columns='customer_id')
		customer_df = customer_df.sort_values(by='timestamp')
	    # Save the DataFrame to a CSV file
		output_file = f"{folder_name}{customer_id}.csv"
		customer_df.to_csv(output_file, index=False, header=False)


