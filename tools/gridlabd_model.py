"""GridLAB-D JSON file accessor

"""

import os, sys
import json
import re
import io
from gridlabd.gridlabd_runner import gridlabd
import pandas as pd

VERSION = "4.3.1" # oldest version supported by this module
ENCODING = "utf-8" # data encode to use for JSON files

class GridlabdModelException(Exception):
    pass

class GridlabdModel:

    def __init__(self,
                 data = None, # GLM filename, JSON data, or JSON filename
                 name = None, # filename to use (overrides default filename)
                 force = False, # force overwrite of existing JSON
                 initialize = False, # initialize GLM first
                 ):

        if name:
            self.filename = name

        if data is None: # new file
            if not name:
                self.autoname(force)
            gridlabd("-o",self.filename)
            self.read_json(self.filename)

        elif type(data) is str and os.path.splitext(data)[1] == ".glm": # glm file

            self.read_glm(data,force=force,initialize=initialize)

        elif type(data) is str and os.path.splitext(data)[1] == ".json": # json file

            self.read_json(data)

        else: # raw data

            if not name:
                self.autoname(force)
            self.load(data)

    def autoname(self,force=False):
        """Generate a new filename

        Arguments:
        - force (bool): use the first name generate regardless of whether the file exists
        """
        num = 0
        def _name(num):
            return f"untitled-{num}.json"
        while os.path.exists(_name(num)) and not force:
            num += 1
        self.filename = _name(num)

    def read_glm(self,filename,force=True,initialize=False):
        """Read GLM file
    
        Arguments:
        - filename (str): name of GLM file to read
        - force (bool): force overwrite of JSON
        - initialize (bool): initialize GLM first
        """
        with open(filename,"r") as fh:
            self.filename = filename
            self.load(data)

    def read_json(self,filename):
        """Read JSON file

        Arguments:
        - filename (str): name of JSON file to read
        """
        with open(filename,"r") as fh:
            data = json.load(fh)
            self.filename = filename
            self.load(data)

    def load(self,data):
        """Load data from dictionary

        Arguments:
        - data (dict|str|bytes): data to load (must be a valid GLM model)
        """
        if type(data) is bytes:
            data = data.decode(ENCODING)
        if type(data) is str:
            if data[0] in ["[","{"]:
                data = json.loads(data)
            else:
                data = json.loads(gridlabd("-C",".glm","-o","-json",binary=True,source=io.StringIO(data)))
                print(data)
        if not type(data) is dict:
            raise GridlabdModelException("data is not a dictionary")
        if data["application"] != "gridlabd":
            raise GridlabdModelException("data is not a gridlabd model")
        if data["version"] < VERSION:
            raise GridlabdModelException("data is from an outdated version of gridlabd")
        for key,values in data.items():
            setattr(self,key,values)
        self.is_modified = False

    def get_objects(self,classes=None,as_type=dict,**kwargs):
        """Find objects belonging to specified classes

        Arguments:
        - classes (str|list of str): patterns of class names to search (default is '.*')
        - as_type (class): type to use for return value
        - kwargs (dict): arguments for as_type

        Return:
        - as_type: object data
        """
        if type(classes) is str:
            match = classes.split(",")
        else:
            match = []
            for y in classes if classes else '.*':
                match.extend([x for x in self.classes if re.match(y,x)])
        data = dict([(obj,data) for obj,data in self.objects.items() if data["class"] in match])
        return as_type(data,**kwargs)

    def rename(self,name):
        self.filename = name
        self.is_modified = True

if __name__ == "__main__":

    import unittest

    if not os.path.exists("/tmp/13.glm"):
        gridlabd("model","get","IEEE/13")
        os.system("mv 13.glm /tmp")
        gridlabd("-C","/tmp/13.glm","-o","/tmp/13.json")

    class TestModel(unittest.TestCase):

        # def test_glm(self):
        #     glm = GridlabdModel("/tmp/13.glm",force=True)
        #     loads = glm.get_objects(classes=[".*load"])
        #     self.assertEqual(len(loads),10)

        # def test_json(self):
        #     glm = GridlabdModel("/tmp/13.json")
        #     loads = glm.get_objects(classes=["load","triplex_load"])
        #     self.assertEqual(len(loads),10)

        # def test_new(self):

        #     glm = GridlabdModel("/tmp/test.json",force=True)
        #     self.assertEqual(glm.objects,{})
        #     self.assertEqual(glm.classes,{})

        def test_str_glm(self):
            with open("/tmp/13.glm","r") as fh:
                data = fh.read()
                glm = GridlabdModel(data)
                loads = glm.get_objects(classes=["load","triplex_load"])
                self.assertEqual(len(loads),10)

        # def test_str_json(self):
        #     with open("/tmp/13.json","r") as fh:
        #         data = json.load(fh)
        #         glm = GridlabdModel(data)
        #         loads = glm.get_objects(classes=["load","triplex_load"])
        #         self.assertEqual(len(loads),10)

    unittest.main()
