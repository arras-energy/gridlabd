HOST="127.0.0.1" # port IP addr
PORT=5000 # server port
DEBUG=False # enable flask debugging
TIMEOUT=60 # run timeout in seconds
RETENTION=300 # session retention in seconds
CLEANUP=60 # session cleanup interval in seconds
TMPDIR="/tmp/gridlabd/rest_server" # path to session data
MAXFILE=2**32-1 # maximum file size
MAXLOG=2**10
LOGFILE=TMPDIR+"/server.log"#"/dev/stderr" # logger output
SSL_CONTEXT=None # "adhoc" or ('cert.pem', 'key.pem')