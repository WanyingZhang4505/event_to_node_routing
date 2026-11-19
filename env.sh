#!/bin/bash
# how to use: source env.sh (in terminal)
# Trillium 原生环境: 退出 conda -> 加载集群 python -> virtualenv + computecanada 轮子
# (集群 python 不能和 miniconda 混用, 否则会出现 libze_loader / GLIBC 报错)

VENV=/scratch/alicezh/routing/trillium_env

# 1. 退出 conda (每次都要, 保证用的是集群 python 而不是 miniconda)
while [ -n "$CONDA_PREFIX" ]; do conda deactivate 2>/dev/null || break; done

# 2. 加载 Trillium 要求的 python (每次都要)
module load python/3.10

# 3. 首次运行: 建 virtualenv 并用 --no-index 从 cvmfs wheelhouse 装依赖
if [ ! -d "$VENV" ]; then
    echo ">> Creating trillium_env..."
    virtualenv --no-download "$VENV"
    source "$VENV/bin/activate"
    pip install --no-index --upgrade pip
    pip install --no-index numpy scipy pandas matplotlib statsmodels torch
else
    source "$VENV/bin/activate"
fi

echo ">> env ready: $(which python) ($(python --version 2>&1))"