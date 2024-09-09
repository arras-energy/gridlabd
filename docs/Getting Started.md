Arras Energy is a commercial version of GridLAB-D.

# Docker 

The preferred method for running GridLAB-D is using [Docker](www.docker.org).  Once you have installed Docker, you can run GridLAB-D as follows.

~~~
bash% docker run -it arras-energy/gridlabd:latest gridlabd <filename>
~~~

where `<filename` is the name of the model file in the container that you wish to run.

If you wish to access the files in the current folder while running GridLAB-D in a container, then use the command

~~~
bash% docker run -vit $PWD:$PWD arras-energy/gridlabd:latest gridlabd -W $PWD <filename>
~~~

More information on using GridLAB-D docker containers can be found at [[/Install/Docker]].

# GitHub Tutorials

You can find tutorial on using GridLAB-D with GitHub projects at https://github.com/gridlabd-tutorials
