[[/GLM/Global/Tmpfile]] -- Get a temporary filename

# Synopsis

~~~
${TMPFILE TAG}
~~~

# Description

Create and access a temporary file using a tag.  The file is deleted when the GridLAB-D run is completed.  The file is located in the `TMPDIR` or `TMP` or `/tmp` folder, whichever is found first. The file naming convention is `gridlabd_tmp_HOSTNAME_PID_NAME.EXT, where

  - `HOSTNAME` is the name of the local host machine
  - `PID` is the process ID of the current gridlabd run
  - `NAME` is the tag name
  - `EXT` is the tag type

If `TAG` has the format `EXT:NAME` these are used in constructing the file name, otherwise `NAME` is set to `TAG`.

# Example

Create the file `/tmp/test.glm`:

~~~
#print ${TMPFILE py:A}
#exec ls ${TMPFILE py:A}
~~~

Run the following command:

~~~
export TMP=/tmp
gridlabd /tmp/test.glm
ls /tmp/gridlabd*
~~~

Output:

~~~
/tmp/test.glm(1): /tmp/gridlabd_tmp_MacBook_Pro_2_local_10391_A.py
/tmp/gridlabd_tmp_MacBook_Pro_2_local_10391_A.py
/tmp/gridlabd-pmap-4
~~~
