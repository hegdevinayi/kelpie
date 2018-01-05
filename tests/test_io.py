import os
import unittest
from kelpie import io


sample_vasp_input_dir = os.path.join(os.path.dirname(__file__), 'sample_vasp_input')


def _poscar_lines(poscar_file):
    with open(poscar_file, 'r') as fr:
        poscar_lines = [line.strip() for line in fr.readlines()]
    return poscar_lines


class TestIOReadPOSCAR(unittest.TestCase):
    """Base class to test `io.read_poscar()`"""

    def setUp(self):
        self.poscar_OK = os.path.join(sample_vasp_input_dir, 'POSCAR.structure_OK')

    def test_poscar_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            io.read_poscar(poscar_file='POSCAR.file_not_found')

    def test_consistent_number_of_atoms(self):
        self.assertTrue(io._consistent_number_of_atoms(_poscar_lines(self.poscar_OK)))
        error_poscar = os.path.join(sample_vasp_input_dir, 'POSCAR.consistent_number_of_atoms_error')
        self.assertFalse(io._consistent_number_of_atoms(_poscar_lines(error_poscar)))

    def test_system_title(self):
        self.assertEqual(io._system_title(_poscar_lines(self.poscar_OK)), 'Fe-Li-O-P')

    def test_scaling_constant(self):
        self.assertEqual(io._scaling_constant(_poscar_lines(self.poscar_OK)), 1.0)
        error_poscar = os.path.join(sample_vasp_input_dir, 'POSCAR.scaling_factor_error')
        with self.assertRaises(io.KelpieIOError):
            io._scaling_constant(_poscar_lines(error_poscar))

    def test_lattice_vectors(self):
        lattice_vectors = io._lattice_vectors(_poscar_lines(self.poscar_OK))
        self.assertIsInstance(lattice_vectors, list)
        self.assertEqual(len(lattice_vectors), 3)
        self.assertEqual(len(lattice_vectors[2]), 3)
        self.assertAlmostEqual(lattice_vectors[0], [-4.1048998, -2.0524499, 2.0524499])
        error_poscar = os.path.join(sample_vasp_input_dir, 'POSCAR.lattice_vectors_error')
        with self.assertRaises(io.KelpieIOError):
            io._lattice_vectors(_poscar_lines(error_poscar))

    def test_list_of_species(self):
        self.assertIsInstance(io._list_of_species(_poscar_lines(self.poscar_OK)), list)
        self.assertEqual(io._list_of_species(_poscar_lines(self.poscar_OK)), ['Li', 'Mn1', 'Mn2', 'O'])
        error_poscar = os.path.join(sample_vasp_input_dir, 'POSCAR.list_of_species_error')
        with self.assertRaises(io.KelpieIOError):
            io._list_of_species(_poscar_lines(error_poscar))

    def test_list_of_number_of_atoms(self):
        self.assertIsInstance(io._list_of_number_of_atoms(_poscar_lines(self.poscar_OK)), list)
        self.assertEqual(io._list_of_number_of_atoms(_poscar_lines(self.poscar_OK)), [6, 1, 1, 7])
        error_poscar = os.path.join(sample_vasp_input_dir, 'POSCAR.list_of_number_of_atoms_error')
        with self.assertRaises(io.KelpieIOError):
            io._list_of_number_of_atoms(_poscar_lines(error_poscar))

    def test_repeating_list_of_species(self):
        rl = ['Li']*6 + ['Mn1'] + ['Mn2'] + ['O']*7
        self.assertEqual(io._repeating_list_of_species(_poscar_lines(self.poscar_OK)), rl)

    def test_coordinate_system(self):
        self.assertEqual(io._coordinate_system(_poscar_lines(self.poscar_OK)), 'Direct')
        error_poscar = os.path.join(sample_vasp_input_dir, 'POSCAR.selective_dynamics_error')
        with self.assertRaises(NotImplementedError):
            io._coordinate_system(_poscar_lines(error_poscar))
        error_poscar = os.path.join(sample_vasp_input_dir, 'POSCAR.coordinate_system_error')
        with self.assertRaises(io.KelpieIOError):
            io._coordinate_system(_poscar_lines(error_poscar))

    def test_list_of_atomic_coordinates(self):
        list_of_atomic_coordinates = io._list_of_atomic_coordinates(_poscar_lines(self.poscar_OK))
        self.assertEqual(len(list_of_atomic_coordinates), 15)
        self.assertEqual(len(list_of_atomic_coordinates[2]), 3)
        self.assertAlmostEqual(list_of_atomic_coordinates[14][0], 0.74999999)
        error_poscar = os.path.join(sample_vasp_input_dir, 'POSCAR.list_of_atomic_coordinates_error')
        with self.assertRaises(io.KelpieIOError):
            io._list_of_atomic_coordinates(_poscar_lines(error_poscar))


if __name__ == '__main__':
    unittest.main()

