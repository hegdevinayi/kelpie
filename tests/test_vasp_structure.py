import unittest
from waspy import vasp_structure as vs


class TestVaspStructure(unittest.TestCase):
    """Base class to test waspy.vasp_structure.VaspStructure class"""

    def setUp(self):
        self.vstruct_ok = vs.VaspStructure(poscar_file='sample_vasp_input/POSCAR.structure_OK')

    def test_read_poscar_file(self):
        with self.assertRaises(FileNotFoundError):
            vs.VaspStructure(poscar_file='POSCAR.file_not_found')

    def test_get_system_title(self):
        self.assertEqual(self.vstruct_ok.system_title, 'Fe-Li-O-P')

    def test_get_scaling_factor(self):
        self.assertEqual(self.vstruct_ok.scaling_factor, 1.0)
        with self.assertRaises(ValueError):
            vs.VaspStructure('sample_vasp_input/POSCAR.scaling_factor_error')

    def test_get_lattice_vectors(self):
        self.assertIsInstance(self.vstruct_ok.lattice_vectors, list)
        self.assertEqual(len(self.vstruct_ok.lattice_vectors), 3)
        self.assertEqual(len(self.vstruct_ok.lattice_vectors[2]), 3)
        self.assertAlmostEqual(self.vstruct_ok.lattice_vectors[0], [-4.1048998, -2.0524499, 2.0524499])
        with self.assertRaises(ValueError):
            vs.VaspStructure(poscar_file='sample_vasp_input/POSCAR.lattice_vectors_error')

    def test_get_list_of_elements(self):
        self.assertIsInstance(self.vstruct_ok.list_of_elements, list)
        self.assertEqual(self.vstruct_ok.list_of_elements, ['Li', '1Mn', 'O'])
        with self.assertRaises(vs.VaspStructureError):
            vs.VaspStructure(poscar_file='sample_vasp_input/POSCAR.list_of_elements_error')

    def test_get_list_of_number_of_atoms(self):
        self.assertIsInstance(self.vstruct_ok.list_of_number_of_atoms, list)
        self.assertEqual(self.vstruct_ok.list_of_number_of_atoms, [6, 2, 7])
        with self.assertRaises(ValueError):
            vs.VaspStructure(poscar_file='sample_vasp_input/POSCAR.list_of_number_of_atoms_error')

    def test_get_coordinate_system(self):
        self.assertEqual(self.vstruct_ok.coordinate_system, 'Direct')
        with self.assertRaises(NotImplementedError):
            vs.VaspStructure(poscar_file='sample_vasp_input/POSCAR.selective_dynamics_error')
        with self.assertRaises(vs.VaspStructureError):
            vs.VaspStructure(poscar_file='sample_vasp_input/POSCAR.coordinate_system_error')

    def test_get_list_of_atomic_coordinates(self):
        self.assertEqual(len(self.vstruct_ok.list_of_atomic_coordinates), 15)
        self.assertEqual(len(self.vstruct_ok.list_of_atomic_coordinates[2]), 3)
        self.assertAlmostEqual(self.vstruct_ok.list_of_atomic_coordinates[14][0], 0.74999999)
        with self.assertRaises(ValueError):
            vs.VaspStructure(poscar_file='sample_vasp_input/POSCAR.list_of_atomic_coordinates_error')


if __name__ == '__main__':
    unittest.main()

