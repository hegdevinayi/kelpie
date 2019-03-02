import os
import json

# read in VASP INCAR tags and the corresponding groups
current_dir = os.path.dirname(os.path.abspath(__file__))
incar_tags_file = os.path.join(current_dir, 'incar_tags_dict.json')
# module variable VASP_INCAR_TAGS
with open(incar_tags_file, 'r') as fr:
    VASP_INCAR_TAGS = json.load(fr)

# read in default VASP settings for difference calculation_types
calculation_types = ['relaxation', 'static', 'acc_std_relax', 'sc_forces']
# module variable DEFAULT_VASP_INCAR_SETTINGS
DEFAULT_VASP_INCAR_SETTINGS = {}
for calculation_type in calculation_types:
    settings_file = os.path.join(current_dir, '{}.json'.format(calculation_type))
    with open(settings_file, 'r') as fr:
        DEFAULT_VASP_INCAR_SETTINGS[calculation_type] = json.load(fr)

# read in Hubbard U values (currently only from Wang et al., PRB 73, 195107 (2006))
hubbard_values_file = os.path.join(current_dir, 'hubbards.json')
with open(hubbard_values_file, 'r') as fr:
    HUBBARD_U_VALUES = json.load(fr)
