"""Convert XLSX SPIDAcalc pole data to geodata

SYNOPSIS

	Shell: 
		$ gridlabd convert -i poles:POLES.xlsx,equipment:ASSETS.xlsx 
			-o GEODATA.csv -f xlsx-spida -t csv-geodata [OPTIONS ...]

	GLM: 
		#convert -i poles:POLES.xlsx,equipment:ASSETS.xlsx -o GEODATA.csv 
			-f xlsx-spida -t csv-geodata [OPTIONS ...]


OPTIONS:

	- `precision=2`: specify the number of digits in a number and function
	  		ROUND will be used (default 2)

	- `extract_equipment`: enable the conversion of pole-mounted equipment,
			dummy values will be used for equipment properties (default None)

	- `include_dummy_network`: enable the generation of a bus-type feeder,
			dummy values will be used for properties of feeder and equipment
			(default None)

	- `include_weather=NAME`: name the weather object and do not use dummy
	  		values for weather data (default None)

	- `include_mount` : enable the generation of pole mounts objects for the
	  		ability to connect poles to network

DESCRIPTION

	This converter extracts pole geodata from a SPIDAcalc pole asset report
	spreadsheet and generates a GriDLAB-D geodata CSV file.

	If only a single input file is specified without a file type
	specification, then it is assumed to be the pole data file. In
	general, multiple files are needed, in which case they must be
	specified as a series of comma-separated specifications, e.g.,
	`TYPE1:NAME1,TYPE2:NAME2,...`.  Accepted file types are

		- `pole`       Pole data from SpidaCalc (XLSX)
		- `equipment`  Equipment data from SpidaCalc (XLSX)
		- `network`    Network mapping data (CSV)

	The output is always a GridLAB-D GeoData CSV file.
"""

import pandas as pd 
import string
import math
import re
import numpy as np
import os


default_options = {
	"precision" : 2,
	"extract_equipment" : None,
	"include_dummy_network" : None,
	"include_weather" : None,
	"include_mount" : None,
}

def string_clean(input_str):
	output_str = input_str.replace(" ", "_")
	output_str = output_str.replace(".", "_")
	output_str = output_str.replace('"', "")
	return output_str

include_network = False
extract_equipment = False

