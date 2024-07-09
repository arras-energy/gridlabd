"""GridLAB-D REST API Client
"""

import os, sys
import json
import requests
import random
from datetime import datetime

try:
    from rest_server_config import TMPDIR
except:
    TMPDIR="/tmp/gridlabd/rest_server"

def get_server_info():
    """Get server info"""
    try:
        with open(os.path.join(TMPDIR,"server.info"),"r") as fh:
            return json.load(fh)
    except FileExistsError:
        return None

def server_get(*args,**kwargs):
    """Server GET query"""
    req = requests.get(os.path.join(URL,*args),**kwargs)
    if req.status_code != 200:
        raise Exception(f"HTTP error {req.status_code}")
    data = json.loads(req.content.decode('utf-8'))
    if data["status"] != "OK":
        raise Exception(data["message"])
    return data["content"]

def server_post(*args,**kwargs):
    """Server POST query"""
    req = requests.post(os.path.join(URL,*args),files=kwargs)
    if req.status_code != 200:
        raise Exception(f"HTTP error {req.status_code}")
    data = json.loads(req.content.decode('utf-8'))
    if data["status"] != "OK":
        raise Exception(data["message"])
    return data["content"]

URL = get_server_info()["url"]

class Session:
    """Session client implementation"""
    def __init__(self,session=None):
        """Open session

        Parameters:

            session (hex): Session id (None for new)
        """
        self.sid = session if session else hex(random.randint(1,2**32))[2:]
        self.status = server_get(self.sid,"open")
        self.created_on = datetime.now()

    def close(self):
        """Close session"""
        return server_get(self.sid,"close")

    def run(self,*args,**kwargs):
        """Run command

        Parameters:

            *args (str list): gridlabd command
            **kwargs (str list): requests GET options
        """
        return server_get(self.sid,"run"," ".join(args),**kwargs)

    def start(self,*args,**kwargs):
        """Run command

        Parameters:

            *args (str list): gridlabd command
            **kwargs (str list): requests GET options
        """
        return server_get(self.sid,"start"," ".join(args),**kwargs)

    def progress(self,*args,**kwargs):
        """Run command

        Parameters:

            *args (str list): gridlabd command
            **kwargs (str list): requests GET options
        """
        return server_get(self.sid,"status"," ".join([str(x) for x in args]),**kwargs)

    def files(self,path=""):
        """Get list of files

        Parameters:

            path (str): folder to list (default "")
        """
        return server_get(self.sid,"files",path)

    def download(self,*args):
        """Download a file

        Parameters:

            *args (str list): file name to download
        """
        result = {}
        for file in args:
            result[file] = server_get(self.sid,"download",file)
        return result

    def upload(self,name,fh):
        """Upload a file

        Parameters:
            
            name (str): file name to upload

            fh (file handle): open file handle
        """
        kwargs = {name:fh}
        return server_post(self.sid,"upload",**kwargs)

if __name__ == "__main__":

    session = Session()
    print("Session",session.sid,"created on",session.created_on,"status",session.status)
    print(session.upload("test.txt",open("rest_client.py","r")))
    print(session.run("version"))
    print(session.files())
    print(session.download("stdout"))
    print(session.download("stderr"))
    print(session.download("test.txt"))
    result = session.start("--version=all")
    print(result)
    print(session.progress(result["content"]["process"]))
    print(session.close())
