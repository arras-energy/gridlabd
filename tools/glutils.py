"""Utilities to link CVX with GridLAB-D networks"""

import sys
import numpy as np
import scipy as sp
import datetime as dt
from typing import TypeVar

class Model:
    """Model accessor base class"""
    def __init__(self,source=None):
        assert("gld" in globals() and source==gld) or isinstance(source,dict), "invalid source"

    def globals(self) -> list:
        raise RuntimeError("baseclass globals not accessible")

    def objects(self) -> dict:
        raise RuntimeError("baseclass objects not accessible")

    def classes(self) -> dict:
        raise RuntimeError("baseclass classes not accessible")

    def properties(self) -> dict:
        raise RuntimeError("baseclass properties not accessible")

    def properties(self,*args) -> TypeVar('Property'):
        raise RuntimeError("baseclass property not accessible")

def rarray(x):
    return np.array(x,dtype=np.float64)

def from_timestamp(x):
    if x == "NEVER":
        return dt.datetime.strptime("2999-12-31 23:59:59 UTC","%Y-%m-%d %H:%M:%S %Z")
    elif x == "INIT":
        return dt.datetime.fromtimestamp(0);
    else:
        return dt.datetime.strptime(x,"%Y-%m-%d %H:%M:%S %Z")

def from_complex(x):
    try:
        return complex(x.split()[0] if " " in x else x)
    except:
        return complex(float('nan'),float('nan'))

class Property:
    """JSON property accessor"""
    fromtypes = {
        "double": lambda x: float(x.split()[0]),
        "complex": from_complex,
        "int16": int,
        "int32": int,
        "int64": int,
        "bool": bool,
        "timestamp": from_timestamp,
        "double_array": lambda x: np.array(x,dtype=np.float64),
        "complex_array": lambda x: np.array(x,dtype=np.complex_),
        "real": float,
        "float" : float,
        # everything else is str
    }
    totypes = {
        "timestamp": lambda x: int(x.isoformat())
        # everything else is str
    }
    def __init__(self,model:TypeVar(Model),*args:list[str]):
        """Property accessor constructor
        
        Arguments:

        * model: the GridLAB-D model

        * args: global name or object name followed by property name 
        """
        assert isinstance(model,JsonModel),"model type invalid"
        self.data = model.data
        assert self.data["application"] == "gridlabd", "not a gridlabd model"
        if len(args) == 1:
            self.obj = None
            self.name = args[0]
        elif len(args) == 2:
            self.obj,self.name = args
        else:
            raise ValueError("too many arguments")

    def get_object(self) -> str:
        """Get object name"""
        return self.obj

    def set_object(self,value:str):
        """Set object name"""
        self.obj = value

    def get_name(self) -> str:
        """Get property name"""
        return self.name

    def get_initial(self) -> str|float|int|bool|complex:
        """Get default value, if any"""
        try:
            spec = self.data["classes"][self.data["objects"][self.obj]["class"]]
            value = spec["default"]
            vtype = self.fromtypes[spec["type"]] if spec["type"] in self.fromtypes else str
            return vtype(value)
        except:
            return None
        
    def get_value(self) -> str|float|int|complex|bool|dt.datetime:
        """Get value, if any"""
        try:
            if not self.name in self.data["header"]:
                spec = self.data["classes"][self.data["objects"][self.obj]["class"]][self.name]
                data = self.data["objects"][self.obj]
                if self.name in data:
                    value = data[self.name] 
                    vtype = self.fromtypes[spec["type"]] if spec["type"] in self.fromtypes else str
                    return vtype(value)
                return None
            return None
        except KeyError:
            spec = self.data["globals"][self.name]
            value = spec["value"]
            vtype = self.fromtypes[spec["type"]] if spec["type"] in self.fromtypes else str
            return vtype(value)

    def set_value(self,value:str|float|int|complex|bool|dt.datetime):
        """Set property value"""
        try:
            # TODO: use totypes
            self.data["objects"][self.obj][self.name] = str(value)
        except KeyError:
            self.data["globals"][self.name]["value"] = str(value)

    def rlock(self):
        """Lock property for read"""
        return None

    def wlock(self):
        """Lock property for write"""
        return None

    def unlock(self):
        """Unlock property"""
        return None

    def convert_unit(self,unit:str) -> float:
        """Convert property units"""
        raise RuntimeError("cannot convert units in static models")

