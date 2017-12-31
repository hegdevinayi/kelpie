import os
import glob

templates = glob.glob('*.q')

# module variable DEFAULT_SCHEDULER_SETTINGS
SCHEDULER_TEMPLATES = {}
for template in templates:
    SCHEDULER_TEMPLATES[template] = os.path.abspath(template)
