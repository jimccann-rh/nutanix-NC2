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

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# load the script configuration
env_path_env = Path(".") / ".env"
load_dotenv(dotenv_path=env_path_env)
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CLUSTER_ID = os.getenv("CLUSTER_ID")
DOMAIN = os.getenv("DOMAIN")
OUTPUT = os.getenv("OUTPUT")


def check_key_exist(test_dict, key):
    try:
        value = test_dict[key]
        logging.info(value)
        return True
    except KeyError:
        return False


def nc2_cluster_status(): # noqa: max-complexity=12
    """Get hibernation/running status of cluster"""
    logging.info("Getting hibernation status of cluster %s", (CLUSTER_ID))

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

    try:
        hibernate_req = requests.get(
            DOMAIN + "/v1/clusters/" + CLUSTER_ID, headers=headers
        )
        hibernate_req.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.exception("Http Error: " + str(errh))
    except requests.exceptions.ConnectionError as errc:
        logging.exception("Error Connecting: " + str(errc))
    except requests.exceptions.Timeout as errt:
        logging.exception("Timeout Error: " + str(errt))
    except requests.exceptions.RequestException as err:
        logging.exception("Ops: Something went really wrong " + str(err))

    jsonResponse = hibernate_req.json()
    logging.debug("Print each key-value pair from JSON response")
    for key, value in jsonResponse.items():
        logging.debug('%r, ":", %r', key, value)

    logging.info(
        "what state is the cluster "
        + jsonResponse["name"]
        + " with ID "
        + jsonResponse["id"]
        + " in? "
        + jsonResponse["cluster_state"]
    )

    i = 0
    data = ""
    dataahv = ""
    datacvm = ""
    while i < len(jsonResponse["hosts"]):
        logging.info("***")
        logging.info(
            "AHV "
            + jsonResponse["hosts"][i]["ahv_ip"]
            + " "
            + jsonResponse["hosts"][i]["name"]
            + " "
            + jsonResponse["hosts"][i]["host_state"]
        )
        # if node hibernated cvm state will be none.
        if (
            (jsonResponse["cluster_state"] != "starting")
            and (jsonResponse["cluster_state"] != "resuming")
            and (jsonResponse["cluster_state"] != "hibernated")
        ):

            logging.info(
                "CVM "
                + jsonResponse["hosts"][i]["cvm_ip"]
                + " "
                + jsonResponse["hosts"][i]["cvm_service_status"]
            )
        else:
            logging.info("CVM " + jsonResponse["hosts"][i]["cvm_ip"])

        logging.info("***")
        data += "AHV" + str(i) + "=" + jsonResponse["hosts"][i]["ahv_ip"] + "\n"
        data += "CVM" + str(i) + "=" + jsonResponse["hosts"][i]["cvm_ip"] + "\n"
        dataahv += jsonResponse["hosts"][i]["ahv_ip"] + " "
        datacvm += jsonResponse["hosts"][i]["cvm_ip"] + " "
        i += 1
    dataver = jsonResponse["desired_aos_version"]
    logging.debug(dataahv)
    logging.debug(datacvm)
    datalistahv = dataahv.split()
    datalistcvm = datacvm.split()
    logging.debug(datalistahv)
    logging.debug(datalistcvm)

    with open(OUTPUT + "NC2clusterinfo.txt", "w") as file3:
        file3.write("VER=" + str(dataver) + "\n")
        file3.write("AHV=" + str(datalistahv) + "\n")
        file3.write("CVM=" + str(datalistcvm) + "\n")
        if jsonResponse["cluster_state"] == "running":
            file3.write("PE_IP=" + jsonResponse["cluster_service_ip"] + "\n")
            key_to_lookup = "load_balancer_dns_name"
            if check_key_exist(jsonResponse, key_to_lookup):
                file3.write("PE_LB=" + jsonResponse["load_balancer_dns_name"] + "\n")

    # https://docs.frame.nutanix.com/frame-apis/admin-api/admin-api.html
    # https://cpanel-backend-prod.frame.nutanix.com/api/v1/docs/clusters/index.html#/

    logging.info(jsonResponse["cluster_state"])
    return jsonResponse["cluster_state"]


if __name__ == "__main__":
    nc2_cluster_status()
