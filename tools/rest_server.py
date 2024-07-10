"""GridLAB-D REST API Server

Syntax: gridlabd rest_server COMMAND [OPTIONS ...] 

Commands:

    start   Start server
    status  Show server status
    stop    Stop server
    help    Show this documentation

Options:

    -h|--help             Show this documentation

    --timeout=INTEGER     Set the simulation runtime limit in seconds
                          (default None)

    --retention=INTEGER   Set the result retention time in seconds
                          (default None)

    --clean=INTEGER       Set the retention cleanup interval in seconds
                          (default None)

    --tmpdir=PATH         Set the temporary storage folder
                          (default /tmp/gridlabd/rest_server)

    --maxfile=INTEGER     Set the maximum upload file size
                          (default is 1GB)

    --logfile=PATHNAME    Set the logfile name (default TMPDIR+"/server.log")

    --ssl_context=STRING  Set the SSL context per Flask documentation
                          (default is None) 

The GridLAB-D REST server provides gridlabd simulation control through a Flask
API.
"""

import os, sys
import shutil, signal, stat
import logging
import subprocess as sp
import socket
import json
from datetime import datetime
from time import time, sleep
from random import randint
from flask import Flask, request
from flask.json import jsonify
import atexit
import errno
import http
from flask_restful import  Api
from flask_restful_swagger import swagger

app = Flask("gridlabd")
api = swagger.docs(Api(app), apiVersion='0')

# Read configuration file (if any)
try:
    from rest_server_config import *
except:
    HOST="127.0.0.1"
    PORT=5000
    TOKEN = None # Automatically generate access token
    DEBUG=False
    TIMEOUT = 60 # run timeout in seconds
    RETENTION = 3600 # session retention in seconds
    CLEANUP = 5 # session cleanup interval in seconds
    TMPDIR = "/tmp/gridlabd/rest_server" # path to session data
    MAXFILE = 2**32 - 1 # maximum file size
    LOGFILE = TMPDIR+"server.log" # logger output
    MAXLOG = 2**20 # maximum logfile size
    SSL_CONTEXT = None # "adhoc" or ('cert.pem', 'key.pem')

#
# Generation security token
#
if not "TOKEN" in globals() or not TOKEN:
    TOKEN=hex(randint(0,2**64))[2:]

class Session():
    """Session implementation"""

    def __init__(self,session=None,create=False):
        """Session constructor

        Parameters
        ----------

            session (hex): session identifier (client provided)

            create (bool): enable creation of session
        """

        # check for valid session id
        if not int(session,16) > 0:
            raise Exception("invalid session id")

        # session id is valid
        self.sid = session

        # check if session exists
        if not self.exists():

            if create: 
                # session create requested
                os.makedirs(self.cwd(),exist_ok=True)

            else: 

                # no such session
                raise FileNotFoundError("no session")

        elif create: 

            # session exists and cannot be created
            raise FileExistsError("session exists")

    def __str__(self):
        """Make string from session"""
        return self.sid

    def exists(self):
        """Check if session exists"""
        return os.path.exists(self.cwd())

    def cwd(self):
        """Get session storage folder"""
        return os.path.join(TMPDIR,self.sid)

    def file(self,name,mode=None):
        """Access session file"""
        if mode is None:
            return os.path.join(self.cwd(),name)
        else:
            return open(self.file(name),mode)

    def close(self):
        """Close session"""
        shutil.rmtree(self.cwd())

    def run(self,*args,wait=True,output=False):
        """Run GridLAB-D in a session"""
        try:

            if not wait:
                pid = os.fork()
                if pid > 0: # parent process
                    return dict(
                        status = "OK",
                        content = dict(
                            process = os.fork(),
                            ),
                        )

            # start timer
            tic = time()

            # dispatch simulation
            result = sp.run(["gridlabd"]+list(args),
                cwd=self.cwd(),
                capture_output=True,
                timeout=TIMEOUT,
                )

            # stop timer
            toc = time()

            # report status
            status = "OK"

        except sp.TimeoutExpired:

            # timeout
            status = "TIMEOUT"

        # store outputs
        if output:
            return dict(
                status=status if result.returncode==0 else "ERROR",
                content=dict(
                    returncode=result.returncode,
                    runtime=round(toc-tic,3),
                    stdout=result.stdout.decode("utf-8"),
                    stderr=result.stderr.decode("utf-8"),
                    ),
                )

        with self.file("stdout","w") as fh:
            fh.write(result.stdout.decode("utf-8"))
        with self.file("stderr","w") as fh:
            fh.write(result.stderr.decode("utf-8"))

        if not wait:
            exit(0)

        # return results
        return dict(
            status=status if result.returncode==0 else "ERROR",
            content=dict(
                returncode=result.returncode,
                runtime=round(toc-tic,3),
                ),
            )

