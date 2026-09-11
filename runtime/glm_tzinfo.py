"""Timezone information"""

import os
import sys
from datetime import datetime, timedelta
import zoneinfo
import warnings

TZINFO = None

class GridlabdZoneInfo(zoneinfo.ZoneInfo):
	"""Abstract base class for GridLAB-D timezone info objects"""
	def __init__(self,tz):
		"""Create a timezone info object"""

		# load the gridlabd tzinfo.txt file
		global TZINFO
		if TZINFO is None:
			with open(os.path.join(os.environ["GLD_ETC"],"tzinfo.txt"),"r") as fh:
				TZINFO = [x.split(";")[0].rstrip() for x in fh.read().split("\n") if not x.strip().startswith(";")]

		# construct the zoneinfo object
		super().__init__(tz)
		# try:
		# 	super().__init__(tz)
		# except zoneinfo._common.ZoneInfoNotFoundError:
		# 	warnings.warn(f"use of {tz=} is deprecated, please use a supported Python timezone")
		# 	self.info = ["UTC",0.0,None]

	def tzname(self,dt:datetime) -> str:
		"""Retrieve the string containing the abbreviation for the time zone
		that applies in a zone at a given datetime.

		Arguments
		---------
		- `dt`: datetime at which to evaluate the timezone offset

		Returns
		-------
		- `timedelta`: the time offset
		"""
		return self.info[0]

	def tzoffset(self,dt) -> timedelta:
		"""Retrieve the time offset that applies in a zone at a given datetime

		Arguments
		---------
		- `dt`: datetime at which to evaluate the timezone offset

		Returns
		-------
		- `timedelta`: the time offset
		"""
		return timedelta(hours=self.info[1])
