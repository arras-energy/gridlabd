"""GridLAB-D assert module

TODO
"""

def assert_init(obj,t):
    """Assert commit event handler

        Arguments
    ---------
    - `obj`: object name
    - `t`: current timestamp

    Returns
    -------
    - `int`: next timestamp
    """
    return gldcore.INIT_OK

def assert_commit(obj,t):
    """Assert commit event handler

        Arguments
    ---------
    - `obj`: object name
    - `t`: current timestamp

    Returns
    -------
    - `int`: next timestamp
    """
    return gldcore.NEVER
