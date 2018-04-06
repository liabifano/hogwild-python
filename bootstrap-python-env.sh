#!/usr/bin/env bash

ENVNAME=$(basename `pwd`)
conda env remove -yq -n $ENVNAME &> /dev/null
conda create -yq -n $ENVNAME --file conda.txt #1> /dev/null
source activate $ENVNAME
pip install -e .
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. hogwild.proto
