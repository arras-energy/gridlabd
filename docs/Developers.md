Software developers and engineers are welcome to contribute to Arras Energy. The source code to HiPAS GridLAB-D is available to the public through the [GitHub HiPAS GridLAB-D project](https://source.gridlabd.us/). 

## Developer Resources

  - [Source code](https://source.gridlabd.us/)
  - [Issues](https://source.gridlabd.us/issues)
  - [Pull requests](https://source.gridlabd.us/pulls)
  - [Projects](https://source.gridlabd.us/projects)
  - [Wiki](https://source.gridlabd.us/wiki)
  - [Discussions](https://source.gridlabd.us/discussions)

Developers should consult the [[/Developer/README]] for information about modifying and contributing to Arras Energy.

# Installing Arras Energy from source code

You can set up your system to host development and build GridLAB-D from source code using the installation script. 

~~~
bash$ git clone https://source.gridlabd.us/ gridlabd
bash$ cd gridlabd
bash$ ./install.sh
~~~

This script supports the most common Linux/Unix platforms.  If your platform is not supported, please consult the developer guide at [[/Developer/README]].

# Validating an Arras Energy installation

Once you have completed installation, you should validate your system before beginning software development.

~~~
bash$ gridlabd --validate
~~~

If you observe any validation failures, please consult the [[/Developer/README]] for further guidance.
