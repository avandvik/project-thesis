#!/usr/bin/env python3

import os
import data

LOCAL = False
if LOCAL:
    RESULTS_DIR = 'output/local/results'
else:
    RESULTS_DIR = 'output/solstorm/211120-131600/results'

RESULTS_PATH = f'{data.PROJECT_DIR_PATH}/{RESULTS_DIR}'
IPYNB_FILENAME = 'template.ipynb'
CONFIG_FILENAME = '.config_ipynb'
REPORT_DIR = f'{data.PROJECT_DIR_PATH}/report/reports'

file_paths = [os.path.join(RESULTS_PATH, f) for f in os.listdir(RESULTS_PATH)
              if os.path.isfile(os.path.join(RESULTS_PATH, f))]
for file_path in file_paths:
    with open(CONFIG_FILENAME, 'w') as f:
        f.write(' '.join(['file_path', file_path]))
    REPORT_NAME = os.path.basename(file_path).split('.')[0]
    os.system(f'jupyter nbconvert --execute {IPYNB_FILENAME} --to html --no-input '
              f'--output="{REPORT_DIR}/{REPORT_NAME}"')
