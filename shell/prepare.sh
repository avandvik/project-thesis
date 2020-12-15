#!/bin/bash

module load Python/3.8.2-GCCcore-9.3.0
module load gurobi/9.0.2
cd "$GUROBI_HOME" || exit
python setup.py build -b "$HOME"/.cache/gurobipy install --user
cd /home/anderhva/project-thesis-lean || exit
