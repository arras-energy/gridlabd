"""Cache control

Syntax: gridlabd cache [OPTIONS ...] COMMAND

Options:

* `--tool=[TOOL,...]`: specify tool cache

Commands:

* `list`: list the contents of the cache

* `clear`: clear the cache

* `peek`: peek at the cache contents

Description:

The `cache` command manipulate the `gridlabd` cache data.
"""

import os
import sys
import gridlabd.framework as app

CACHEDIR = os.path.join(os.environ["GLD_ETC"],".cache")

class CacheError(Exception):
    """Cache exception"""

class Cache:

    def __init__(self,tool=None):

        # get/check cachedir
        self.cachedir = os.path.join(CACHEDIR,tool) if tool else CACHEDIR
        if not os.path.exists(self.cachedir):

            os.makedirs(self.cachedir,exist_ok=True)

    def get(self,name,on_fail=None,args=[],kwargs={}):
        """Get data from the cache

        Arguments:
        
        * `name`: the file name

        * `on_fail`: the function to call if the name does not exist in the cache

        Returns:

        * `str`: the contents of the cache

        Description:

        Retrieves data from the cache if found. If the data is not found, the
        `on_fail(name,*args,**kwargs)` function is called and the return
        value is stored in the cache.

        If `on_fail` is not specified, the `get` peeks at the cache and
        returns the contents if any. If nothing is found, a `CacheError`
        exception is raised.
        """
        pathname = os.path.join(self.cachedir,name)
        if os.path.exists(pathname):
            return open(pathname,"r").read()
        if not on_fail:
            raise CacheError(f"'{name}' not found")
        result = on_fail(*args,**kwargs)
        try:
            with open(pathname,"w") as fh:
                fh.write(str(result))
                return result
        except:

            # remove anything that causes a failure so it has a chance of working next time
            os.remove(pathname)
            raise

    def list(self):
        """List the cache contents"""
        return [x for x in os.listdir(self.cachedir) if not x.startswith(".")]

    def clear(self):
        """Clear the cache

        Arguments:

        """
        for item in [x for x in os.listdir(self.cachedir) if x not in [".",".."]]:
            os.remove(os.path.join(self.cachedir,item))

def main(argv:list[str]) -> int:
    """Main routine

    Arguments:

    * `argv`: command line arguments

    Returns:

    * `int`: exit code
    """
    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        elif key == "list":

            Cache().list()

        elif key == "clear":

            Cache().clear()

        elif key == "peek":

            Cache().get(value)

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # implement your code here

    # normal termination condition
    return app.E_OK

def test() -> (int,int):

    n_tested = 0
    n_failed = 0
    import random
    import shutil
    name = f".test-{hex(random.randint(0,2**64-1))[2:]}"
    cache = Cache(name)

    try:

        assert cache.list() == [], f"new random test cache '{name}' is not empty"
        assert cache.get("test",lambda x: name) == name, f"cache value does not match"
        cache.clear()
        assert cache.list() == [], f"new random test cache '{name}' clear failed"

        n_tested += 1

    except:

        e_type,e_value,e_trace = sys.exc_info()
        print(f"TEST FAILED: {__file__}@{e_trace.tb_lineno} ({e_type.__name__}) {e_value}")
        n_failed += 1

    finally:

        shutil.rmtree(cache.cachedir)

    return n_failed,n_tested

if __name__ == "__main__":

    if not sys.argv[0]:

        n,m = test()
        print(f"{os.path.basename(__file__)}: {m} tests, {n} failed")

    else:

        app.run(main)
