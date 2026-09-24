"""GridLAB-D Command Line Processor
"""

import subprocess

def glm_command(*args,**kwargs):
    """Process GridLAB-D command line

    Arguments
    ---------
    - `*args`: `gridlabd.bin` command line arguments
    - `**kwargs`: subprocess run options (see `subprocess.run`)

    Returns
    -------
    - `subprocess.CompletedProcess`: subprocess run result
    """
    if "capture_output" not in kwargs:
        kwargs["capture_output"] = True
    if "text" not in kwargs:
        kwargs["text"] = True
    return subprocess.run(["gridlabd.bin"] + list(args), **kwargs)
