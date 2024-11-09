"""Utilities to link CVX with GridLAB-D networks"""

import numpy as np
import scipy as sp

class Model:

    def __init__(self,source=None):
        assert(source==gld or isinstance(source,dict))

class Property:

    def __init__(self,model,*args):
        assert isinstance(model,dict),"model type invalid"
        assert model["application"]=="gridlabd","not a gridlabd model"
        self.model = model
        self.obj = args[0]
        self.name = args[1]

    def get_object(self,*args):

        return self.obj

    def set_object(self,*args):

        self.obj = args[0]

    def get_name(self,*args):

        return self.name

    def get_initial(self,*args):

        try:
            return model["classes"][model["objects"]["class"]]["initial"]
        except:
            return None
        
    def get_value(self,*args):

        return model["objects"][self.obj][self.name]

    def set_value(self,*args):

        model["objects"][self.obj][self.name] = args[0]

    def rlock(self,*args):

        return None

    def wlock(self,*args):

        return None

    def unlock(self,*args):

        return None

    def convert_unit(self,*args):

        raise RuntimeError("cannot convert units in static models")

        
class GldModel(Model):

    def __init__(self):
        self.cache = {}
        super().__init__(gld)

    def objects(self):
        return gld.objects

    def classes(self):
        return gld.classes

    def globals(self):
        return gld.globals

    def property(self,*args):
        key = "#".join(args)
        try:
            return self.cache[key]
        except:
            prop = gld.property(*args)
            self.cache[key] = prop
            return prop

class JsonModel(Model):

    def __init__(self,jsonfile):
        import json
        self.json = json.load(open(jsonfile,"r"))
        super().__init__(self.json)

    def objects(self):
        return self.json["objects"]

    def classes(self):
        return self.json["classes"]

    def globals(self):
        return self.json["globals"]

    def property(self,*args):
        return Property(model,*args)


class Network:
    """Network model accessor
    """
    def __init__(self):

        self.update()

    def update(self,auto=None):

        model = GldModel()
        now = model.property("clock").get_value()
        if auto is None:


            if not hasattr(self,'last') or now > self.last:

                update = True

            else:

                update = False

        elif isinstance(auto,bool):

            update = auto

        else:

            raise ValueError("auto is not boolean or None")

        if not hasattr(self,'nodes') or not hasattr(self,'lines') or update:

            self.last = now
            self.lines = []
            self.nodes = {}
            self.Y = []
            for name,data in model.objects().items():

                oclass = model.classes()[data["class"]]
                if "from" in oclass and "to" in oclass:
                    Z = model.property(name,"R").get_value()
                    if Z > 0:
                        fobj,tobj = model.property(name,"from").get_value(),model.property(name,"to").get_value()
                        for obj in [fobj,tobj]:
                            if not obj in self.nodes:
                                self.nodes[obj] = len(self.nodes)
                        self.lines.append([self.nodes[fobj],self.nodes[tobj]])
                        self.Y.append(1/Z)

            self.bus = np.array(list(self.nodes.values()))
            self.branch = np.array(self.lines)
            self.row,self.col = self.branch.T.tolist()
            M = len(self.branch)
            N = len(self.bus)

            # adjacency matrix 
            self.A = sp.sparse.coo_array(
                (   [1]*len(self.row) + [-1]*M, # data
                    (self.row+self.col,self.col+self.row) # coords
                    ),
                shape=(N,N),
                )

            # degree matrix
            self.D = sp.sparse.diags(np.abs(self.A).sum(axis=1))

            # Laplacian matrix
            self.L = self.D - self.A

            # oriented incidence matrix
            self.B = sp.sparse.coo_array(([1]*M,(list(range(M)),self.row)),shape=(M,N)) - sp.sparse.coo_array(([1]*M,(list(range(M)),self.col)),shape=(M,N))

            # weighted Laplacian matrix
            self.W = self.B.T @ sp.sparse.diags_array(self.Y) @ self.B
