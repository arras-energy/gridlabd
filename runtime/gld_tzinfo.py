"""Timezone information"""

import os
import sys
from datetime import timedelta
import zoneinfo
import warnings

with open(os.path.join(os.environ["GLD_ETC"],"tzinfo.txt"),"r") as fh:
	TZINFO = [x.split(";")[0].rstrip() for x in fh.read().split("\n") if not x.strip().startswith(";")]
	print(TZINFO)

class GridlabdZoneInfo(zoneinfo.ZoneInfo):

	def __init__(self,tz):

		try:
			super().__init__(tz)
		except zoneinfo._common.ZoneInfoNotFoundError:
			warnings.warn(f"use of {tz=} is deprecated, please use a supported Python timezone")
			self.info = ["UTC",0.0,None]

	def tzname(self,dt):
		return self.info[0]

	def tzoffset(self,dt):
		return timedelta(hours=self.info[1])


if __name__ == '__main__':
	
	tz = GridlabdZoneInfo("PST+8PDT")
	print(tz.tzname(None),tz.tzoffset(None))