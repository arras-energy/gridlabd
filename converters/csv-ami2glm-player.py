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
import json


default_options = {
	"folder_name" : "./player/",
}

def string_clean(input_str):
	output_str = input_str.replace(" ", "_")
	output_str = output_str.replace(".", "_")
	output_str = output_str.replace('"', "")
	return output_str

network = False
ami_key = False

def write_player(file, obj, node_ID, phase) : 
	file.write('object player {\n')
	file.write('\tparent "' + obj + '";\n')
	file.write('\tfile "' + os.path.join(folder_name,str(node_ID)) + '.csv";\n')
	for p in phase : 
		file.write(f'\tproperty constant_power_{p};\n')
	file.write('}\n')

def filter_dict_by_min_value(input_dict, patterns):
    result_dict = {}
    for pattern in patterns:
        pattern_dictionary = {key: value for key, value in input_dict.items() if pattern in key}   
        min_value = min(pattern_dictionary.values())
        min_dict = {key: value for key, value in pattern_dictionary.items() if value == min_value}
        result_dict.update(min_dict)
    return list(result_dict.keys())

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
			global network
			network_path = input_files["network"]
			with open(network_path,'r') as network_json: 
				network = json.load(network_json)

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
	
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)

	if os.path.splitext(output_file)[1]=='.csv' : 
		df.to_csv(os.path.join(folder_name,os.path.basename(output_file)), index=False)
	elif os.path.splitext(output_file)[1]=='.glm' :
		phase_dict = {}
		load_list = {}
		load_list_filtered = {}
		with open(output_file, mode='w') as file :  
			file.write('module tape;\n')

			for node_ID in node_ID_set : 
				if isinstance(node_ID, float) and math.isnan(node_ID) :
					continue 
				for obj,val in network["objects"].items() : 
					if "load" in val["class"] and node_ID in obj: 
						volts = float(val['nominal_voltage'].split(' ')[0])
						if 'k' in val['nominal_voltage'].split(' ')[1] : 
							load_list[obj] = volts*1000
						elif 'M' in val['nominal_voltage'].split(' ')[1] : 
							load_list[obj] = volts*1000000
						else : 
							load_list[obj] = volts
				load_phase = ''.join([x for x in 'ABC' if x in val['phases']])
				phase_dict[node_ID]=load_phase

							
			# Grabbing only loads on the low side of the Transformer				
			load_list_filtered = filter_dict_by_min_value(load_list,node_ID_set)
			for load_ID in load_list_filtered :
				for obj, val in network["objects"].items() : 
					if load_ID==obj :
						load_phase = ''.join([x for x in 'ABC' if x in val['phases']])
						parent = val["parent"]
						for node_ID in node_ID_set : 
							if node_ID in load_ID : 
								write_player(file, obj, node_ID, load_phase)

	new_column_names = {
		'reading_dttm': 'timestamp',
		'net_usage': 'power[kW]',
		'transformer_structure': 'customer_id'
	}
	df_ami.rename(columns=new_column_names,inplace=True)
	df_ami.drop(['interval_pcfc_date','interval_pcfc_hour'],axis=1,inplace=True)
	df_ami.sort_index(inplace=True)
	# Iterate over unique customer IDs
	for customer_id in df_ami['customer_id'].unique():
	    # Create a new DataFrame for each customer ID
		if isinstance(customer_id, float) and math.isnan(customer_id) : 
			continue
		customer_df = df_ami[df_ami['customer_id'] == customer_id].drop(columns='customer_id')
		customer_df = customer_df.sort_values(by='timestamp')
		customer_df['power[kW]'] = customer_df['power[kW]']/len(phase_dict[customer_id])*1000
	    # Save the DataFrame to a CSV file
		output_file = f"{folder_name}/{customer_id}.csv"
		customer_df.to_csv(output_file, index=False, header=False)
