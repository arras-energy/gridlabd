"""GridLAB-D runner"""
import os, sys
import subprocess
import time
import shutil

class GridlabdException(Exception):
    pass

_exitcode = {
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

def gridlabd(*args,split=None,**kwargs):
    """Run gridlabd and return the output

    Arguments:
    - *args: gridlabd command line arguments
    - **kwargs: gridlabd global definitions

    Returns:
    - str: stdout

    Exceptions:
    - GridlabdException(code,stderr)
    """
    gld = Gridlabd(*args,**kwargs)
    return gld.result.stdout if not split else gld.result.stdout.strip().split(split if type(split) is str else "\n")

class Gridlabd:

    def __init__(self,*args,
            binary = False,
            start = True,
            wait = True,
            timeout = None,
            source = None,
            **kwargs,
            ):
        """Construct a runner

        Arguments:
        - *args=[]: gridlabd command line arguments
        - binary=True (bool=True): use the gridlabd binary if possible
        - start=True (bool): start gridlabd immediately
        - wait=True (bool): wait for gridlabd to complete
        - timeout=None (float): seconds to wait for completion before failing
        - source=None (bufferedio): input data source
        - **kwargs: gridlabd global definitions

        Exceptions:
        - GridlabdException(code,stderr)
        """
        cmd = shutil.which("gridlabd.bin")
        cmd = cmd if cmd and binary else shutil.which("gridlabd")
        if not cmd:
            raise GridlabdException(-1,"gridlabd not found")
        self.command = [cmd]
        for name,value in kwargs.items():
            self.command.extend(["-D",f"{name}={value}"])
        self.command.extend(args)
        self.process = None
        self.result = None
        if not start:
            raise NotImplementedError("Gridlabd.start")
        elif not wait:
            raise NotImplementedError("Gridlabd.wait")
        else:
            self.run(timeout=timeout,source=source)

    def run(self,timeout=None,source=None):
        """Run gridlabd

        Arguments:
        - timeout=None (float): seconds to wait before for completion failing

        Returns:
        - str: output

        Exceptions:
        - GridlabdException(code,message)
        - subprocess.TimeoutExpired
        """
        try:
            self.result = subprocess.run(self.command, 
                capture_output = True, 
                text = True,
                timeout = timeout,
                stdin = source,
                )
        except subprocess.TimeoutExpired:
            raise
        except:
            raise
        if self.result.returncode != 0:
            raise GridlabdException(f"gridlabd.{_exitcode[self.result.returncode]} -- {self.result.stderr}" 
                if self.result.returncode in _exitcode 
                else f"gridlabd.EXITCODE {self.result.returncode}") 
        return self.result.stdout

    def is_started(self):
        """Check if gridlabd is started

        Returns:
        bool: gridlabd is started
        """
        return not self.process is None

    def is_running(self):
        """Check if gridlabd is running

        Returns:
        bool: gridlabd is running
        """
        return not self.process is None and self.result is None
        
    def is_completed(self):
        """Check if gridlabd is done

        Returns:
        bool: process is completed
        """
        return not self.result is None

    def start(self,wait=True):
        """Start gridlabd"""
        if self.is_completed():
            raise GridlabdException("already completed")
        if self.is_started():
            raise GridlabdException("already started")

    def wait(self,timeout=None):
        """Wait for gridlabd to complete"""
        if self.is_completed():
            raise GridlabdException("already completed")

if __name__ == '__main__':

    import unittest

    class TestGridlabd(unittest.TestCase):

        def test_ok(self):
            output = gridlabd("--version")
            self.assertTrue(output.startswith("HiPAS GridLAB-D"))

        def test_err(self):
            try:
                output = gridlabd("--nogood")
                msg = None
            except GridlabdException as err:
                msg = err.args
            self.assertEqual(msg[0],5)

        # def test_start(self):
        #     try:
        #         proc = Gridlabd("--version",start=False).start()
        #         msg = None
        #     except GridlabdException as err:
        #         msg = err
        #     self.assertEqual(msg.args[0],"already completed")

        # def test_wait(self):
        #     gld = Gridlabd("--version",wait=False)
        #     try:
        #         proc = gld.wait()
        #         msg = None
        #     except GridlabdException as err:
        #         msg = err
        #     self.assertEqual(msg.args[0],"already completed")

        # run = Gridlabd("8500.glm","clock.glm","recorders.glm")
        # run.start(wait=False)
        # while not run.result:
        #     print("STDOUT",run.output,file=sys.stdout,flush=True)
        #     print("STDERR",run.errors,file=sys.stderr,flush=True)
        #     time.sleep(1)
        # run.wait()

    unittest.main()