def convert(input_files, output_file, options={}):

	if type(input_files) is dict:
		for key in input_files:
			if not key in ["poles","equipment","network"]:
				print(f"WARNING [xlsx-spida2csv-geodata]: input file spec '{key}' is not valid",file=sys.stderr)
		
		if not "poles" in input_files:
			raise Exception("poles not specified among input files")
		else:
			input_pole_file = input_files["poles"]
		
		if not "equipment" in input_files:
			input_equipment_file = None
		else:
			input_equipment_file = input_files["equipment"]
			global extract_equipment
			extract_equipment = True

		if "network" in input_files:
			global include_network
			include_network = input_files["network"]
			global include_mount
			include_mount = True

	elif type(input_files) is str:
		input_pole_file = input_files
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

	# check network mounts
	if include_network : 
		globals()['include_mount'] = True

	# Read all the sheets in the .xlxs file 
	file_extension = input_pole_file.split(".")[-1]
	if file_extension == 'xlsx':
		df = pd.read_excel(input_pole_file, sheet_name=0, engine='openpyxl') 
		df.columns = [col.replace("_x0020_", " ") for col in df.columns]
		desired_columns = [
			'Structure ID', 'AS-IS AGL', 'AS-IS Species', 'AS-IS GLC', 'AS-IS Length',
			'AS-IS Class', 'AS-IS Allowable Stress Adjustment',
			'AS-IS Effective Stress Adjustment', 'AS-IS GPS Point']
		df = df[desired_columns]
	elif file_extension == 'xls':
		df = pd.read_excel(input_pole_file, sheet_name=0, usecols=[
			'Structure ID', 'AS-IS AGL', 'AS-IS Species', 'AS-IS GLC', 'AS-IS Length', 
			'AS-IS Class', 'AS-IS Allowable Stress Adjustment', 
			'AS-IS Effective Stress Adjustment', 'AS-IS GPS Point']) 
	elif file_extension == 'csv':
		df = pd.read_csv(input_pole_file, usecols=[
			'Structure ID', 'AS-IS AGL', 'AS-IS Species', 'AS-IS GLC', 'AS-IS Length', 
			'AS-IS Class', 'AS-IS Allowable Stress Adjustment', 
			'AS-IS Effective Stress Adjustment', 'AS-IS GPS Point']) 

	# Read the overhead lines 
	df_lines = pd.read_csv(include_network) if include_network else pd.DataFrame()
	overheadline_names = []
	for index, row in df_lines.iterrows(): 

		if row['class']=="overhead_line" : 
			overheadline_names.append(row['name'])

	# Parse necessary columns into a format supported by Gridlabd.
	# parse_column(df_current_sheet, 'Lean Angle', parse_angle)
	# parse_column(df_current_sheet, 'Lean Direction', parse_angle)
	parse_column(df, 'AS-IS Length', parse_length)
	parse_column(df, 'AS-IS GLC', parse_circumference_to_diamater)
	parse_column(df, 'AS-IS AGL', parse_length)
	parse_column(df, 'AS-IS Effective Stress Adjustment', parse_pressure) # for sec data
	parse_column(df, 'AS-IS GPS Point', check_lat_long)

	# Prepare GPS Point column for splitting and split value into lat and long. 
	df['AS-IS GPS Point'] = df['AS-IS GPS Point'].apply(lambda x: str(x).replace('', ',') if str(x) == '' else str(x))
	df[['latitude','longitude']] = df['AS-IS GPS Point'].str.split(',', expand=True)

	# Subtract agl from length to get depth. 
	for row in range(0,len(df['AS-IS AGL'])):
		try: 
			df.at[row,'AS-IS AGL'] = subtract_length_columns(str(df.at[row,'AS-IS Length']), str(df.at[row,'AS-IS AGL']), 'AS-IS Length', 'AS-IS AGL', row)

		except ValueError as e: 
			df.at[row,'AS-IS AGL'] = ""

	# Missing tilt angle and direction, set to default 0 
	columns_to_ensure = ['Lean Angle', 'Lean Direction']

	# Loop through the columns you want to ensure
	for col in columns_to_ensure:
		if col not in df.columns:
			df[col] = 0

	# Rename columns to its corresponding column name in Gridlabd.
	# I believe class in the file is referring to grade, so it is renamed. 
	df.rename(columns = {'Structure ID' : 'name', 'AS-IS Effective Stress Adjustment': 'fiber_strength',\
		 'AS-IS Length' : 'pole_length', 'AS-IS GLC' : 'ground_diameter', 'AS-IS AGL' : 'pole_depth',\
		  'Class': "grade", 'Lean Angle': 'tilt_angle', 
		'Lean Direction': 'tilt_direction'}, inplace=True) # for sec data

	# Split GPS Point into longitude and latitude, then parse.
	# Remove original GPS Point column
	df.drop(columns = {'AS-IS GPS Point'},axis=1,inplace=True) # sce data

	# Split the dataframe based on properties of pole_config and pole_library.
	df_pole_config = df[['pole_length', 'pole_depth', 'ground_diameter', 'fiber_strength']].copy()
	df_pole_library = df[['tilt_angle', 'tilt_direction', 'latitude', 'longitude']].copy()

	# # # Adding a pole mount for each pole 
	# if include_mount : 
	# 	df_pole_mount = df[['tilt_angle']].copy()
	# 	df_pole_mount.drop(['tilt_angle'],axis=1, inplace=True)
	# 	df_pole_mount['class'] = 'powerflow.pole_mount'
	# Specify class of the properties.
	df_pole_config.loc[:,'class'] = 'powerflow.pole_configuration'
	df_pole_library.loc[:,'class'] = 'powerflow.pole'
	

	# Additional properties for each class. These values are just for testing purposes for now. 
	pole_configuration_name = []
	pole_name = []
	pole_mount_name = []

	for i in range(len(df["name"])):
		pole_configuration_name.append(f"pole_configuration_{df['name'][i]}")
		pole_name.append(f"pole_{df['name'][i]}")


	df_pole_config.loc[:,'class'] = 'pole_configuration'
	df_pole_library.loc[:,'class'] = 'pole'

	
	df_pole_config.loc[:,'name'] = pole_configuration_name
	df_pole_library.loc[:,'configuration'] = pole_configuration_name
	df_pole_library.loc[:,'name'] = pole_name
	

	if include_weather:
		df_pole_library.loc[:,'weather'] = include_weather
	else:
		df_pole_library.loc[:,'wind_speed'] = '0 m/s'
		df_pole_library.loc[:,'wind_direction'] = '0 deg'
	df_pole_library.loc[:,'flags'] = 'NONE'
	if include_mount : 
		

		equipment_name = {}

		for pole in pole_name : 
			if [p for p in overheadline_names if pole[5:] in p] : 
				# equipment_name_raw.append([p for p in overheadline_names if pole[5:] in p])
				# matching_lines = 
				equipment_name[pole] = [p for p in overheadline_names if pole[5:] in p]
				# equipment_name_raw = {pole[5:]: p for p in overheadline_names if pole[5:] in p}
				# equipment_name = [item for sublist in equipment_name_raw for item in sublist]
		
		# Create an empty list to hold the formatted data
		formatted_equipment = []

		# Iterate through the dictionary items and format them
		for pole, lines in equipment_name.items():
		    for line in lines:
		        formatted_equipment.append([pole, line])

		# Create a DataFrame from the formatted data
		df_pole_mount = pd.DataFrame(formatted_equipment, columns=['parent', 'equipment'])
		df_pole_mount.loc[:,'class'] = 'pole_mount'
		df_pole_mount.loc[:,'name'] = 'pole_mount_'+df_pole_mount['equipment']

		poles_with_parents_named = set([p for p in pole_name if any(p[5:] in l for l in overheadline_names)])
		
		# Filtering poles to the ones that found in overheadline names
		df_pole_library_filtered= df_pole_library[df_pole_library['name'].isin(poles_with_parents_named)]

	if include_mount : 
		df= pd.concat([df_pole_config, df_pole_library_filtered, df_pole_mount], axis=0, ignore_index=True)	
	else : 
		df= pd.concat([df_pole_config, df_pole_library], axis=0, ignore_index=True)	

	# Drop rows with duplicate entries under the 'ID' column
	df = df.drop_duplicates(subset=['name'])
	# Secondly do operations on the sheet 'Design - Structure'
	if extract_equipment:
		file_extension = input_equipment_file.split(".")[-1]
		if file_extension == 'xlsx':
			df_structure_raw = pd.read_excel(input_equipment_file, sheet_name=0, usecols=['ID', 'Structure_x0020_ID', 'AS-IS_x0020_Size', 'AtHeight_x0020_Unit', 'AtHeight_x0020_Value', 'Usage_x0020_Group', 'AS-IS_x0020_Height', 'AS-IS_x0020_Direction',
       'AS-IS_x0020_Offset_x002F_Lead'], engine='openpyxl')
		elif file_extension == 'xls':
			df_structure_raw = pd.read_excel(input_equipment_file, sheet_name=0, usecols=['ID', 'Structure_x0020_ID', 'AS-IS_x0020_Size', 'AtHeight_x0020_Unit', 'AtHeight_x0020_Value', 'Usage_x0020_Group', 'AS-IS_x0020_Height', 'AS-IS_x0020_Direction',
       'AS-IS_x0020_Offset_x002F_Lead'])
		elif file_extension == 'csv':
		    df_structure_raw = pd.read_csv(input_equipment_file, usecols=['ID', 'Structure_x0020_ID', 'AS-IS_x0020_Size', 'AtHeight_x0020_Unit', 'AtHeight_x0020_Value', 'Usage_x0020_Group', 'AS-IS_x0020_Height', 'AS-IS_x0020_Direction',
       'AS-IS_x0020_Offset_x002F_Lead'], engine='openpyxl')

		# new_header_index = df_structure.iloc[:, 0].first_valid_index()
		# new_header = df_structure.iloc[new_header_index+1]
		# df_structure = df_structure[new_header_index:]
		# df_structure.columns = new_header
		# df_structure.index = range(len(df_structure.index))
		# df_structure.columns.name = None
		# pos_index = []
		# pole_index = 0
		# for i in range(len(df_structure["ID#"])):
		# 	if df_current_sheet.iloc[i]["ID#"] == pole_name[pole_index].split('_')[1]:
		# 		pos_index.append(i)
		# 		if pole_index == len(pole_name)-1:
		# 			break
		# 		else:
		# 			pole_index += 1
		# pos_index = sorted(pos_index)
		# pole_index = 0
		# mount_wire_dic = {}
		# mount_equip_dic = {}
		# mount_wep_dic = {}
		# for i in range(len(pos_index)-1):
		# 	for k in range(pos_index[i]+2,pos_index[i+1]-1):
		# 		mount_ID = df_current_sheet.iloc[k]["ID#"]
		# 		if "Wire" in mount_ID:
		# 			mount_height = parse_length(df_current_sheet.iloc[k]["Height"], "Height", f"{k}")
		# 			mount_direction = parse_angle(df_current_sheet.iloc[k]["Direction"], "Direction", f"{k}")
		# 			mount_wire_dic[f"OL_{mount_ID}_{pole_name[pole_index]}"] = {
		# 				"equipment" : f"OL_{mount_ID}_{pole_name[pole_index]}",
		# 				"class" : "pole_mount",
		# 				"parent" : pole_name[pole_index],
		# 				"height" : mount_height,
		# 				"direction" : mount_direction,
		# 				"pole_spacing" : f'WEP_{df_current_sheet.iloc[k]["Related"]}_{pole_name[pole_index]}',
		# 				"// cable_type" : df_current_sheet.iloc[k]["Size"],
		# 				"flags" : "NONE",
						
		# 			}
		# 		elif "Equip" in mount_ID:
		# 			mount_height = parse_length(df_current_sheet.iloc[k]["Height"], "Height", f"{k}")
		# 			mount_direction = parse_angle(df_current_sheet.iloc[k]["Direction"], "Direction", f"{k}")
		# 			mount_equip_dic[f"TF_{mount_ID}_{pole_name[pole_index]}"] = {
		# 				"equipment" : f"TF_{mount_ID}_{pole_name[pole_index]}",
		# 				"class" : "pole_mount",
		# 				"parent" : pole_name[pole_index],
		# 				"height" : mount_height,
		# 				"direction" : mount_direction,
		# 				"offset" : "1 ft",
		# 				"area" : "1 sf",
		# 				"weight" : "10 lb",
		# 				"// equipment_type" : df_current_sheet.iloc[k]["Size"],
		# 				"flags" : "NONE",
						
		# 			}
		# 		elif "WEP" in mount_ID:
		# 			mount_direction = parse_angle(df_current_sheet.iloc[k]["Direction"], "Direction", f"{k}")
		# 			mount_offset = parse_length(df_current_sheet.iloc[k]["Offset/Lead"], "Offset/Lead", f"{k}")
		# 			mount_wep_dic[f"WEP_{mount_ID}_{pole_name[pole_index]}"] = {
		# 				"name" : f"WEP_{mount_ID}_{pole_name[pole_index]}",
		# 				"direction" : mount_direction,
		# 				"distance" : mount_offset,
		# 			}
		# 	pole_index += 1
		# for k in range(pos_index[-1]+2,len(df_current_sheet["ID#"])):
		# 	mount_ID = df_current_sheet.iloc[k]["ID#"]
		# 	if "Wire" in mount_ID:
		# 		mount_height = parse_length(df_current_sheet.iloc[k]["Height"], "Height", f"{k}")
		# 		mount_direction = parse_angle(df_current_sheet.iloc[k]["Direction"], "Direction", f"{k}")
		# 		mount_wire_dic[f"OL_{mount_ID}_{pole_name[pole_index]}"] = {
		# 			"equipment" : f"OL_{mount_ID}_{pole_name[pole_index]}",
		# 			"class" : "pole_mount",
		# 			"parent" : pole_name[pole_index],
		# 			"height" : mount_height,
		# 			"direction" : mount_direction,
		# 			"pole_spacing" : f'WEP_{df_current_sheet.iloc[k]["Related"]}_{pole_name[pole_index]}',
		# 			"// cable_type" : df_current_sheet.iloc[k]["Size"],
		# 			"flags" : "NONE",
		# 		}
		# 	elif "Equip" in mount_ID:
		# 		mount_height = parse_length(df_current_sheet.iloc[k]["Height"], "Height", f"{k}")
		# 		mount_direction = parse_angle(df_current_sheet.iloc[k]["Direction"], "Direction", f"{k}")
		# 		mount_equip_dic[f"TF_{mount_ID}_{pole_name[pole_index]}"] = {
		# 			"equipment" : f"TF_{mount_ID}_{pole_name[pole_index]}",
		# 			"class" : "pole_mount",
		# 			"parent" : pole_name[pole_index],
		# 			"height" : mount_height,
		# 			"direction" : mount_direction,
		# 			"offset" : "1 ft",
		# 			"area" : "1 sf",
		# 			"weight" : "10 lb",
		# 			"// equipment_type" : df_current_sheet.iloc[k]["Size"],
		# 			"flags" : "NONE",
		# 		}
		# 	elif "WEP" in mount_ID:
		# 		mount_direction = parse_angle(df_current_sheet.iloc[k]["Direction"], "Direction", f"{k}")
		# 		mount_offset = parse_length(df_current_sheet.iloc[k]["Offset/Lead"], "Offset/Lead", f"{k}")
		# 		mount_wep_dic[f"WEP_{mount_ID}_{pole_name[pole_index]}"] = {
		# 			"name" : f"WEP_{mount_ID}_{pole_name[pole_index]}",
		# 			"direction" : mount_direction,
		# 			"distance" : mount_offset,
		# 		}
		# for key in mount_wire_dic.keys():
		# 	mount_wire_dic[key]["pole_spacing"] = mount_wep_dic[mount_wire_dic[key]["pole_spacing"]]["distance"]
		# df_mount_wire = pd.DataFrame.from_dict(mount_wire_dic, orient='index')
		# df_mount_equip = pd.DataFrame.from_dict(mount_equip_dic, orient='index')
		# df['Design - Structure']= pd.concat([df_mount_wire, df_mount_equip], axis=0, ignore_index=True)
		# df['Design - Pole']= pd.concat([df['Design - Pole'], df['Design - Structure']], axis=0, ignore_index=True)
		
	if include_dummy_network:
		df = xls2glm_object(df,input_pole_file)

	# Keep track of final df to output at the end. 
	df_final = df.copy()

	# Move class column to the first column. May not be necessary. 
	class_column = df_final.pop('class')
	df_final.insert(0, 'class', class_column)

	# Create the intermediate csv files. May not be necessary. 

	df_final.reset_index(drop=True, inplace=True)

	# Create final csv file. 
	df_final.to_csv(output_file, index=False)

