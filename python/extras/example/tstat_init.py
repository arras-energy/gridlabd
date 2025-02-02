#!/anaconda/bin/python
import os
import gldcore
import random

gldcore.set('show_progress','FALSE')
#
# Get a list of houses
#
houses = gldcore.find('class=house')
houselist = [];
# 
# This command is required to disable the internal house thermostat
#
for house in houses :
	name = house['name']
	gldcore.set(name,'thermostat_control','NONE')
	houselist.append(name) 
	
gldcore.set('houselist',';'.join(houselist))
