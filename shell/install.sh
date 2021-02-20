rm -rf venv
python -m venv venv
source venv/bin/activate
cd /Library/gurobi911/mac64 || exit
python setup.py install
export GRB_LICENSE_FILE=/Library/gurobi911/mac64/gurobi.lic
cd /Users/andersvandvik/Repositories/project-thesis || exit
pip install --upgrade pip
pip install -r requirements.txt
deactivate