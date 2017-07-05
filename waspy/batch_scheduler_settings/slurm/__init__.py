import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))

hosts = ['cori']
# read in the default SLURM settings for various hosts
# module varible DEFAULT_SETTINGS
DEFAULT_SETTINGS = {}
for host in hosts:
    settings_file = os.path.join(current_dir, '{}.json'.format(host))
    with open(settings_file, 'r') as fr:
        DEFAULT_SETTINGS[host] = json.load(fr)
