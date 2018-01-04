import os

#version info
version_file = os.path.join(os.path.dirname(__file__, '..', 'VERSION'))
with open(version_file, 'r') as fr:
    VERSION = fr.read().strip()
