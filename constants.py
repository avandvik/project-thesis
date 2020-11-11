import pathlib


# Path of the root of the project
PROJECT_DIR_PATH = f'{pathlib.Path(__file__).parent.absolute()}'

# Either 'mongstad' or 'simple_instances'
INSTANCE_GROUP = 'simple_instances'

# File name WITHOUT '.json'
FILE_NAME = 5

# Run program with lots of printing
VERBOSE = False

# Max run time of gurobi solver
TIME_LIMIT = 60 * 60
