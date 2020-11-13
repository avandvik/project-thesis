import pathlib


# Path of the root of the project
PROJECT_DIR_PATH = f'{pathlib.Path(__file__).parent.absolute()}'

# Either 'mongstad' or 'simple_instances'
# INSTANCE_GROUP = 'simple_instances'
INSTANCE_GROUP = 'mongstad'

# File name WITHOUT '.results'
# FILE_NAME = 5
FILE_NAME = 'CS-I3-V1-WS0'

# Run program with lots of printing
VERBOSE = True

# Max run time of gurobi solver
TIME_LIMIT = 60 * 60
