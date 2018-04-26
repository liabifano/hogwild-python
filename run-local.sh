#!/usr/bin/env bash
set -eo pipefail

ENVNAME=$(basename `pwd`)

if [[ -z $(conda env list | grep ${ENVNAME}) ]];
then
    echo "bootstraping virtual env"
    bash bootstrap-python-env.sh
fi;

for port in 50052 50053;
do
    source activate hogwild-python && python src/hogwild/node.py $port &
done;

source activate hogwild-python && python src/hogwild/coordinator.py
