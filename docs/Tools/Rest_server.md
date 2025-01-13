[[/Tools/Rest_server]] -- GridLAB-D REST API Server

# Synopsis

Shell:
~~~
gridlabd rest_server COMMAND [OPTIONS ...] 
~~~

## Commands

  * `start`: Start server
  * `status`: Show server status
  * `stop`: Stop server
  * `help`: Show this documentation

## Options

  * `-h|--help`: Show this documentation

  * `--timeout=INTEGER`: Set the simulation runtime limit in seconds (default None)

  * `--retention=INTEGER`: Set the result retention time in seconds (default None)

  * `--clean=INTEGER`: Set the retention cleanup interval in seconds (default None)

  * `--tmpdir=PATH`: Set the temporary storage folder (default /tmp/gridlabd/rest_server)

  * `--maxfile=INTEGER`: Set the maximum upload file s (default is 1GB)

  * `--logfile=PATHNAME`: Set the logfile name (default TMPDIR+"/server.log")

  * `--ssl_context=STRING`: Set the SSL context per Fla (default is None) 

# Description

The GridLAB-D REST server provides gridlabd simulation control through a Flask API. The API Spec can be obtained using the endpoint `/api/spec.html` or `/api/spec.json`.

# See also

* [[/Tools/Rest_client]]
