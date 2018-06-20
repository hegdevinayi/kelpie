import os
import unittest


sample_vasp_output_dir = os.path.join(os.path.dirname(__file__), 'sample_vasp_output')


class TestVaspCalculationData(unittest.TestCase):
    """Base class to test :class:`kelpie.vasp_calculation_data.VaspCalculationData`."""

    def setUp(self):
        pass

