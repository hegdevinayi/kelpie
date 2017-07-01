import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
incar_tags_file = os.path.join(current_dir, 'incar_tags_dict.json')
# read in VASP INCAR tags and the corresponding groups
with open(incar_tags_file, 'r') as fr:
    VASP_INCAR_TAGS = json.load(fr)

# read in default VASP settings for difference calculation_types
calculation_types = ['relaxation', 'static']
VASP_SETTINGS = {}
for calculation_type in calculation_types:
    settings_file = os.path.join(current_dir, '{}.json'.format(calculation_type))
    with open(settings_file, 'r') as fr:
        VASP_SETTINGS[calculation_type] = json.load(fr)
