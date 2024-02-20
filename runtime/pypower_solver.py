import os, sys
from pypower import runpf
from numpy import array

with_opf = False
save_case = True

def solver(pf_case):

    data = dict(version=pf_case['version'],baseMVA=pf_case['baseMVA'])

    # copy from model
    for name in ['bus','branch','gen']:
        data[name] = array(pf_case[name])

    if save_case:
        with open("casedata.py","w") as fh:
            fh.write(str(save_case))

    # TODO: call solver
    _,result = runpf(data)

    # copy back to model
    if result:
        for name in ['bus','branch','gen']:
            pf_case[name] = data[name].tolist()

    print(f"solver(pf_case={pf_case})",file=sys.stderr,flush=True)

    return True

