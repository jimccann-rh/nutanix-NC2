# nutanix-NC2-

Nutanix Cluster scripts

./bearnuatnixcluster.py --help

./bearnuatnixcluster.py --bear resume_cluster
./bearnuatnixcluster.py --bear hibernate

This will take care of the prism central VM as well

At this time you will need to VPN into "cluster" network to be able to talk to prism element (unless prism element IP is public)

For using docker look at the copy commands and make sure those same files are in the root of the docker directory. There is a seprate env.list file for docker vs the .env for non docker use.

docker command './runit.sh clusternutanix.py' or './runit.sh ./bearnuatnixcluster.py --bear hibernate'

Output should be in the output dir.
