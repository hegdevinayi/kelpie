import os
import glob
import json

host_setting_files = glob.glob('*.json')

# module variable DEFAULT_SCHEDULER_SETTINGS
DEFAULT_SCHEDULER_SETTINGS = {}
for host_setting_file in host_setting_files:
    host_tag = os.path.splitext(host_setting_file)[0]
    with open(host_setting_file, 'r') as fr:
        DEFAULT_SCHEDULER_SETTINGS[host_tag] = json.load(fr)
