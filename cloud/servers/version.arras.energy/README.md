# AWS EC2 Setup Procedure

1. Create a new t2micro EC2 instance
2. Open a shell and run the following command

   curl https://code.arras.energy/${BRANCH}/cloud/servers/version.arras.energy/install.sh | bash

By default the script pulls from the master branch. To change
which branch is used for the source set the BRANCH environment
variable to the name of the source branch, e.g.,

   export BRANCH=develop
   curl https://code.arras.energy/${BRANCH}/cloud/servers/version.arras.energy/install.sh | bash

# Reading version check log

The version check log may be read at http://version.arras.energy/access.csv.