def parse_angle(cell_string, current_column, current_row):
	"""Parse a string to get a string with angle in a unit that is supported by Gridlabd

	Additional acceptable units can be added to angle_units. Invalid inputs raise a ValueError. 

	Keyword arguments:
	cell_string -- the string to be parsed (presumably from a cell)
	current_column -- the column of the cell it is parsing. For more descriptive ValueErrors
	current_row -- the row of the cell it is parsing. For more descriptive ValueErrors
	"""
	angle_units = {	
	"°" : "deg",
	"deg" : "deg",
	"rad" : "rad",
	"grad" : "grad",
	"quad" : "quad",
	"sr" : "sr"
	}
	value = re.search("\d+[\.]?[\d+]*", cell_string)
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	output_unit = ""
	for unit in angle_units.keys():
		if unit in cell_string:
			output_unit = angle_units[unit]
			break
	if output_unit == "": 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')
	elif value == None: 
		raise ValueError(f'Please specify valid value for {cell_string} in column: {current_column}, row {current_row}.')
	else:
		return value.group() + " " + output_unit
	

def parse_length(cell_string_raw, current_column, current_row):
	"""Parse a string to get a string with length in a unit that is supported by Gridlabd

	Additional acceptable units can be added to length_units and length_conversion with its corresponding conversion value to degrees. 
	Supports multiple units in one string. Invalid inputs raise a ValueError. 

	Keyword arguments:
	cell_string -- the string to be parsed (presumably from a cell)
	current_column -- the column of the cell it is parsing. For more descriptive ValueErrors
	current_row -- the row of the cell it is parsing. For more descriptive ValueErrors
	"""
	cell_string=cell_string_raw.lower()

	INCH_TO_FEET = 0.0833
	UNIT_TO_UNIT = 1.0 
	YARD_TO_FEET = 3.0
	MILE_TO_FT = 5280.0 
	FEET_TO_INCH = 12.0
	YARD_TO_INCH = 36.0
	MILE_TO_INCH = 6360.0
	MILE_TO_YARD = 1760.0
	# Handle values and units in different orders.
	length_units = {
	"'" : "ft",
	'"' : "in",
	"in" : "in",
	"inch" : "in",
	"inches" :'in',
	"feet" : "ft",
	"ft" : "ft",
	"foot" : "ft",
	"yd" : "yd",
	"yard" : "yd",
	"mile" : "mile",
	"mi" : "mile"
	}
	# Map to a dictionary of conversion rates of different units to the key of length_conversions.
	length_conversions = {	
	"ft" : {"in" : INCH_TO_FEET, "ft" :  UNIT_TO_UNIT, "yd" : YARD_TO_FEET, "mile" : MILE_TO_FT},
	"in" : {"in" : UNIT_TO_UNIT,"ft": FEET_TO_INCH,  "yd": YARD_TO_INCH, "mile" : MILE_TO_INCH},
	"yd" : {"in": 1/YARD_TO_INCH, "ft": 1/YARD_TO_FEET, "yd": UNIT_TO_UNIT, "mile" : MILE_TO_YARD},
	"mile" : {"in": 1/MILE_TO_INCH, "ft": 1/MILE_TO_FT, "yd": 1/MILE_TO_YARD, "mile" : UNIT_TO_UNIT}
	}

	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')

	# Keeps track of the units that are in the cell. Whichever unit is listed first in length_units AND is present in the string is the unit that will be used as the output.
	cell_units = []
	units_positions = []
	num_strings = []
	for key in length_units.keys():
		if key in cell_string:
			cell_units.append(length_units[key])
			units_positions.append(cell_string.find(key))
	last_pos = 0
	for units_position in units_positions:
		num_strings.append(cell_string[last_pos:units_position])
		last_pos = units_position+1

	if len(cell_units) == 0: 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')

	if len(num_strings) != len(cell_units):
		raise ValueError(f'Please make sure there are the same number of numbers and units for value {cell_string} in column: {current_column}, row {current_row}')

	cell_numbers = re.findall('\d+[\./]?[\d+]*', cell_string)

	# Convert all the units and values in the cell to one unit and value.
	total_cell_value = 0
	convert_to = length_conversions[cell_units[0]]
	for i in range(len(num_strings)):
		num_unit_strings = re.findall('\d+[\./]?[\d+]*', num_strings[i])
		total_num_value = 0
		for num_unit_string in num_unit_strings:
			if "/" in num_unit_string:
				total_num_value += float(num_unit_string.split('/')[0])/float(num_unit_string.split('/')[1])
			else:
				total_num_value += float(num_unit_string)
		total_cell_value += total_num_value * convert_to[cell_units[i]]
	return str(round(total_cell_value,precision)) + " " + cell_units[0]

