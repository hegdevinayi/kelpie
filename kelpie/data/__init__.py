import json
import os

# GLOBAL data

# Standard atomic weights
# Source: Meija et al., "Atomic weights of the elements 2013 (IUPAC Tehcnical Report)", Pure Appl. Chem. 88, 265 (2016)
# For elements missing from the above list, source:
# Sansonetti et al., Handbook of Basic Atomic Spectroscopic Data (version 1.1.3). NIST, Gaithersburg, MD
# Accessed from http://physics.nist.gov/Handbook [Date: Dec 27, 2017]
atomic_weights_file = os.path.join(os.path.dirname(__file__), 'standard_atomic_weights.json')
with open(atomic_weights_file, 'r') as fr:
    STD_ATOMIC_WEIGHTS = json.load(fr)


# Number of electrons in s, p, d, f shells
# Source: OQMD (for which the data was taken from Mathematica, IIRC)
valence_electrons_file = os.path.join(os.path.dirname(__file__), 'valence_electrons.json')
with open(valence_electrons_file, 'r') as fr:
    VALENCE_ELECTRONS = json.load(fr)
