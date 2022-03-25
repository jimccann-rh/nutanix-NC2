#!/usr/bin/env python3
import datetime
import logging
import os
import subprocess
import sys
import time
from base64 import b64encode
from pathlib import Path

# trunk-ignore(flake8/F401)
# import click
import requests
import urllib3
from dateutil import parser
from dotenv import load_dotenv

from clusternutanix import nc2_cluster_status

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

DELETE_THRESHOLD = 24  #: threshold for deleting vpc resources in hours


def determine_age_in_hours(date_string) -> int:
    """Determine age of an object in hours"""
    start_date = parser.parse(date_string)
    end_date = datetime.datetime.now(datetime.timezone.utc)
    age = end_date - start_date
    object_age = age.total_seconds() / 3600
    return object_age


def is_expired(object_age: float) -> bool:
    """Check if the object age is above the threshold and return either True or False"""
    logging.info("object age in hours : " + str(object_age))
    return object_age - DELETE_THRESHOLD > 0


def check_key_exist(test_dict, key):
    try:
        value = test_dict[key]
        logging.info(value)
        return True
    except KeyError:
        return False


def vms_prune():   # noqa: max-complexity=12
    """Prune VMs in the cluster"""
    ncs = nc2_cluster_status()

    if (ncs != "hibernated") and (ncs == "running"):

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # load the script configuration
        env_path_env = Path(".") / ".env"
        load_dotenv(dotenv_path=env_path_env)
        PE_PORT = os.getenv("PE_PORT")
        PE_USERNAME = os.getenv("PE_USERNAME")
        PE_PASSWORD = os.getenv("PE_PASSWORD")
        OUTPUT = os.getenv("OUTPUT")
        VM_EXCEPTIONS = os.getenv("VM_EXCEPTIONS").split(",")
        PRISMCENTRAL_VMDESC = os.getenv("PRISMCENTRAL_VMDESC")

        if not VM_EXCEPTIONS:
            logging.info(
                "*** DANAGER *** Prism Centrals (all of them) should be in this list we are ABORTING *********"
            )
            exit
        else:
            logging.info("list assumed to have Prism Central's uuid listed")

        # load the script configuration
        env_path_nc2 = Path(OUTPUT) / "NC2clusterinfo.txt"
        load_dotenv(dotenv_path=env_path_nc2)
        PE_IP = os.getenv("PE_IP")

        # ping to see if cluster IP is up it should come up after the cluster is online
        cmd = ["ping", "-c2", "-W 5", PE_IP]
        done = False
        timeout = (
            1000  # default time out after 1000 times, set to -1 to disable timeout
        )
        logging.info("Waiting for cluster IP to come on-line.")
        while not done and timeout:
            response = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            stdout, stderr = response.communicate()
            if response.returncode == 0:
                print("Server up!")
                done = True
            else:
                sys.stdout.write(".")
                timeout -= 1
        if not done:
            logging.info("\nCluster failed to respond")
        # Get logged in and get list of vms
        request_url = "https://%s:%s/api/nutanix/v3/vms/list" % (PE_IP, PE_PORT)
        encoded_credentials = b64encode(
            bytes(f"{PE_USERNAME}:{PE_PASSWORD}", encoding="ascii")
        ).decode("ascii")
        auth_header = f"Basic {encoded_credentials}"
        payload = '{"kind":"vm"}'
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"{auth_header}",
            "cache-control": "no-cache",
        }
        response = requests.request(
            "post", request_url, data=payload, headers=headers, verify=False
        )
        logging.debug(response.status_code)
        logging.debug(response.text)

        info = response.json()

        logging.info("*************")
        # logging.info(info['entities'])
        todelete = ""
        for entity in info["entities"]:
            logging.debug(entity)
            vm_uuid = entity["metadata"]["uuid"]
            vm_name = entity["spec"]["name"]
            vm_creation = entity["metadata"]["creation_time"]
            key_to_lookup = "description"
            if check_key_exist(entity["spec"], key_to_lookup):
                vm_description = entity["spec"]["description"]
            else:
                vm_description = ""

            print("VM found in cluster")
            print(
                "********* " + vm_uuid,
                vm_creation,
                vm_name,
                vm_description + "**************",
            )
            howlong = determine_age_in_hours(vm_creation)
            logging.debug("how old ami " + str(howlong))
            deleteme = is_expired(howlong)
            logging.info(deleteme)
            # todelete = " ".join([todelete, vm_uuid]).lstrip()

            toberemove = ""
            if deleteme:
                todelete = f"{todelete} {vm_uuid}".lstrip()
                # logging.info(todelete)
                listtodelete = todelete.split(" ")
                # logging.info(listtodelete)

                # fail safe in case prism central not in vm_exceptions list in .env
                if vm_description == PRISMCENTRAL_VMDESC:
                    VM_EXCEPTIONS.append(vm_uuid)

                logging.info(f"These VMs are excepctions to be pruned {VM_EXCEPTIONS}")
                toberemove = list(set(listtodelete) - set(VM_EXCEPTIONS))
                # print("TOREMOVE***" + str(toberemove))
                print(f"These VMs will be pruned *** {toberemove}")

            else:
                print(f"nothing to be done to this vm {vm_name} {vm_uuid}")
                print("*******************")

        for x in toberemove:
            print(f"DELETED {x}")
            # trunk-ignore(flake8/F841)
            request_url2 = "https://%s:%s/api/nutanix/v3/vms/%s" % (
                PE_IP,
                PE_PORT,
                x,
            )
            # danger
            # response2 = requests.request("delete", request_url2, data=payload, headers=headers, verify=False)
            logging.debug(request_url2)
            time.sleep(1)


if __name__ == "__main__":
    vms_prune()