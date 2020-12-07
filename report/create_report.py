#!/usr/bin/env python3

import os
import data

LOCAL = True
if LOCAL:
    RESULTS_DIR = 'local/order_selection'
    RESULTS_PATH = f'{data.PROJECT_DIR_PATH}/output/{RESULTS_DIR}/results'
    REPORT_PATH = f'{data.PROJECT_DIR_PATH}/report/reports/{RESULTS_DIR}'
else:
    RESULTS_DIR = 'solstorm/weather'
    RESULTS_PATH = f'{data.PROJECT_DIR_PATH}/output/{RESULTS_DIR}/results'
    REPORT_PATH = f'{data.PROJECT_DIR_PATH}/report/reports/{RESULTS_DIR}'

IPYNB_FILENAME = 'template.ipynb'
CONFIG_FILENAME = '.config_ipynb'

file_paths = [os.path.join(RESULTS_PATH, f) for f in os.listdir(RESULTS_PATH)
              if os.path.isfile(os.path.join(RESULTS_PATH, f))]
for file_path in file_paths:
    with open(CONFIG_FILENAME, 'w') as f:
        f.write(' '.join(['file_path', file_path]))
    REPORT_NAME = os.path.basename(file_path).split('.')[0]
    os.system(f'jupyter nbconvert --execute {IPYNB_FILENAME} --to html --no-input '
              f'--output="{REPORT_PATH}/{REPORT_NAME}"')