class GldModel(Model):
    """Dynamic model accessor"""
    def __init__(self):
        """Dynamic model accessor"""
        assert "gld" in globals(), "no current simulation running ('gld' is not built-in)"
        self.cache = {}
        super().__init__(gld)

    def objects(self) -> dict:
        """Get objects in model"""
        return gld.objects

    def classes(self) -> dict:
        """Get classes"""
        return gld.classes

    def globals(self) -> list[str]:
        """Get list of global names"""
        return gld.globals

    def properties(self,obj) -> list[str]:
        """Get list of properties in object"""
        raise NotImplementedError("properties not implemented yet")

    def property(self,*args) -> TypeVar('Property'):
        """Get property accessor

        Arguments:

        * obj (str): object name or global variable name

        * name (str): property name (for objects only, None for globals)

        Returns:

        Property: the property accessor
        """
        key = "#".join(args)
        try:
            return self.cache[key]
        except:
            self.cache[key] = prop = gld.property(*args)
            return prop

class JsonModel(Model):
    """Static model accessor"""
    def __init__(self,jsonfile):
        """Static model accessor

        Arguments:

        * jsonfile (str): name of JSON file to access
        """
        import json
        self.data = json.load(open(jsonfile,"r"))
        super().__init__(self.data)

    def objects(self) -> dict:
        """Get objects in model"""
        header = ["class","id","latitude","longitude","group","parent"]
        return {x:{z:w for z,w in y.items() if z in header} for x,y in self.data["objects"].items()}

    def classes(self) -> dict:
        """Get classes in model"""
        return {x:[z for z,w in y.items() if type(w) is dict] for x,y in self.data["classes"].items()}

    def globals(self) -> list[str]:
        """Get globals in model"""
        return list(self.data["globals"])

    def properties(self,obj) -> list[str]:
        """Get list of object properties"""
        return list([x for x,y in self.data["classes"][self.data["objects"][obj]["class"]].items() if isinstance(y,dict)])

    def property(self,*args) -> TypeVar('Property'):
        """Get property accessor

        Arguments:

        * obj (str): object name or global variable name

        * name (str): property name (for objects only, None for globals)

        Returns:

        Property: the property accessor
        """
        return Property(model,*args)


