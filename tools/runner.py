"""GridLAB-D runner

Library for gridlabd runner.

Example:

The following python code gets the current version of GridLAB-D.

~~~
import gridlabd.runner as gld
version = gld.gridlabd("--version")
print(version)
~~~
"""
import os
import sys
import json
import io
import subprocess
import time
import shutil
import gridlabd as gld
import random
from typing import TypeVar

class GridlabdRunnerException(Exception):
    """GridLAB-D runner exception handler"""

EXITCODES = {
    -1 : "FAILED",
     0 : "SUCCESS",
     1 : "ARGERR",
     2 : "ENVERR",
     3 : "TSTERR",
     4 : "USRERR",
     5 : "RUNERR",
     6 : "INIERR",
     7 : "PRCERR",
     8 : "SVRKLL",
     9 : "IOERR",
    10 : "LDERR",
    11 : "TMERR",
   127 : "SHFAILED",
   128 : "SIGNAL",
 128+1 : "SIGHUP",
 128+2 : "SIGINT",
 128+9 : "SIGKILL",
128+15 : "SIGTERM",
   255 : "EXCEPTION",
}

def gridlabd(*args,split:bool|str=None,**kwargs) -> str:
    """Run gridlabd and return the output

    Arguments:
    
    * `*args`: gridlabd command line arguments
    
    * `split`: split output using `split` value (uses `'\n'` if `True`)

    * `**kwargs`: gridlabd global definitions

    Returns:

    * `str`: stdout

    Exceptions:

    * `GridlabdRunnerException(code,stderr)`
    """
    gld = GridlabdRunner(*args,**kwargs)
    return gld.result.stdout if not split else gld.result.stdout.strip().split(split if type(split) is str else "\n")

class GridlabdRunner:
    """GridLAB-D runner class"""
    def __init__(self,*args,
            binary:bool = False,
            start:bool = True,
            wait:bool = True,
            timeout:float = None,
            source:str|TypeVar('io.BufferedIOBase') = None,
            **kwargs,
            ):
        """Construct a runner

        Arguments:
        
        * `*args`: gridlabd command line arguments
        
        * `binary`: use the gridlabd binary if possible
        
        * `start`: start gridlabd immediately
        
        * `wait`: wait for gridlabd to complete

        * `timeout`: seconds to wait for completion before failing
        
        * `source`: input data source
        
        * `**kwargs`: gridlabd global definitions

        Exceptions:

        * `GridlabdRunnerException(code,stderr)`
        """
        cmd = shutil.which("gridlabd.bin" if binary else "gridlabd")
        if not cmd:
            raise GridlabdRunnerException(-1,"gridlabd not found")
        self.command = [cmd]
        for name,value in kwargs.items():
            self.command.extend(["-D",f"{name}={value}"])
        self.command.extend(args)
        self.process = None
        self.result = None
        if not start:
            raise NotImplementedError("GridlabdRunner.start")
        elif not wait:
            raise NotImplementedError("GridlabdRunner.wait")
        else:
            if isinstance(source,str):
                source = io.StringIO(source)
            self.run(timeout=timeout,source=source)

    def run(self,timeout:float=None,source:TypeVar('io.BufferedIOBase')=None):
        """Run gridlabd

        Arguments:
        
        * `timeout`: seconds to wait before for completion failing

        * `source`: input source
        Returns:
        
        * `str`: output

        Exceptions:
        
        * `GridlabdRunnerException(code,message)`
        
        * `subprocess.TimeoutExpired`
        """
        try:
            self.result = subprocess.run(self.command, 
                capture_output = True, 
                text = True,
                timeout = timeout,
                input = source.read() if source else None,
                )
        except subprocess.TimeoutExpired:
            raise
        except:
            raise
        if self.result.returncode != 0:
            raise GridlabdRunnerException(f"gridlabd.{EXITCODES[self.result.returncode]} -- {self.result.stderr}" 
                if self.result.returncode in EXITCODES 
                else f"gridlabd.EXITCODE {self.result.returncode}") 
        return self.result.stdout

    def is_started(self) -> bool:
        """Check if gridlabd is started

        Returns:
        
        * `bool`: gridlabd is started
        """
        return not self.process is None

    def is_running(self) -> bool:
        """Check if gridlabd is running

        Returns:
        
        * `bool`: gridlabd is running
        """
        return not self.process is None and self.result is None
        
    def is_completed(self) -> bool:
        """Check if gridlabd is done

        Returns:
        
        * `bool`: process is completed
        """
        return not self.result is None

    def start(self,wait=True):
        """Start gridlabd

        Arguments:

        * `wait`: enable wait for completion
        """
        if self.is_completed():
            raise GridlabdRunnerException("already completed")
        if self.is_started():
            raise GridlabdRunnerException("already started")

    def wait(self,timeout=None):
        """Wait for gridlabd to complete

        Arguments:

        * `timeout`: wait timeout in seconds
        """
        if self.is_completed():
            raise GridlabdRunnerException("already completed")

