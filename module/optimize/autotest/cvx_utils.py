"""Utilities to link CVX with GridLAB-D networks"""

import numpy as np
import scipy as sp

class Network:
    """Network accessor
    """
    def __init__(self):

        self.update()

    def update(self,auto=None):

        if auto is None:

            now = gld.property("clock").get_value()

            if not hasattr(self,'last') or now > self.last:
                update = True
                self.last = now
        elif isinstance(auto,bool):

            update = auto

        else:

            raise ValueError("auto is not boolean or None")

        if not hasattr(self,'nodes') or not hasattr(self,'lines') or update:

            self.lines = []
            self.nodes = {}
            self.Y = []
            for name,data in gld.objects.items():

                oclass = gld.classes[data["class"]]
                if "from" in oclass and "to" in oclass:
                    Z = gld.property(name,"R").get_value()
                    if Z > 0:
                        fobj,tobj = gld.property(name,"from").get_value(),gld.property(name,"to").get_value()
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
