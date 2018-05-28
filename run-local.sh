#!/usr/bin/env bash
set -eo pipefail

ENVNAME=$(basename `pwd`)

while getopts ":r:" opt; do
  case $opt in
    r) RUNNING_MODE="$OPTARG";; # synchronous or asynchronous
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done


if [[ -z $(conda env list | grep ${ENVNAME}) ]];
then
    echo "bootstraping virtual env"
    bash bootstrap-python-env.sh
fi;

for port in 50052 50053 50054 50055;
do
    source activate hogwild-python && export RUNNING_MODE=$RUNNING_MODE && python src/hogwild/worker.py $port &
done;

source activate hogwild-python && export RUNNING_MODE=$RUNNING_MODE && python src/hogwild/coordinator.py


pkill -f worker
pkill -f coordinator
