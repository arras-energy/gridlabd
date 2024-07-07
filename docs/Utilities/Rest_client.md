[[/Utilities/Rest_client]] -- REST API Client

# Synopsis

Python:

~~~
import rest_client
client = Session()
client.upload(FILENAME,FH)
client.run(COMMAND[,OPTIONS[,...]])
client.files([FOLDER])
client.download(PATHNAME)
client.close()
~~~

# Description

The REST API client provide a convenience class to access a `gridlabd rest_server` running on a local or remote host.  By default the client accesses the local host without need to identify the server access token. If you are accessing a remote host, you must specify the `client.URL`, including the access token, e.g., `http://SERVER:PORT/TOKEN`.

# See also

* [[/Utilities/Rest_server]]
