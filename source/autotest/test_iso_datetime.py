import json 
from datetime import datetime

with open('test_iso_datetime.json') as json_file:
	data = json.load(json_file)
	assert str(datetime.fromisoformat(data["globals"]["starttime"]["value"])) == "2000-01-01 00:00:00-05:00"
	assert str(datetime.fromisoformat(data["globals"]["stoptime"]["value"])) == "2000-01-02 02:00:00-05:00"
