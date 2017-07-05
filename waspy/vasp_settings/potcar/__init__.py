import os
import json

# read in list of VASP recommended potentials for each element
current_dir = os.path.dirname(os.path.abspath(__file__))
reco_potcars_file = os.path.join(current_dir, 'vasp_reco_potcars.json')
# module variable VASP_RECO_POTCARS
with open(reco_potcars_file, 'r') as fr:
    VASP_RECO_POTCARS = json.load(fr)

