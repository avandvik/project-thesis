#!/usr/bin/env python3

import os
import constants as cs
from traitlets.config import Config
import nbformat as nbf
from nbconvert.exporters import NotebookExporter
from nbconvert.preprocessors import TagRemovePreprocessor


REPORT_DIR = f'{cs.PROJECT_DIR_PATH}/report'
REPORT_NAME = f'{cs.FILE_NAME}'

# Name for temporary notebook with cells executed
temporary_notebook = f"{REPORT_DIR}/temporary.ipynb"

# Execute notebook with input data
os.system(f'jupyter nbconvert --to notebook --execute {REPORT_DIR}/template.ipynb\
     --output {temporary_notebook} --ExecutePreprocessor.timeout=180')

c = Config()

# Configure our tag removal
c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell",)
c.TagRemovePreprocessor.remove_input_tags = ('remove_input',)
c.TagRemovePreprocessor.enabled = True

# NotebookExporter.preprocessors = ["nbconvert.preprocessors.TagRemovePreprocessor"]

# Configure and run out exporter
exporter = NotebookExporter(config=c)
exporter.register_preprocessor(TagRemovePreprocessor(config=c), True)

exporter.from_filename(temporary_notebook)

"""
# Convert notebook to html (with removed formatting cells etc.)
os.system(f"jupyter nbconvert --to html {temporary_notebook} \
        --TagRemovePreprocessor.enabled=True\
        --TagRemovePreprocessor.remove_cell_tags=\"['remove_cell']\"\
        --TagRemovePreprocessor.remove_input_tags=\"['remove_input']\"\
        --ExecutePreprocessor.timeout=180\
        --output {REPORT_DIR}/reports/{REPORT_NAME}")
"""

# Clean up temp files
# os.remove(temporary_notebook)
