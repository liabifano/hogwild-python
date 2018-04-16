#!/usr/bin/env bash

ENVNAME=$(basename `pwd`)
conda env remove -yq -n $ENVNAME &> /dev/null
conda create -yq -n $ENVNAME --file conda.txt #1> /dev/null
source activate $ENVNAME
pip install -e .
