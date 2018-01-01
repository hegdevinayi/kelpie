import os
import glob

current_dir = os.path.dirname(os.path.abspath(__file__))
templates = glob.glob(os.path.join(current_dir, '*.q'))

# module variable DEFAULT_SCHEDULER_SETTINGS
SCHEDULER_TEMPLATES = {}
for template in templates:
    SCHEDULER_TEMPLATES[template] = os.path.abspath(template)
