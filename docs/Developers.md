Software developers and engineers are welcome to contribute to Arras Energy. The source code to HiPAS GridLAB-D is available to the public through the [GitHub HiPAS GridLAB-D project](https://source.arras.energy/).

## Developer Resources

  - [Source code](https://source.arras.energy/)
  - [Issues](https://source.arras.energy/issues)
  - [Pull requests](https://source.arras.energy/pulls)
  - [Projects](https://source.arras.energy/projects)
  - [Wiki](https://source.arras.energy/wiki)
  - [Discussions](https://source.arras.energy/discussions)

Developers should consult the [[/Developer/README]] for information about modifying and contributing to Arras Energy.

# Installing Arras Energy from source code

You can set up your system to host development and build GridLAB-D from source code using the installation script.

~~~
bash$ git clone https://source.arras.energy/ gridlabd
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
