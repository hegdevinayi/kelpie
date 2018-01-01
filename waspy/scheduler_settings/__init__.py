import os
import glob
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
host_setting_files = glob.glob(os.path.join(current_dir, '*.json'))

# module variable DEFAULT_SCHEDULER_SETTINGS
DEFAULT_SCHEDULER_SETTINGS = {}
for host_setting_file in host_setting_files:
    host_tag = os.path.splitext(os.path.basename(host_setting_file))[0]
    with open(host_setting_file, 'r') as fr:
        DEFAULT_SCHEDULER_SETTINGS[host_tag] = json.load(fr)
