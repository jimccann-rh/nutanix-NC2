#!/bin/bash

volumemount=output
mkdir -p "$(pwd)"/"${volumemount}"

SETPODSSHKEYS=${HOME}/.ssh:/run/localsshkeys

if grep -qF "${SETPODSSHKEYS}" /etc/containers/mounts.conf; then
	echo "SSH key path for podman is set look under /run"
else
	echo "${SETPODSSHKEYS}" | sudo tee -a /etc/containers/mounts.conf /dev/null
fi

PODMANAME=PYTHONC2
num=0

STATUS=$(podman ps -aqf "name=^${PODMANAME}$")

until [[ ${STATUS} == "" ]]; do
	echo "already running ${PODMANAME}"
	num=$((num + 1))
	PODMANAME=${PODMANAME}${num}
	STATUS=$(podman ps -aqf "name=^${PODMANAME}$")
done
echo "create container ${PODMANAME}"
podman run --env-file env.list --rm --name "${PODMANAME}" -it --volume "$(pwd)"/"${volumemount}":/"${volumemount}":Z python-nc2 "$@"