class Network:
    """Network model accessor

    Arguments:

    * model (dict): JSON model (dynamic model if None)

    * matrix (list): List of matrices to generation (all if None)

    * nodemap (dict): Map of properties to extract from nodes (or None)

    * linemap (dict): Map of properties to extract from lines (or None)

    The network model accessor generates a vector for all the extracted
    properties in the `nodemap` and `linemap` arguments, if any. The
    accessor also generates all the matrices listed in the `matrix` 
    argument or all if `None`.

    Properties generated for `matrix` list:

    * last (dt.datetime): time of last update (when force=None)

    * lines (list[str]): list of lines in model

    * nodes (dict): nodes map

    * Y (list[float]): list of line admittances

    * bus (np.array): bus matrix

    * branch (np.array): branch matrix

    * row (np.array): row index matrix (branch from values)

    * col (np.array): col index matrix (branch to values)

    * A (np.array): adjacency matrix

    * D (np.array): degree matrix

    * L (np.array): graph Laplacian matrix

    * B (np.array): oriented incidence matrix

    * W (np.array): weighted Laplacian matrix
    """
    def __init__(self,
        model:dict=None,
        matrix:list=None,
        nodemap:dict=None,
        linemap:dict=None,
        ):
        """Network model accessor constructor"""
        self.model = model if model else GldModel()
        self.matrix = matrix
        self.nodemap = nodemap if nodemap else {}
        self.linemap = linemap if linemap else {}

        self.update(force=True)

    def update(self,force=None):
        """Update dynamic model

        Arguments:

        * force (None|bool): force update (None is auto)
        """
        model = self.model
        now = model.property("clock").get_value()
        if force is None:


            if not hasattr(self,'last') or now > self.last:

                update = True

            else:

                update = False

        elif isinstance(force,bool):

            update = force

        else:

            raise ValueError("force is not boolean or None")

        if not hasattr(self,'nodes') or not hasattr(self,'lines') or update:

            # initialize the extract arrays
            self.last = now
            self.lines = []
            self.nodes = {}
            self.names = {"node":[],"line":[]}
            try:
                self.baseMVA = float(model.property("pypower::baseMVA").split()[0])
            except:
                self.baseMVA = 100.0
            self.refbus = []
            self.Y = []
            self.Yc = []
            self.R = []
            self.Z = []
            for var in self.linemap:
                if var in ["D","L","A","B","W","Wc","Y","Z"]:
                    raise ValueError(f"linemap name {var} is reserved for matrices")
                setattr(self,var,[])
            for var in self.nodemap:
                if var in ["D","L","A","B","W","Wc","Y","Z"]:
                    raise ValueError(f"nodemap name {var} is reserved for matrices")
                setattr(self,var,[])

            # create a reverse map of bus names from bus index
            busindex = {int(model.property(x,"bus_i").get_value()):x for x,y in model.objects().items() if y["class"] == "bus"}
            
            # process every object in the model
            for name,data in model.objects().items():

                # get the object class
                oclass = model.classes()[data["class"]]

                # pypower branches contain "fbus" and "tbus" properties
                if "fbus" in oclass and "tbus" in oclass:

                    # append the linemap values to the extract arrays
                    for var,prop in self.linemap.items():
                        val = model.property(name,prop).get_value()
                        getattr(self,var).append(val)

                    # append the line name to the line names array 
                    self.names["line"].append(name)

                    # get the fbus and tbus indexes
                    fobj,tobj = model.property(name,"fbus").get_value(),model.property(name,"tbus").get_value()

                    # for each of the from and to bus indexes
                    for obj in [fobj,tobj]:

                        # if the bus index is not yet listed in the nodes list
                        if not obj in self.nodes:

                            # add the bus index to the node list
                            self.nodes[obj] = len(self.nodes)

                            # get the name index for the bus
                            ndx = busindex[int(obj)]

                            # append the nodemap values to the extract arrays
                            for var,prop in self.nodemap.items():
                                val = model.property(ndx,prop).get_value()
                                getattr(self,var).append(val)

                            # append the index name to the node name array
                            self.names["node"].append(ndx)

                            # if the bus is a reference bus
                            if model.property(ndx,"type").get_value() == "REF":

                                # append the bus index to the reference bus list
                                self.refbus.append(obj)

                    # append the from and to bus index to line list
                    self.lines.append([self.nodes[fobj],self.nodes[tobj]])

                    # get the line impedance
                    Z = complex(*[model.property(name,x).get_value() for x in ["r","x"]])

                    # append the impedance to the Z array
                    self.Z.append(Z)

                    # if the impedance is non-zero
                    if abs(Z) > 0:

                        # append the admittance to the Y arrays
                        self.Y.append(1/Z.imag) # susceptance dominates over conductance
                        self.Yc.append(1/Z)
                    
                    else: # zero impedance means no line present (proxy for infinity)

                        # no admittance
                        self.Y.append(0)
                        self.Yc.append(complex(0))

                # powerflow lines contain from and to object names
                elif "from" in oclass and "to" in oclass:

                    raise NotImplementedError("powerflow network not supported")

            # create the bus index array
            self.bus = np.array(list(self.nodes.values()))

            # create the branch index array
            self.branch = np.array(self.lines)

            # create the row and col index arrays
            self.row,self.col = self.branch.T.tolist()

            # get the number of branches and busses
            M = len(self.branch)
            N = len(self.bus)

            # adjacency matrix 
            if self.matrix is None or "A" in self.matrix or "L" in self.matrix:
                self.A = sp.sparse.coo_array(
                    (   [1]*M + [-1]*M, # data
                        (self.row+self.col,self.col+self.row) # coords
                        ),
                    shape=(N,N),
                    dtype=int
                    )

            # degree matrix
            if self.matrix is None or "D" in self.matrix or "L" in self.matrix:
                self.D = sp.sparse.diags(np.abs(self.A).sum(axis=1),dtype=int)

            # Laplacian matrix
            if self.matrix is None or "L" in self.matrix:
                self.L = self.D - self.A

            # oriented incidence matrix
            if self.matrix is None or "B" in self.matrix or "W" in self.matrix or "Wc" in self.matrix: 
                self.B = sp.sparse.coo_array(([1]*M,(list(range(M)),self.row)),shape=(M,N)) - sp.sparse.coo_array(([1]*M,(list(range(M)),self.col)),shape=(M,N),dtype=int)

            # weighted Laplacian matrix
            if self.matrix is None or "W" in self.matrix:
                self.W = self.B.T @ sp.sparse.diags_array(self.Y,dtype=np.float64) @ self.B
            if self.matrix is None or "Wc" in self.matrix:
                self.Wc = self.B.T @ sp.sparse.diags_array(self.Yc,dtype=np.complex_) @ self.B