#
# API Routes
#

# Session open
@app.route(f"/{TOKEN}/<string:session>/open")
def app_open(session):
    try:
        session = Session(session,create=True)
        return jsonify(dict(status="OK",content=dict(retention=RETENTION)))
    except Exception as err:
        log.error(f"app_open(session={session}):{str(err)}")
        return jsonify(dict(status="ERROR",message=str(err))),http.HTTPStatus.BAD_REQUEST

# Session run
@app.route(f"/{TOKEN}/<string:session>/run/<string:command>")
def app_run(session,command):
    try:
        session = Session(session)
        args = command.split()
        result = session.run(*args)
        log.info(f"app_run(session={session}),command='{command}':exit({result['content']['returncode']})")
        return jsonify(result),http.HTTPStatus.OK
    except Exception as err:
        log.error(f"app_run(session={session},command='{command}'):{str(err)}")
        return jsonify(dict(status="ERROR",message=str(err))),http.HTTPStatus.BAD_REQUEST

# Session start
@app.route(f"/{TOKEN}/<string:session>/start/<string:command>")
def app_start(session,command):
    try:
        session = Session(session)
        args = command.split()
        result = session.run(*args,wait=False)
        log.info(f"app_start(session={session}),command='{command}':exit({result['content']['process']})")
        return jsonify(dict(status="OK",content=result)),http.HTTPStatus.OK
    except Exception as err:
        log.error(f"app_start(session={session},command='{command}'):{str(err)}")
        return jsonify(dict(status="ERROR",message=str(err))),http.HTTPStatus.BAD_REQUEST

# Session status
@app.route(f"/{TOKEN}/<string:session>/status/<int:process>")
def app_status(session,process):
    try:
        session = Session(session)
        # result = [x.split() for x in session.run("--pstatus",output=True)["stdout"].split("\n")]
        # result = [x.split() for x in session.run("--pstatus",output=True)["content"]["stdout"].split("\n")]
        # result = dict([(x[1],x[2:]) for x in result])
        result = session.run("--pstatus",output=True)
        if result["status"] == "OK":
            print("result = ",result,file=sys.stderr)
            result = [x.split() for x in result["content"]["stdout"].split("\n")]
            print("result = ",result,file=sys.stderr,flush=True)
            result = dict([(int(x[1]),[x[3],x[4]]) for x in result if len(x) > 4])
            print("result = ",result,file=sys.stderr,flush=True)
            if process in result:
                result = dict(status="OK",content=dict(zip(["progress","state"],result[process])))#[(x[1],x[2:]) for x in result])
            else:
                result = dict(status="OK",content=dict(state="Done",progress="100%"))
        return jsonify(result),http.HTTPStatus.OK
    except Exception as err:
        log.error(f"app_start(session={session}):{str(err)}")
        return jsonify(dict(status="ERROR",message=str(err))),http.HTTPStatus.BAD_REQUEST        

# Session files
@app.route(f"/{TOKEN}/<string:session>/files/")
def app_root(session):
    return app_files(session,".")