def parse_pressure(cell_string, current_column, current_row):
	"""Parse a string to get a string with pressure in a unit that is supported by Gridlabd

	Additional acceptable units can be added to pressure_units. Invalid inputs raise a ValueError. 

	Keyword arguments:
	cell_string -- the string to be parsed (presumably from a cell)
	current_column -- the column of the cell it is parsing. For more descriptive ValueErrors
	current_row -- the row of the cell it is parsing. For more descriptive ValueErrors
	"""
	pressure_units = {
	"psi" : "psi",
	"lb/in²" : "psi",
	"bar" : "bar",
	"atm" : "atm", 
	}
	value = re.search("\d+[\.]?[\d+]*", cell_string)
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	output_unit = ""
	for unit in pressure_units.keys():
		if unit in cell_string:
			cell_string = cell_string.replace(unit,pressure_units[unit])
			output_unit = pressure_units[unit]
		else : # ASSUME no unit given
			output_unit="psi"

	if output_unit == "": 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')
	elif value == None: 
		raise ValueError(f'Please specify valid value for {cell_string} in column: {current_column}, row {current_row}.')
	else:
		return  value.group() + " " + output_unit
	
def parse_column(df_current_sheet, current_column, parsing_function):
	"""Parse each cell in the column with a function 
	For invalid inputs, resulting cell will be ''.
	Allows empty cells ('nan'). Can remove the if statement if an error should be raised for empty cells. 
	Keyword arguments:
	current_column -- the string to be parsed (presumably from a cell)
	parsing_function -- the function to be called for each cell
	"""
	for row in range(len(df_current_sheet[current_column])):
		current_string = str(df_current_sheet.at[row,current_column]).lower()
		if (current_string == 'nan'):
			df_current_sheet.at[row,current_column] = ''
		else:
			try: 
				df_current_sheet.at[row,current_column] = parsing_function(str(df_current_sheet.at[row,current_column]),current_column,row)
			except ValueError as e: 
				df_current_sheet.at[row,current_column] = ''		