#
# Test JSON accessors
#
if __name__ == "__main__":

    import os
    import sys
    import json

    assert not "gld" in globals(), "not running as static model ('gld' is built-in)"

    if not os.path.exists("autotest/case14.json"):
        os.system("cd autotest; gridlabd convert case14.py case14.glm")
        os.system("gridlabd -C autotest/case14.glm -o autotest/case14.json")

    model = JsonModel('autotest/case14.json')
    
    assert "bus" in model.classes(), "class 'bus' not found in model"
    assert "bus_i" in model.classes()["bus"], "class 'bus' missing property 'bus_i'"

    assert "pypower::version" in model.globals(), "global 'pypower::version' not found in model"
    assert model.property("pypower::version").get_value() == 2, "pypower::version value is not 2"

    assert "pp_bus_1" in model.objects(), "object 'pp_bus_1' not found in model"
    assert model.property("pp_bus_1","bus_i").get_value() == 1, "pp_bus_1.bus_1 is not 1"

    with open("autotest/case14.txt","w") as txt:
        for var in model.globals():
            print("global",var,"get_object() ->",model.property(var).get_object(),file=txt)
            print("global",var,"get_name() ->",model.property(var).get_name(),file=txt)
            print("global",var,"get_value() ->",model.property(var).get_value(),file=txt)
            print("global",var,"property() ->",model.property(var).get_initial(),file=txt)

        for obj in model.objects():
            for var in model.properties(obj):
                print(obj,var,"property().get_object() ->",model.property(obj,var).get_object(),file=txt)
                print(obj,var,"property().get_name() ->",model.property(obj,var).get_name(),file=txt)
                init = model.property(obj,var).get_initial()
                print(obj,var,"property().get_initial() ->",init,file=txt)
                value = model.property(obj,var).get_value()
                print(obj,var,"property().get_value() ->",value,file=txt)
                if not value is None or not init is None:
                    model.property(obj,var).set_value(init if value is None else value)
                    assert model.property(obj,var).get_value()==value, "value changed"

    network = Network(model,matrix=['W'],nodemap={"_D":"Pd"})
    np.set_printoptions(precision=1)
    assert network.B.shape == (20,14), "B shape is incorrect"
    assert network.W.shape == (14,14), "W shape is incorrect"
    assert network.refbus == [1], "refbus is incorrect"
    assert len(network.Y) == 20, "Y size is incorrect"
    assert len(network._D) == 14, "_D size is incorrect"

