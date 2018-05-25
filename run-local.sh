#!/usr/bin/env bash
set -eo pipefail

ENVNAME=$(basename `pwd`)


if [[ -z $(conda env list | grep ${ENVNAME}) ]];
then
    echo "bootstraping virtual env"
    bash bootstrap-python-env.sh
fi;

for port in 50052 50053 50054 50055 50056 50057 50058 50059 50060 50061;
do
    source activate hogwild-python && export RUNNING_MODE=synchronous && python src/hogwild/node.py $port &
done;

source activate hogwild-python && export RUNNING_MODE=synchronous && python src/hogwild/coordinator.py
