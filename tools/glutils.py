"""GridLAB-D model access utilities

Syntax: gridlabd glutils JSONFILE [OPTIONS ...]

Options:

* --debug: enable traceback on exceptions

* --test: run a self test

* graph:VAR: matrix analysis result

* node:VAR: node property vector

* line:VAR: line property vector

The `glutils` module is a `gridlabd` runtime model accessor library that can
be used when running Python code in `gridlabd` modules. The accessors allow
Python code to read and write both global variables and object properties.
The library also includes convenience methods to obtain a list global
variables, and dictionaries of object, object header values, classes, class
members, as well as property accessor that can perform unit conversion.

The `glutils` module also includes a JSON model accessor that uses the same
underlying methods as the runtime accessor.

The utilities include a number of useful graph theory methods to extract the
structure and properties of network embedded in the model. Networks are
identified by `from` and `to` properties in edges, or in the case of
`pypower` models, the presence of `fbus` and `tbus` properties that refer to
`bus_i` properties in vertices. The following structural property can be
extracted using the `graph` option:

* A: adjacency matrix

* D: degree matrix

* L: graph Laplacian matrix

* B: oriented incidence matrix

* W: weighted real Laplacian matrix

* Wc: weighted complex Laplacian matrix

Metadata arrays are also extract to support interpretation of the graph
matrices. These include the following:

* lines: list of line from/to tuples as an index into the `bus` list

* nodes: mapping of the node ids as an index into the `branch` list

* names: a list of the node and line object names in the model

* baseMVA: the baseMVA value, if found

* row: the `from` node index in the graph matrices

* col: the `to` node index in the graph matrices

* bus: the bus list

* branch: the branch from/to list

The extraction process automatically generates the edge weights based on the
line impedance. These are stored in `Y`, `Yc`, and `Z`.  All other properties
of lines/branches or nodes/buses can be extracted as a vector using the
`line` and `node` options, respectively by defining the mapping, e.g.,
`node:VAR:PROPERTY`, where `VAR` is any string not already used for graph
matrices and impedance vectors.
"""

import os
import sys
import json
import numpy as np
import scipy as sp
import datetime as dt
from typing import TypeVar
import inspect

DEBUG = True

class Model:
    # Baseclass for model accessors
    def __init__(self,source:dict=None) -> None:
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

def rarray(x:str) -> TypeVar('np.array'):
    # Convert string to float array
    return np.array(x,dtype=np.float64)

def from_timestamp(x:str) -> TypeVar('dt.datetime'):
    # Convert string to timestamp
    if x == "NEVER":
        return dt.datetime.strptime("2999-12-31 23:59:59 UTC","%Y-%m-%d %H:%M:%S %Z")
    elif x == "INIT":
        return dt.datetime.fromtimestamp(0);
    else:
        return dt.datetime.strptime(x,"%Y-%m-%d %H:%M:%S %Z")

def from_complex(x:str) -> complex:
    # Convert string complex
    try:
        return complex(x.split()[0] if " " in x else x)
    except:
        return complex(float('nan'),float('nan'))

class Property:
    """JSON property accessor

    This property accessor is the static model version of the dynamic accessor that is built-in when running Python inside a GridLAB-D
    simulation.
    """
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
    def __init__(self,model:TypeVar('Model'),*args:list[str]) -> None:
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
        """Get the object name for this property

        Returns:

        * str: the name of the object to which this property refers
        """
        return self.obj

    def set_object(self,value:str) -> None:
        """Set the object name for this property"""
        self.obj = value

    def get_name(self) -> str:
        """Get the property name

        Returns:

        * str: the name of the property
        """
        return self.name

    def get_initial(self) -> str|float|int|bool|complex:
        """Get default value, if any

        Returns:
        * str|float|int|bool|complex: the default value of the property
        """
        try:
            oclass = self.data["objects"][self.obj]["class"]
            spec = self.data["classes"][oclass]
            value = spec["default"]
            vtype = self.fromtypes[spec["type"]] \
                if spec["type"] in self.fromtypes else str
            return vtype(value)
        except:
            return None
        
    def get_value(self) -> str|float|int|complex|bool|dt.datetime:
        """Get value, if any"""
        try:
            if not self.name in self.data["header"]:
                oclass = self.data["objects"][self.obj]["class"]
                spec = self.data["classes"][oclass][self.name]
                data = self.data["objects"][self.obj]
                if self.name in data:
                    value = data[self.name] 
                    vtype = self.fromtypes[spec["type"]] \
                        if spec["type"] in self.fromtypes else str
                    return vtype(value)
                return None
            return None
        except KeyError:
            spec = self.data["globals"][self.name]
            value = spec["value"]
            vtype = self.fromtypes[spec["type"]] \
                if spec["type"] in self.fromtypes else str
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
    """Dynamic model accessor

    The dynamic model accessor allows Python code running in a simulation to access global variables and object properties while the simulation is running.  Use `objects()` to obtain a dict of object names and header values. Use `classes()` to obtain a dict class name and properties. Use `globals()` to obtain a list of global variables.  Use `properties(obj)` to obtain a list of properties of an object. Use `property(obj)` to access an object property or global variable value.
    """
    def __init__(self) -> None:
        """Dynamic model accessor"""
        assert "gld" in globals(), \
            "no current simulation running ('gld' is not built-in)"
        self.cache = {}
        super().__init__(gld)

    def objects(self) -> dict:
        """Get objects in model

        Returns:

        * dict: the object names and header values
        """
        return gld.objects

    def classes(self) -> dict:
        """Get classes

        Returns:

        * dict: the classes and property names available
        """
        return gld.classes

    def globals(self) -> list[str]:
        """Get list of global names

        Returns:

        * list: the global variables defined
        """
        return gld.globals

    def properties(self,obj) -> list[str]:
        """Get list of properties in object

        Returns:

        * list: the list of properties defined in an object
        """
        raise NotImplementedError("properties not implemented yet")

    def property(self,*args) -> TypeVar('gld.property'):
        """Get property accessor

        Arguments:

        * obj (str): object name or global variable name

        * name (str): property name (for objects only, None for globals)

        Returns:

        gld.property: the dynamic property accessor
        """
        key = "#".join(args)
        try:
            return self.cache[key]
        except:
            self.cache[key] = prop = gld.property(*args)
            return prop

