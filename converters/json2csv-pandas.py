"""Convert JSON to CSV

SYNTAX
------

    gridlabd -C input.glm -D csv_save_options="-t pandas -f PROPERTY=VALUE ..." -o output.csv

DESCRIPTION
-----------

The filter option can be used to limit the output to object with matching properties, e.g.,

	-f class=CLASS

or

	-f class="CLASS1|CLASS2".

Multiple filters may be specified in which case, all objects will match all
filters, with an "and" operation, r.h.,

	-f class=CLASS name=NAME

Filter values are interpreted using regular expressions, e.g.,

	-f name=EXPRESSION

Be careful to quote expressions that can be interpreted by the shell.

EXAMPLE
-------

The following command downloads the IEEE 13-bus model and saves all the PQ bus nodes and loads:

	gridlabd model get IEEE/13
	gridlabd -C 13.glm -D csv_save_options='-t pandas -f class="node|load" -f bustype=PQ' -o 13.csv
"""
import json 
import os 
import sys, getopt
from datetime import datetime 
import csv
import io
import pandas as pd
import re

def convert(input_file,output_file=None, options={}):

	if output_file == '':
		if input_file[-5:] == ".json":
			output_file = input_file[:-5] + ".csv" 
		else: 
			output_file = input_file + ".csv"

	with open(input_file,"r") as f :
		data = json.load(f)
		assert(data['application']=='gridlabd')
		assert(data['version'] >= '4.2.0')

	if "filter" in options and len(options["filter"]) > 0:
		result = {}
		for name,properties in data["objects"].items():
			ok = 0
			for key,value in options["filter"].items():
				if key == "name" and re.match(value,name):
					ok += 1
				elif key in properties and re.match(value,properties[key]):
					ok += 1
			if ok == len(options["filter"]):
				result[name] = properties
	else:
		result = data["objects"]
	df = pd.DataFrame(result).transpose()
	df.to_csv(output_file,header=True,index=False)	