def subtract_length_columns(minuend_string, subtrahend_string, minuend_column, subtrahend_column,current_row):
	"""Subtract the lengths of strings contained in two cells 
	
	Assumes the units are the same for the two columns. 

	Keyword arguments:
	minuend_string -- the string containing the minuend 
	subtrahend_string -- the string containing the subtrahend 
	minuend_column -- the name of the column containing the minuend cell. For more descriptive ValueErrors
	subtrahend_column -- the name of the column containing the subtrahend cell. For more descriptive ValueErrors
	current_row -- the row number containing the minuend cell. For more descriptive ValueErrors
	"""
	length_units = {	
	"'" : "ft",
	'"' : "in",
	"in" : "in",
	"inch" : "in",
	"feet" : "ft",
	"ft" : "ft",
	"foot" : "ft",
	"yd" : "yd",
	"yard" : "yd",
	"mile" : "mile",
	"mi" : "mile"
	}
	if minuend_string == "nan":
		raise ValueError(f'The cell column: {minuend_column}, row {current_row} is empty. Please enter a value.')
	elif subtrahend_string == "nan": 
		raise ValueError(f'The cell column: {subtrahend_column}, row {current_row} is empty. Please enter a value.')
	output_unit = ""
	for unit in length_units.keys():
		if unit in minuend_string and unit in subtrahend_string:
			output_unit = length_units[unit]
			break
	if output_unit == "": 
		raise ValueError(f'Please provide {minuend_column} and {subtrahend_column}, row {current_row} with the same units.')
	else:
		return str(round(float(re.search("^[1-9]\d*(\.\d+)?", minuend_string).group()) - float(re.search("^[1-9]\d*(\.\d+)?", subtrahend_string).group()),precision)) + " " + output_unit


