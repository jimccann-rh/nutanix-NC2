#!/usr/bin/env python3
import codecs
import hashlib
import hmac
import logging
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from clusternutanix import nc2_cluster_status
from clusternutanixvm import pcvm_status

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def nc2_bear_status(bear):
    """To wake up the "bear" cluster or put the "bear" cluster to sleep this will also toggle the prism central vm to be power on or off"""
    ncs = nc2_cluster_status()

    # load the script configuration
    env_path_env = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path_env)
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    CLUSTER_ID = os.getenv("CLUSTER_ID")
    DOMAIN = os.getenv("DOMAIN")
    OUTPUT = os.getenv("OUTPUT")

    # load the script configuration
    env_path_nc2 = Path(OUTPUT) / "NC2clusterinfo.txt"
    load_dotenv(dotenv_path=env_path_nc2)
    # trunk-ignore(flake8/F841)
    PE_IP = os.getenv("PE_IP")
    # trunk-ignore(flake8/F841)
    AHV = os.getenv("AHV")
    # trunk-ignore(flake8/F841)
    CVM = os.getenv("CVM")
    VER = os.getenv("VER")

    if VER >= "6.0.1.1":

        # Create signature
        timestamp = int(time.time())
        to_sign = "%s%s" % (timestamp, CLIENT_ID)
        signature = hmac.new(
            codecs.encode(CLIENT_SECRET),
            msg=codecs.encode(to_sign),
            digestmod=hashlib.sha256,
        ).hexdigest()

        # Prepare http request headers
        headers = {
            "X-Frame-ClientId": CLIENT_ID,
            "X-Frame-Timestamp": str(timestamp),
            "X-Frame-Signature": signature,
        }

        # hibernate_req = requests.post(DOMAIN + "/v1/clusters/" + CLUSTER_ID + "/" + bear, headers=headers)
        # hibernate_req = requests.post(DOMAIN + "/v1/clusters/" + CLUSTER_ID + "/resume_cluster", headers=headers)

        logging.info(headers)
        # logging.info(hibernate_req)
        # logging.info(hibernate_req.json())

        # https://docs.frame.nutanix.com/frame-apis/admin-api/admin-api.html
        # https://cpanel-backend-prod.frame.nutanix.com/api/v1/docs/clusters/index.html#/

        if bear == "resume_cluster":
            # query status of cluster
            hibernate_req = requests.post(
                DOMAIN + "/v1/clusters/" + CLUSTER_ID + "/" + bear, headers=headers
            )
            # logging.info(hibernate_req)
            # logging.info(hibernate_req.json())
            while (
                (ncs == "hibernated")
                or (ncs == "starting_nodes")
                or (ncs == "starting_services")
                or (ncs == "resuming")
                or (ncs == "starting")
            ):
                print("***" + ncs + "***")
                time.sleep(60)
            else:
                while ncs == "resume_failed":
                    print(
                        "***BAD "
                        + ncs
                        + " BAD*** TAKING COUNTER MEASURES!!!!"
                    )
                    time.sleep(600)

                    """The code area below is in development"""
                    # ~/cluster/bin$ python resume_hibernate_resume --workflow=resume
                    # dir = os.getcwd()
                    # print(dir)
                    # ping to see if cluster IP is up it should come up after the cluster is online
                    # cmd = ['ping', '-c2', '-W 5', PE_IP ]
                    #
                    #
                    # cmd = ['ssh', '-i /home/jimb0/nutanix-NC2-/development-sts.pem', 'ec2-user@3.129.209.238', 'allssh genesis restart;','allssh genesis stop prism;','cluster start']
                    # cmd = ["ssh -i /home/jimb0/nutanix-NC2-/development-sts.pem ec2-user@3.129.209.238 'allssh genesis restart; allssh genesis stop prism; cluster start'"]
                    # cmd = ["ssh -i /home/jimb0/nutanix-NC2-/development-sts.pem ec2-user@3.129.209.238 'cm.sh'"]
                    # response = subprocess.Popen("ssh -i /home/jimb0/nutanix-NC2-/development-sts.pem {user}@{host} {cmd}".format(user='ec2-user', host='3.129.209.238', cmd='allssh genesis restart; allssh genesis stop prism; cluster start'), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                    # stdout, stderr = response.communicate()

                    # print(response)
                    # print(response.communicate())
                    # print(cmd)
                    # done = False
                    # time.sleep(10)
                    # timeout = 10 # default time out after 1000 times, set to -1 to disable timeout

                    # logging.info("Waiting for cluster IP to come on-line.")

                    # while not done and timeout:
                    #    response = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                    #    stdout, stderr = response.communicate()
                    #    if response.returncode == 0:
                    #        print("Server up!")
                    #        done = True
                    #    else:
                    #        sys.stdout.write('.')
                    #        timeout -= 1
                # if not done:
                #    logging.info("\nCluster failed to respond")
                """'Code above is in active development"""

                while (
                    (ncs == "hibernated")
                    or (ncs == "starting_nodes")
                    or (ncs == "starting_services")
                    or (ncs == "resuming")
                    or (ncs == "starting")
                ):
                    print("***" + ncs + "***")
                    time.sleep(60)

            pcvm_status(TRANSITION_PAYLOAD="ON")

        elif bear == "hibernate":
            # query status of cluster
            pcvm_status(TRANSITION_PAYLOAD="ACPI_SHUTDOWN")
            hibernate_req = requests.post(
                DOMAIN + "/v1/clusters/" + CLUSTER_ID + "/" + bear, headers=headers
            )
            logging.debug(hibernate_req)
            # logging.info(hibernate_req.json())
            while (
                (ncs == "running")
                or (ncs == "hibernating")
                or (ncs == "stopping_nodes")
                or (ncs == "stopping_services")
                or (ncs == "resuming")
            ):
                print("***" + ncs + "***")
                time.sleep(60)
        else:
            print("no valid parm set (resume_cluster,hibernate)")


if __name__ == "__main__":
    # nc2_bear_status()
    locals().get(
        sys.argv[2],
        "parameter *resume_cluster* or *hibernate* and function *nc2_bear_status* not found",
    )(sys.argv[1])
