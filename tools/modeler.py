"""GridLAB-D JSON file accessor

"""

import os, sys
import json
import re
import io
import gridlabd.runner as runner
import pandas as pd
from typing import Any

VERSION = "4.3.1" # oldest version supported by this module
ENCODING = "utf-8" # data encoding to use for JSON files

class GridlabdModelException(Exception):
    """GridLAB-D modeler exception handler"""

class GridlabdModel:
    """GridLAB-D modeler class implementation"""
    def __init__(self,
                 data:str = None,
                 name:str = None,
                 force:bool = False,
                 initialize:bool = False,
                 ):
        """Create a gridlabd model object

        Arguments:

        * `data`: GLM filename, JSON data, or JSON filename

        * `name`: filename to use (overrides default filename)

        * `force`: force overwrite of existing JSON

        * `initialize`: initialize GLM first
        """

        if name:
            self.filename = name

        if data is None: # new file
            if not name:
                self.autoname(force)
            runner.gridlabd("-o",self.filename)
            self.read_json(self.filename)

        elif type(data) is str and os.path.splitext(data)[1] == ".glm": # glm file

            self.read_glm(data,force=force,initialize=initialize)

        elif type(data) is str and os.path.splitext(data)[1] == ".json": # json file

            self.read_json(data)

        else: # raw data

            if not name:
                self.autoname(force)
            self.load(data)

    def autoname(self,force:bool=False) -> str:
        """Generate a new filename

        Arguments:
        
        * `force`: use the first name generate regardless of whether the file
          exists

        Returns:

        * `str`: new filename
        """
        num = 0
        def _name(num):
            return f"untitled-{num}.json"
        while os.path.exists(_name(num)) and not force:
            num += 1
        self.filename = _name(num)
        return self.filename

    def read_glm(self,filename:str,force:bool=True,initialize:bool=False):
        """Read GLM file
    
        Arguments:
        
        * `filename`: name of GLM file to read

        * `force`: force overwrite of JSON

        * `initialize`: initialize GLM first
        """
        with open(filename,"r") as fh:
            self.filename = filename
            self.load(fh.read())

    def read_json(self,filename:str):
        """Read JSON file

        Arguments:
        
        * `filename`: name of JSON file to read
        """
        with open(filename,"r") as fh:
            data = json.load(fh)
            self.filename = filename
            self.load(data)

    def load(self,data):
        """Load data from dictionary

        Arguments:
        
        * `data`: data to load (must be a valid GLM model)
        """
        if type(data) is bytes:
            data = data.decode(ENCODING)
        if type(data) is str:
            if data[0] in ["[","{"]:
                data = json.loads(data)
            else:
                data = json.loads(runner.gridlabd("-C",".glm","-o","-json",source=data,binary=True))
        if not type(data) is dict:
            raise GridlabdModelException("data is not a dictionary")
        if data["application"] != "gridlabd":
            raise GridlabdModelException("data is not a gridlabd model")
        if data["version"] < VERSION:
            raise GridlabdModelException("data is from an outdated version of gridlabd")
        for key,values in data.items():
            setattr(self,key,values)
        self.is_modified = False

    def get_objects(self,classes=None,as_type:Any=dict,**kwargs) -> Any:
        """Find objects belonging to specified classes

        Arguments:
        
        * `classes`: patterns of class names to search (default is '.*')
        
        * `as_type`: type to use for return value
        
        * `**kwargs`: arguments for as_type

        Return:
        
        * `as_type`: object data
        """
        if type(classes) is str:
            match = classes.split(",")
        else:
            match = []
            for y in classes if classes else '.*':
                regex = re.compile(y)
                match.extend([x for x in self.classes if regex.match(x)])
        data = dict([(obj,data) for obj,data in self.objects.items() if data["class"] in match])
        return as_type(data,**kwargs)

    def rename(self,name):
        self.filename = name
        self.is_modified = True

if __name__ == "__main__":

    if not sys.argv[0]:
        import unittest

        class TestModel(unittest.TestCase):

            def test_glm_get_objects_pattern(self):
                runner.gridlabd("model","get","IEEE/13","-o=/tmp/13.glm")
                glm = GridlabdModel("/tmp/13.glm",force=True)
                loads = glm.get_objects(classes=[".*load"])
                self.assertEqual(len(loads),10)

            def test_json_get_objects_list(self):
                runner.gridlabd("model","get","IEEE/13","-o=/tmp/13.json")
                glm = GridlabdModel("/tmp/13.json")
                loads = glm.get_objects(classes=["load","triplex_load"])
                self.assertEqual(len(loads),10)

            def test_new_members(self):
                glm = GridlabdModel(force=True)
                self.assertEqual(glm.objects,{})
                self.assertEqual(glm.classes,{})

        unittest.main()

    else:

        print(f"ERROR [modeler]: cannot be run from command line",file=sys.stderr)
        exit(1)
