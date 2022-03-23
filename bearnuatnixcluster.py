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
    nc2_cluster_status()

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
                (nc2_cluster_status() == "hibernated")
                or (nc2_cluster_status() == "starting_nodes")
                or (nc2_cluster_status() == "starting_services")
                or (nc2_cluster_status() == "resuming")
                or (nc2_cluster_status() == "starting")
            ):
                print("***" + nc2_cluster_status() + "***")
                time.sleep(60)
            else:
                while nc2_cluster_status() == "resume_failed":
                    print(
                        "***BAD "
                        + nc2_cluster_status()
                        + " BAD*** TAKING COUNTER MEASURES!!!!"
                    )
                    time.sleep(600)

                    """The code area below is in development"""
                    # ~/cluster/bin$ python resume_hibernate_resume --workflow=resume

                """'Code above is in active development"""

                while (
                    (nc2_cluster_status() == "hibernated")
                    or (nc2_cluster_status() == "starting_nodes")
                    or (nc2_cluster_status() == "starting_services")
                    or (nc2_cluster_status() == "resuming")
                    or (nc2_cluster_status() == "starting")
                ):
                    print("***" + nc2_cluster_status() + "***")
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
                (nc2_cluster_status() == "running")
                or (nc2_cluster_status() == "hibernating")
                or (nc2_cluster_status() == "stopping_nodes")
                or (nc2_cluster_status() == "stopping_services")
                or (nc2_cluster_status() == "resuming")
            ):
                print("***" + nc2_cluster_status() + "***")
                time.sleep(60)
        else:
            print("no valid parm set (resume_cluster,hibernate)")


if __name__ == "__main__":
    # nc2_bear_status()
    locals().get(
        sys.argv[2],
        "parameter *resume_cluster* or *hibernate* and function *nc2_bear_status* not found",
    )(sys.argv[1])