def check_lat_long(cell_string, current_column, current_row):
	"""Parse the lat/long value
	
	Keyword arguments:
	cell_string -- the string to be parsed (presumably from a cell)
	current_column -- the column number containing the cell_string. For more descriptive ValueErrors
	current_row -- the row number containing the cell_string. For more descriptive ValueErrors
	"""
	CONTIGUOUS_US_LOWER_LAT = 23
	CONTIGUOUS_US_UPPER_LAT = 50
	CONTIGUOUS_US_LOWER_LONG = -130
	CONTIGUOUS_US_UPPER_LONG = -64
	ALASKA_LOWER_LAT = 55
	ALASKA_UPPER_LAT = 71
	ALASKA_LOWER_LONG = -168
	ALASKA_UPPER_LONG = -130
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	else:
		lat_long = re.findall('[\-]?\d+[\.]?[\d+]*', cell_string)
		if (len(lat_long) != 2):
			raise ValueError(f'The cell value {cell_string} in {current_column}, row {current_row} is not valid. Please provide GPS Point in this format: lat , long')	
		try: 
			lat = float(lat_long[0])
			longitude = float(lat_long[1])
		except ValueError: 
			raise ValueError(f'The cell value {cell_string} in {current_column}, row {current_row} is not valid. Please provide GPS Point in this format: float , float')
		if ((lat < CONTIGUOUS_US_UPPER_LAT and longitude > CONTIGUOUS_US_LOWER_LONG) and (lat > CONTIGUOUS_US_LOWER_LAT and longitude < CONTIGUOUS_US_UPPER_LONG) or 
		((lat > ALASKA_LOWER_LAT and  longitude < ALASKA_UPPER_LONG ) and (lat < ALASKA_UPPER_LAT and longitude > ALASKA_LOWER_LONG))):
			return str(lat) + ","  + str(longitude)
		else:
			raise ValueError(f'The cell value {cell_string} in {current_column}, row {current_row} is not in North America. Please enter a valid value.')
		 