class JsonModel(Model):
    """Static model accessor"""
    def __init__(self,jsonfile) -> None:
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

class NetworkError(Exception):
    pass

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

    * names (dict): names of node and line objects

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

    RESULTS = ["D","L","A","B","W","Wc"]

    def __init__(self,
        model:dict=None,
        matrix:list=None,
        nodemap:dict=None,
        linemap:dict=None,
        ) -> None:
        """Network model accessor constructor"""
        self.model = model if model else GldModel()
        self.matrix = matrix
        self.nodemap = nodemap if nodemap else {}
        self.linemap = linemap if linemap else {}

        self.update(force=True)

    def todict(self,extras=None,precision=6) -> dict:
        """Get network data as a dict

        Arguments:

        * extras: include extracted node or line variables with network data

        * precision: change precision of extracted values (default is 6)

        Returns:

        * dict: network data
        """
        result = {x:getattr(self,x) for x in ["lines","nodes","names","refbus",
                "baseMVA","row","col",
                ]}
        result['Y'] = [round(x,precision) for x in network.Y]
        for x in ["Z","Yc"]:
            result[x] = [f"{round(x.real,precision):f}{round(x.imag,precision):+f}j" for x in getattr(self,x)]
        for x in ["bus","branch"]:
            result[x] = getattr(self,x).round(precision).tolist()
        for x in self.RESULTS:
            if x in dir(self):
                value = getattr(self,x).todense()
                if value.dtype == np.complex_:
                    result[x] = [[str(y).strip('()') for y in x] for x in value.round(precision).tolist()]
                else:
                    result[x] = value.round(precision).tolist()
        for x,y in extras.items() if extras else {}:
            if x in dir(self):
                result[x] = y(getattr(self,x))
        return result

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
            self.Z = []
            for var in self.linemap:
                if var in self.RESULTS + ["Y","Yc","Z","last","lines",
                        "nodes","names","refbus","baseMVA"]:
                    raise ValueError(f"linemap name {var} is reserved for matrices")
                setattr(self,var,[])
            for var in self.nodemap:
                if var in self.RESULTS + ["Y","Yc","Z","last","lines",
                        "nodes","names","refbus","baseMVA"]:
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

                    raise NotImplementedError(f"powerflow network not supported (object '{name}')")

            if self.nodes and self.lines:

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

    def islands(self,precision:int=9) -> int:
        """Calculate the number of islands in network

        Arguments:

        * precision (int): the precision with which to evaluate eigenvalues

        Returns:

        * int: the number of connected subnetworks in the network
        """
        if not hasattr(self,"W"):
            raise NetworkError("cannot compute islands unless W is computed")

        # TODO: replace with sp.linalg.eigs
        e,v = np.linalg.eigh(network.W.todense())
        return len([x for x in e.round(precision) if x == 0.0])
#
# Test JSON accessors
#
if __name__ == "__main__":

    if len(sys.argv) == 1:
        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax")]))
        exit(1)

    if sys.argv[1] in ["-h","--help","help"]:

        print(__doc__)
        exit(0)

    try:

        if sys.argv[1] == "--test":

            assert not "gld" in globals(), "not running as static model ('gld' is built-in)"

            source = "tools/autotest/case14.py"
            python = os.path.join("/tmp",os.path.basename(source))
            glmfile = python.replace(".py",".glm")
            target = python.replace(".py",".json")
            os.system(f"gridlabd source {source} > {python}")
            os.system(f"cd /tmp; gridlabd convert {os.path.basename(python)} {os.path.basename(glmfile)}")
            os.system(f"gridlabd -C {glmfile} -o {target}")

            model = JsonModel(target)
            
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
            assert network.islands() == 1, "incorrect number of islands"

            exit(0)

        DEBUG = "--debug" in sys.argv
        if DEBUG:
            sys.argv.remove("--debug")

        model = JsonModel(sys.argv[1])
        matrix = [x.split(':',2)[1] for x in sys.argv[2:] if x.startswith("graph:")]
        nodes = dict([x.split(':',3)[1:] for x in sys.argv[2:] if x.startswith("node:")])
        lines = dict([x.split(':',3)[1:] for x in sys.argv[2:] if x.startswith("line:")])
        print(matrix,nodes,lines)
        network = Network(model,matrix=matrix,nodemap=nodes,linemap=lines)
        for key in [x for x in sys.argv[2:] if not x.split(":")[1] in dir(network)]:
            print(f"WARNING [glutils.py]: '{key}' is not a valid network analysis result",file=sys.stderr)
        extras = list(nodes) + list(lines)
        print(json.dumps(network.todict(extras={y:lambda x:x for y in extras}),indent=2))

    except Exception as err:

        print(f"ERROR [glutils.py]: {err}",file=sys.stderr)

        if DEBUG:
            raise