# Session files with path
@app.route(f"/{TOKEN}/<string:session>/files/<path:path>")
def app_files(session,path):
    try:
        session = Session(session)
        content = {}
        if not path:
            path = "."
        for file in os.listdir(os.path.join(session.cwd(),path)):
            info = os.lstat(os.path.join(session.cwd(),path,file))
            content[file] = {
                "type" : "D" if stat.S_ISDIR(info.st_mode) else "F",
                "size" : len(os.listdir(os.path.join(session.cwd(),path,file))) if stat.S_ISDIR(info.st_mode) else info.st_size,
            }
        return jsonify(dict(status="OK",content=content)),http.HTTPStatus.OK
    except Exception as err:
        log.error(f"app_files(session={session}):{str(err)}")
        return jsonify(dict(status="ERROR",message=str(err))),http.HTTPStatus.BAD_REQUEST

# Session upload
@app.route(f"/{TOKEN}/<string:session>/upload",methods=["POST"])
def app_upload(session):
    try:
        session = Session(session)
        result = {}
        for name,data in request.files.items():
            filepath = os.path.join(TMPDIR,session.cwd(),name) 
            data.save(filepath)
            size = os.lstat(filepath).st_size
            result[name] = dict(size=size)
            log.info(f"upload:filename={name}:size={size}")
        return jsonify(dict(status="OK",content=result))
    except Exception as err:
        log.error(f"app_upload(session={session}):{str(err)}")
        return jsonify(dict(status="ERROR",message=str(err))),http.HTTPStatus.BAD_REQUEST

# Session download
@app.route(f"/{TOKEN}/<string:session>/download/<string:name>")
def app_download(session,name):
    try:
        session = Session(session)
        with session.file(name,"r") as fh:
            return jsonify(status="OK",content="".join(fh.readlines()))
    except Exception as err:
        log.error(f"app_download(session={session},name='{name}'):{str(err)}")
        return jsonify(dict(status="ERROR",message=str(err))),http.HTTPStatus.BAD_REQUEST

# Session close
@app.route(f"/{TOKEN}/<string:session>/close")
def app_close(session):
    try:
        session = Session(session)
        session.close()
        return jsonify(dict(status="OK",content={})),http.HTTPStatus.OK
    except Exception as err:
        log.error(f"app_close(session={session}):{str(err)}")
        return jsonify(dict(status="ERROR",message=str(err))),http.HTTPStatus.BAD_REQUEST