if __name__ == '__main__':

    if not sys.argv[0]:
        import unittest

        class TestGridlabd(unittest.TestCase):

            def test_version(self):
                output = gridlabd("--version")
                self.assertTrue(output.startswith("Arras Energy"))

            def test_new(self):
                file = f"/tmp/{hex(random.randint(0,2**64-1))[2:]}.json"
                try:
                    output = gridlabd("-o",file)
                    self.assertTrue(os.path.exists(file))
                    with open(file,"r") as fh:
                        glm = json.load(fh)
                        self.assertEqual(glm["application"],"gridlabd")
                        ver = [int(x) for x in glm["version"].split(".")]
                        chk = [gld.version()[x] for x in ["major","minor","patch"]]
                        self.assertEqual(ver,chk)
                        self.assertEqual(len(glm["objects"]),0)
                except:
                    raise
                finally:
                    try:
                        os.remove(file)
                    except OSError:
                        pass

            def test_err(self):
                try:
                    output = gridlabd("--nogood")
                    msg = None
                except GridlabdRunnerException as err:
                    msg = err.args[0].split()
                self.assertGreater(len(msg),0)
                if len(msg) > 0:
                    self.assertEqual(msg[0],"gridlabd.RUNERR")

            def test_model(self):
                name = f"/tmp/{hex(random.randint(0,2**64-1))[2:]}"
                try:
                    gridlabd("model","get","IEEE/13","-o",f"{name}.glm")
                    gridlabd("-C",f"{name}.glm","-o",f"{name}.json",binary=True)
                except:
                    raise
                finally:
                    try:
                        os.remove(f"{name}.glm")
                    except OSError:
                        pass
                    try:
                        os.remove(f"{name}.json")
                    except OSError:
                        pass

            def test_input(self):
                result = gridlabd(".glm",source="#print hello")
                self.assertEqual(result,"/dev/stdin(1): hello\n")

            # def test_start(self):
            #     try:
            #         proc = GridlabdRunner("--version",start=False).start()
            #         msg = None
            #     except GridlabdRunnerException as err:
            #         msg = err
            #     self.assertEqual(msg.args[0],"already completed")

            # def test_wait(self):
            #     gld = GridlabdRunner("--version",wait=False)
            #     try:
            #         proc = gld.wait()
            #         msg = None
            #     except GridlabdRunnerException as err:
            #         msg = err
            #     self.assertEqual(msg.args[0],"already completed")

            # run = GridlabdRunner("8500.glm","clock.glm","recorders.glm")
            # run.start(wait=False)
            # while not run.result:
            #     print("STDOUT",run.output,file=sys.stdout,flush=True)
            #     print("STDERR",run.errors,file=sys.stderr,flush=True)
            #     time.sleep(1)
            # run.wait()

        unittest.main()

    else:

        print(f"ERROR [{os.path.split(sys.argv[0])[1]}]: not a command line tool",file=sys.stderr)
        exit(1)
