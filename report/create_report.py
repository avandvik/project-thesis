#!/usr/bin/env python3

import os
import data

RESULTS_DIR = 'output/results'
RESULTS_PATH = f'{data.PROJECT_DIR_PATH}/{RESULTS_DIR}'
IPYNB_FILENAME = 'template.ipynb'
CONFIG_FILENAME = '.config_ipynb'
REPORT_DIR = f'{data.PROJECT_DIR_PATH}/report/reports'
RUN_NAME = 'local'
REPORT_NAME = f'{data.INSTANCE_NAME}'

files = [f for f in os.listdir(RESULTS_PATH) if os.path.isfile(os.path.join(RESULTS_PATH, f))]

for file in files:
    with open(CONFIG_FILENAME, 'w') as f:
        f.write(' '.join(['data_file', file]))
    os.system(f'jupyter nbconvert --execute {IPYNB_FILENAME} --to html --no-input '
              f'--output="{REPORT_DIR}/{RUN_NAME}/{REPORT_NAME}"')