#
# Main processing
#
if __name__ == "__main__":

    # Configure app
    app.config['MAX_CONTENT_LENGTH'] = MAXFILE

    # Default command
    COMMAND = 'status'

    # Argument processing
    if len(sys.argv) == 1:
        print([x for x in __doc__.split("\n") if x.startswith("Syntax: ")][0],file=sys.stderr)
        exit(errno.EINVAL)
    del sys.argv[0]
    for n,arg in enumerate(sys.argv):
        if "=" in arg:
            key,value = arg.split("=")
        else:
            key,value = arg,None
        if key in ["-h","--help","help"]:
            print(__doc__)
            exit(0)
        elif key in ["--timeout"]:
            TIMEOUT=int(value) if value else None
        elif key in ["--retention"]:
            RETENTION=int(value) if value else None
        elif key in ["--cleanup"]:
            CLEANUP=int(value) if value else None
        elif key in ["--tmpdir"]:
            TMPDIR=value if value else "."
        elif key in ["--maxfile"]:
            MAXFILE=int(value) if value else 2**64-1
        elif key in ["--logfile"]:
            LOGFILE=value if value else "/dev/stderr"
        elif key in ["--ssl_context"]:
            SSL_CONTEXT=value.split(",") if "," in value else ( value if value else None )
        elif key in ["status","start","stop"]:
            COMMAND = key
        else:
            raise Exception(f"'{arg}' is an invalid option")

    # Setup logging
    os.makedirs(TMPDIR,exist_ok=True)
    log = logging.getLogger("gridlabd")
    logging.basicConfig(
        filename=LOGFILE,
        encoding='utf-8',
        level=logging.DEBUG,
        )

    # Setup session retention and log file rotation
    if not RETENTION is None:
        def on_sigalrm(signum,frame):
            global log
            signame = signal.Signals(signum).name
            for sid in os.listdir(TMPDIR):
                pathname = os.path.join(TMPDIR,sid)
                fileinfo = os.stat(pathname)
                age = time() - fileinfo.st_atime
                if age > RETENTION:
                    try:
                        session = Session(sid)
                        session.close()
                        log.info(f"delete session {sid} idle for {age} seconds")
                    except:
                        pass
            if os.lstat(LOGFILE).st_size > MAXLOG:
                name = LOGFILE+datetime.now().strftime("-%Y%m%d-%H%M%S")
                shutil.copyfile(LOGFILE,name)
                open(LOGFILE,"w").close()
                log.info(f"rotated log into {name}")
            signal.alarm(CLEANUP)
        signal.signal(signal.SIGALRM,on_sigalrm)
        signal.alarm(CLEANUP)

    def set_server_info(**kwargs):
        """Set server info"""
        with open(os.path.join(TMPDIR,"server.info"),"w") as fh:
            json.dump(kwargs,fh,indent=4)

    def get_server_info():
        """Get server info"""
        try:
            with open(os.path.join(TMPDIR,"server.info"),"r") as fh:
                return json.load(fh)
        except FileExistsError:
            return None

    def check_server():
        """Check server"""
        try:
            info = get_server_info()
            os.kill(info["pid"],0)
        except OSError:
            return False
        else:
            return True

    # Command processing
    if COMMAND == 'start':

        if os.fork() > 0:
            sleep(1)
            exit(0)

        # Check server status
        if check_server():

            # Already running
            print(f"ERROR: server is already started {get_server_info()}",file=sys.stderr)
            exit(errno.EEXIST) # errno EEXIST

        # Setup the exit handler
        def on_exit(*args,**kwargs):
            os.unlink(os.path.join(TMPDIR,"server.info"))
            log.info(f"*** STOP ***")

        # Register the exit handler
        atexit.register(on_exit)

        # Start logging
        log.info(f"*** START ***")
        log.info(f"starting:{datetime.now()}")
        log.info(f"hostname:{socket.gethostname()}")

        # Check if server all interfaces
        if HOST == '0.0.0.0':

            # Get the actual interface IP address
            HOST = socket.gethostbyname(socket.gethostname())

        # Construct, report, and save the URL that clients will use
        URL = f"{'https' if SSL_CONTEXT else 'http'}://{HOST}:{PORT}/{TOKEN}"
        print(URL,flush=True)
        log.info(f"URL:{URL}")
        set_server_info(url=URL,pid=os.getpid())

        # Setup the Ctrl-C handler
        last_sigint = 0
        def on_sigint(signum,frame):
            global last_sigint
            if time()-last_sigint < 1:
                log.info(f"*** SIGINT ***")
                exit(errno.EINTR) # E_INTR
            else:
                last_sigint = time()
                print("Interrupt received. Send SIGINT twice within 1 second to interrupt server.",file=sys.stderr,flush=True)
        signal.signal(signal.SIGINT,on_sigint)

        # Setup the terminate and hang-up signal handlers
        signal.signal(signal.SIGTERM,lambda x,y:exit(errno.EINTR))
        signal.signal(signal.SIGHUP,lambda x,y:exit(errno.EINTR))

        app.run(ssl_context=SSL_CONTEXT,host=HOST,port=PORT,debug=DEBUG)

    elif COMMAND == 'stop':

        if check_server():
            pid = get_server_info()["pid"]
            os.kill(pid,signal.SIGTERM)

    elif COMMAND == 'status':

        if check_server():
            info = get_server_info() 
            info["status"] = "up"
        else:
            info = {"status" : "down"}
        print(json.dumps(info))
