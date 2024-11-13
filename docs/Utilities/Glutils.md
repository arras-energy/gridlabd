[[/Utilities/Glutils]] -- Utilities to link CVX with GridLAB-D networks


# Classes

## GldModel

Dynamic model accessor

## JsonModel

Static model accessor

## Model

Model accessor base class

## Network

Network model accessor

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


## Property

JSON property accessor

# Functions

## `from_complex(x:str) -> complex`

Convert string complex

## `from_timestamp(x:str) -> dt.datetime`

Convert string to timestamp

## `rarray(x:str) -> np.array`

Convert string to float array
