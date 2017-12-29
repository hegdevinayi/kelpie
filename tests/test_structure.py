import unittest
from waspy.structure import Structure


class TestStructure(unittest.TestCase):
    """Base class to test waspy.vasp_structure.VaspStructure class"""

    def setUp(self):
        self.vstruct_ok = Structure()
        poscar_file='sample_vasp_input/POSCAR.structure_OK')


if __name__ == '__main__':
    unittest.main()