def parse_circumference_to_diamater(cell_string, current_column, current_row):
	"""Parse the circumference value into its diameter value 

	Keyword arguments:
	cell_string --  the string to be parsed (presumably from a cell)
	current_column -- the column number containing the cell_string. For more descriptive ValueErrors
	current_row -- the row number containing the cell_string. For more descriptive ValueErrors
	"""
	try: 
		string_value = parse_length(cell_string, current_column, current_row).split(" ")
		return str(round(float(string_value[0])/math.pi, precision)) + " " + string_value[1]
	except ValueError as e: 
		raise e

def parse_space_to_underscore(cell_string, current_column, current_row):
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	return cell_string.replace(' ','_')

def xls2glm_object(df_glm, input_file):
	glm_node_dic = {}
	glm_OLLC_dic = {}
	glm_LS_dic = {}
	glm_LC_dic = {}
	glm_OL_dic = {}
	glm_TC_dic = {}
	glm_TF_dic = {}

	swing_node = f"ND_{re.sub(r'[^a-zA-Z]', '_', os.path.basename(input_file).split('.')[0])}"
	df_glm["parent"]=swing_node
	glm_node_dic[swing_node] = {
		"name" : swing_node,
		"class" : "node",
		"phases" : "A",
		"bustype" : "SWING",
		"nominal_voltage" : "2401 V",
	}
	last_node = swing_node
	# for n in range(len(df_glm["class"])):
	# 	if df_glm.iloc[n]["class"] == "pole_mount":
	# 		if df_glm.iloc[n]["equipment"].split('_')[0] == "OL":
	# 			if f'ND_{df_glm.iloc[n]["equipment"]}' not in glm_node_dic.keys():
	# 				glm_node_dic[f'ND_{df_glm.iloc[n]["equipment"]}'] = {
	# 					"name" : f"ND_{df_glm.iloc[n]['equipment']}",
	# 					"class" : "node",
	# 					"phases" : "A",
	# 					"nominal_voltage" : "2401 V",
	# 				}
				
	# 			name_overhead_line_conductor = f'OC_{string_clean(df_glm.iloc[n]["// cable_type"])}'
	# 			if name_overhead_line_conductor not in glm_OLLC_dic.keys():
	# 				glm_OLLC_dic[name_overhead_line_conductor] = {
	# 					"name" : name_overhead_line_conductor,
	# 					"class" : "overhead_line_conductor",
	# 					"diameter" : "0.1 in",
	# 					"resistance" : "0.1 Ohm/mile",
	# 					"weight" : "0.1 lb/ft",
	# 					"strength" : "100 lb",
	# 				}
				
	# 			name_line_spacing = f'LS_{string_clean(df_glm.iloc[n]["height"])}'
	# 			if name_line_spacing not in glm_LS_dic.keys():
	# 				glm_LS_dic[name_line_spacing] = {
	# 					"name" : name_line_spacing,
	# 					"class" : "line_spacing",
	# 					"distance_AE" : df_glm.iloc[n]["height"],
	# 				}
				
	# 			name_line_configuration = f'LC_{df_glm.iloc[n]["equipment"]}'
	# 			if name_line_configuration not in glm_LC_dic.keys():
	# 				glm_LC_dic[name_line_configuration] = {
	# 					"name" : name_line_configuration,
	# 					"class" : "line_configuration",
	# 					"conductor_A" : name_overhead_line_conductor,
	# 					"spacing" : name_line_spacing,
	# 				}
				
	# 			name_overhead_line = f'{df_glm.iloc[n]["equipment"]}'
	# 			if name_overhead_line not in glm_OL_dic.keys():
	# 				glm_OL_dic[name_overhead_line] = {
	# 					"name" : name_overhead_line,
	# 					"class" : "overhead_line",
	# 					"phases" : "A",
	# 					"from" : last_node,
	# 					"to" : f'ND_{df_glm.iloc[n]["equipment"]}',
	# 					"length" : df_glm.iloc[n]["pole_spacing"],
	# 					"configuration" : name_line_configuration
	# 				}
	# 			last_node = f'ND_{df_glm.iloc[n]["equipment"]}'
	# 		elif df_glm.iloc[n]["equipment"].split('_')[0] == "TF":
	# 			if f'ND_{df_glm.iloc[n]["equipment"]}' not in glm_node_dic.keys():
	# 				glm_node_dic[f'ND_{df_glm.iloc[n]["equipment"]}'] = {
	# 					"name" : f"ND_{df_glm.iloc[n]['equipment']}",
	# 					"class" : "node",
	# 					"phases" : "A",
	# 					"nominal_voltage" : "2401 V",
	# 				}
				
	# 			name_transformer_configuration = f'TC_{df_glm.iloc[n]["equipment"]}'
	# 			if name_transformer_configuration not in glm_TC_dic.keys():
	# 				glm_TC_dic[name_transformer_configuration] = {
	# 					"name" : name_transformer_configuration,
	# 					"class" : "transformer_configuration",
	# 					"connect_type" : "WYE_WYE",
	# 					"install_type" : "PADMOUNT",
	# 					"power_rating" : "100 kVA",
	# 					"primary_voltage" : "2401 V",
	# 					"secondary_voltage" : "2401 V",
	# 					"resistance" : "0.000333",
	# 					"reactance" : "0.00222",
	# 				}
	# 			name_transformer = f'{df_glm.iloc[n]["equipment"]}'
	# 			if name_transformer not in glm_TF_dic.keys():
	# 				glm_TF_dic[name_transformer] = {
	# 					"name" : name_transformer,
	# 					"class" : "transformer",
	# 					"phases" : "AN",
	# 					"from" : last_node,
	# 					"to" : f'ND_{df_glm.iloc[n]["equipment"]}',
	# 					"configuration" : name_transformer_configuration,
	# 				}
	# 			last_node = f'ND_{df_glm.iloc[n]["equipment"]}'
	# 		else:
	# 			raise Exception(f"cannot convert equipment")
	df_glm_node = pd.DataFrame.from_dict(glm_node_dic, orient='index')
	df_glm_OLLC = pd.DataFrame.from_dict(glm_OLLC_dic, orient='index')
	df_glm_LS = pd.DataFrame.from_dict(glm_LS_dic, orient='index')
	df_glm_LC = pd.DataFrame.from_dict(glm_LC_dic, orient='index')
	df_glm_OL = pd.DataFrame.from_dict(glm_OL_dic, orient='index')
	df_glm_TC = pd.DataFrame.from_dict(glm_TC_dic, orient='index')
	df_glm_TF = pd.DataFrame.from_dict(glm_TF_dic, orient='index')
	
	df_glm_network= pd.concat([df_glm_node, df_glm_OLLC, df_glm_LS, df_glm_LC, df_glm_OL, df_glm_TC, df_glm_TF], axis=0, ignore_index=True)
	df_glm= pd.concat([df_glm, df_glm_network], axis=0, ignore_index=True)

	return df_glm.copy()
