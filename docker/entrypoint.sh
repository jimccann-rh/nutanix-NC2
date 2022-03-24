#!/bin/bash

export IC_API_KEY=${IBMCLOUD_API_KEY}

if [ "$INTERATCLI" = false ] ; then
python "$@"
else
bash
fi
