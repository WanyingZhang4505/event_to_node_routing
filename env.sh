#!/bin/bash
# how to use: source env.sh (in terminal)

# check if the environment exists in conda env folders
# (specific path: /home/alicezh/miniconda3/envs/<env_name>);
# env is a folder in conda env folders, so we can use ls to list all envs
if ! conda env list | grep -q "/ar_practice$"; then
    echo ">> Creating ar_practice environment..."
    conda create -n ar_practice python=3.10
    conda install -n ar_practice -c conda-forge numpy scipy pandas matplotlib statsmodels -y
else
    echo ">>ar_practice environment already exists!"
fi

conda activate ar_practice
