import os
import glob

current_dir = os.path.dirname(os.path.abspath(__file__))
templates = glob.glob(os.path.join(current_dir, '*.q'))

# module variable DEFAULT_SCHEDULER_SETTINGS
SCHEDULER_TEMPLATES = {}
for template in templates:
    template_tag = os.path.splitext(os.path.basename(template))[0]
    SCHEDULER_TEMPLATES[template_tag] = os.path.abspath(template)
