#!/usr/bin/env python3
import logging
import os
import subprocess
import sys
from base64 import b64encode
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv

from clusternutanix import nc2_cluster_status

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def pcvm_status(TRANSITION_PAYLOAD="ON"):
    """Status and setting of the Prism Central VM in the cluster"""
    ncs = nc2_cluster_status()
    if (
        (TRANSITION_PAYLOAD == "ON")
        and (ncs != "hibernated")
        or (TRANSITION_PAYLOAD == "OFF")
        and (ncs() == "running")
        or (TRANSITION_PAYLOAD == "ACPI_SHUTDOWN")
        and (ncs() == "running")
    ):

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # load the script configuration
        env_path_env = Path(".") / ".env"
        load_dotenv(dotenv_path=env_path_env)
        PE_PORT = os.getenv("PE_PORT")
        PE_USERNAME = os.getenv("PE_USERNAME")
        PE_PASSWORD = os.getenv("PE_PASSWORD")
        PRISMCENTRAL_VMNAME = os.getenv("PRISMCENTRAL_VMNAME")
        PRISMCENTRAL_VMDESC = os.getenv("PRISMCENTRAL_VMDESC")
        PRISMCENTRAL_TOGGLE = os.getenv("PRISMCENTRAL_TOGGLE")
        OUTPUT = os.getenv("OUTPUT")

        # load the script configuration
        env_path_nc2 = Path(OUTPUT) / "NC2clusterinfo.txt"
        load_dotenv(dotenv_path=env_path_nc2)
        PE_IP = os.getenv("PE_IP")
        # trunk-ignore(flake8/F841)
        AHV = os.getenv("AHV")
        # trunk-ignore(flake8/F841)
        CVM = os.getenv("CVM")
        # trunk-ignore(flake8/F841)
        VER = os.getenv("VER")

        # ping to see if cluster IP is up it should come up after the cluster is online
        cmd = ["ping", "-c2", "-W 5", PE_IP]
        done = False
        timeout = -1  # default time out after 1000 times, set to -1 to disable timeout

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

        logging.info(response.status_code)
        logging.info(response.text)
        # print(response.json())

        # jsonResponse = response.json()

        # print("Print each key-value pair from JSON response")
        # for key, value in jsonResponse.items():
        # print(key, ":", value)
        # print(jsonResponse)

        request_url = "https://%s:%s/api/nutanix/v2.0/vms/" % (PE_IP, PE_PORT)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"{auth_header}",
            "cache-control": "no-cache",
        }
        response = requests.request("get", request_url, headers=headers, verify=False)
        logging.info(response.text)

        info = response.json()
        # print(info)
        # print(info.get('entities')[0]['uuid'])
        # print(info.get('entities')[0]['name'])

        logging.info("*************")
        # logging.info(info['entities'])

        if PRISMCENTRAL_TOGGLE == "PCVM":
            for entity in info["entities"]:
                if entity["name"] == PRISMCENTRAL_VMNAME:
                    logging.info("found it")
                    logging.info(PRISMCENTRAL_VMNAME)
                    vm_uuid = entity["uuid"]
                    vm_name = entity["name"]
                    vm_description = entity["description"]
                    vm_power_state = entity["power_state"]
                    # vm_host_uuid = entity['host_uuid']
                    # print(vm_uuid, vm_name)
                    break
                else:
                    logging.info("DID NOT find it looping though list")
                    logging.info(PRISMCENTRAL_VMNAME)

            try:
                vm_name
            except NameError:
                logging.info("no match")
            else:
                logging.info("match")

        else:
            # def checkKey(dict, key):
            #   if key in dict:
            #        print("Present, ", end =" ")
            #        print("value =", dict[key])
            #        return True
            #    else:
            #        print("Not present")
            #        return False

            # this function added if VM has no description set it has no key (entities[*]description) in dict.
            def check_key_exist(test_dict, key):
                try:
                    value = test_dict[key]
                    logging.info(value)
                    return True
                except KeyError:
                    return False

            # def checkKey(dict, key):
            #    if key in dict.keys():
            #        print("Present, ", end =" ")
            #        print("value =", dict[key])
            #    else:
            #        print("Not present")

            for entity in info["entities"]:
                key_to_lookup = "description"
                if check_key_exist(entity, key_to_lookup):
                    if entity["description"] == PRISMCENTRAL_VMDESC:
                        logging.info("found it")
                        logging.info(PRISMCENTRAL_VMDESC)
                        vm_uuid = entity["uuid"]
                        vm_name = entity["name"]
                        vm_description = entity["description"]
                        vm_power_state = entity["power_state"]
                        # vm_host_uuid = entity['host_uuid']
                        # print(vm_uuid, vm_name)
                        break
                else:
                    logging.info("DID NOT find it looping though list")
                    logging.info(PRISMCENTRAL_VMDESC)
            try:
                vm_description
            except NameError:
                logging.info("no match")
            else:
                logging.info("match")

                if vm_power_state.upper() != TRANSITION_PAYLOAD:
                    request_url = (
                        "https://%s:%s/api/nutanix/v2.0/vms/%s/set_power_state/"
                        % (PE_IP, PE_PORT, vm_uuid)
                    )
                    headers = {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"{auth_header}",
                        "cache-control": "no-cache",
                    }
                    payload = '{"transition": "%s"}' % (TRANSITION_PAYLOAD)
                    # print(request_url, payload)
                    response = requests.request(
                        "post", request_url, data=payload, headers=headers, verify=False
                    )

                    info3 = response.json()
                    # info4 = response.text
                    # print(info3, info4)

                    logging.info(info3.get("task_uuid"))

                    vm_task_id = info3.get("task_uuid")
                    logging.info(vm_task_id)

                    request_url = "https://%s:%s/api/nutanix/v2.0/tasks/poll" % (
                        PE_IP,
                        PE_PORT,
                    )
                    headers = {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"{auth_header}",
                        "cache-control": "no-cache",
                    }
                    payload = '{"completed_tasks": ["%s"], "timeout_interval": 10 }' % (
                        vm_task_id
                    )
                    # print(request_url, payload)
                    response = requests.request(
                        "post", request_url, data=payload, headers=headers, verify=False
                    )

                    info = response.json()
                    # info2 = response.text
                    # print(info, info2)

                    print(
                        "Task reqeust we got back ",
                        info["completed_tasks_info"][0]["progress_status"]
                        + " state was set to "
                        + TRANSITION_PAYLOAD,
                    )
                else:
                    logging.info(
                        "*** cluster is "
                        + ncs
                        + " *** power set "
                        + TRANSITION_PAYLOAD
                        + " for Prism Central VM current power setting is "
                        + vm_power_state.upper()
                    )


if __name__ == "__main__":
    pcvm_status()
