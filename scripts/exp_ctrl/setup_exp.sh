#!/bin/bash
#
# Copyright (C) 2019 Freie Universität berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}"  )" >/dev/null 2>&1 && pwd  )"
export DATA_DIR=$(realpath -L ${SCRIPT_DIR}/../../results)

RUN_WINDOW=run
DISPATCH_WINDOW=dispatch
EXPERIMENT_TYPE=${1-load}
SESSION=doc-eval-${EXPERIMENT_TYPE}
DISPATCH_SCRIPT=${SCRIPT_DIR}/dispatch_${EXPERIMENT_TYPE}_experiments.py
IOTLAB_SITE_URL=grenoble.iot-lab.info
# TODO check iotlabrc and fetch user
IOTLAB_SITE_VIRTUALENV=/senslab/users/lenders/doc-eval-env
SSH="ssh lenders@${IOTLAB_SITE_URL}"

if ! [ -x "${DISPATCH_SCRIPT}" ]; then
    echo "No dispatch script ${DISPATCH_SCRIPT}" >&2
    echo "for experiment type ${EXPERIMENT_TYPE}" >&2
    exit 1
fi

export PYTHONPATH=$(readlink -f "${SCRIPT_DIR}/../../RIOT/dist/pythonlibs")

. ${SCRIPT_DIR}/ssh-agent.cfg
if [ -z "${SSH_AGENT_PID}" ] || ! ps -p ${SSH_AGENT_PID} > /dev/null; then
    ssh-agent > ${SCRIPT_DIR}/ssh-agent.cfg
    . ${SCRIPT_DIR}/ssh-agent.cfg
fi

if ! ssh-add -l &> /dev/null; then
    ssh-add
fi

if ! [ -d ${SCRIPT_DIR}/env ]; then
    virtualenv -p python3 ${SCRIPT_DIR}/env || exit 1
fi

# . ${SCRIPT_DIR}/env/bin/activate
# pip install --upgrade -r ${SCRIPT_DIR}/requirements.txt

if ! ${SSH} test -d ${IOTLAB_SITE_VIRTUALENV}; then
    REQ_FILE=${IOTLAB_SITE_VIRTUALENV}-req.txt
    cat ${SCRIPT_DIR}/requirements.txt | ${SSH} tee ${REQ_FILE} > /dev/null
    ${SSH} "virtualenv -p python3 ${IOTLAB_SITE_VIRTUALENV} &&
        ( . ${IOTLAB_SITE_VIRTUALENV}/bin/activate; pip install --upgrade -r ${REQ_FILE} )" ||
    exit 1
fi

tmux new-session -d -s ${SESSION} -n ${RUN_WINDOW} -c ${SCRIPT_DIR} \
        script -fa "${DATA_DIR}/${SESSION}.${RUN_WINDOW}.log" \; \
     send-keys -t ${SESSION}:${RUN_WINDOW} "cd ${SCRIPT_DIR}" Enter \; \
     new-window -t ${SESSION} -n ${DISPATCH_WINDOW} -c ${SCRIPT_DIR} \
        script -fa "${DATA_DIR}/${SESSION}.${DISPATCH_WINDOW}.log" \; \
     send-keys -t ${SESSION}:${DISPATCH_WINDOW} "cd ${SCRIPT_DIR}" Enter \; \
     send-keys -t ${SESSION}:${DISPATCH_WINDOW} \
        ". ${SCRIPT_DIR}/env/bin/activate" Enter \; \
     send-keys -t ${SESSION}:${DISPATCH_WINDOW} \
        "pip install --upgrade -r ${SCRIPT_DIR}/requirements.txt" Enter \; \
     send-keys -t ${SESSION}:${DISPATCH_WINDOW} \
        "while true; do ${DISPATCH_SCRIPT} ${IOTLAB_SITE_VIRTUALENV} && break; " \
        "sleep 10; done" Enter \; \
     attach -t ${SESSION}:${DISPATCH_WINDOW}
