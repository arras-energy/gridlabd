import json
from numpy import array
import cvxpy as cvx
import pandas as pd

with open("test_cvx.json","r") as fh:
    model = json.load(fh)
    name = [x for x,y in model["objects"].items() if y["class"] == "test"]
    A = array([float(y["A"]) for x,y in model["objects"].items() if y["class"] == "test"])
    b = array([float(y["b"]) for x,y in model["objects"].items() if y["class"] == "test"])
    y = array([float(y["y"]) for x,y in model["objects"].items() if y["class"] == "test"])

print(pd.DataFrame({"A":A,"b":b,"y":y,"A@y-b":A@y-b},index=name))

assert cvx.sum_squares(A@y-b).value.round(4) == round(float(model["objects"]["problem-y-dpp"]["value"]),4), "value does not match objective"

print("problem-y-dpp solution is ok")
