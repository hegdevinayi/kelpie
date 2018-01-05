import unittest
from kelpie.structure import Atom, AtomError
from kelpie.structure import Structure, StructureError


class TestAtom(unittest.TestCase):
    """Base class to test kelpie.structure.Atom class"""

    def test_no_coordinate(self):
        with self.assertRaises(AtomError):
            Atom(species='Al')

    def test_non_float_coordinates(self):
        with self.assertRaises(AtomError):
            Atom(coordinates=[0., 'A', 0.], species='Al')

    def test_coordinates_shape(self):
        with self.assertRaises(AtomError):
            Atom(coordinates=[], species='Al')
        with self.assertRaises(AtomError):
            Atom(coordinates=[0, 1, 2, 3], species='Al')

    def test_no_species(self):
        with self.assertRaises(AtomError):
            Atom(coordinates=[0, 0, 0])

    def test_species_starts_with_unknown_element_symbol(self):
        with self.assertRaises(AtomError):
            Atom(coordinates=[0, 0, 0], species='Af')

    def test_non_string_species(self):
        with self.assertRaises(AtomError):
            Atom(coordinates=[0, 0, 0], species='1Al')

    def test_all_OK(self):
        atom = Atom(coordinates=[0, 0.5, 0.989], species='Mn345')
        self.assertAlmostEqual(atom.x, 0.)
        self.assertAlmostEqual(atom.y, 0.5)
        self.assertAlmostEqual(atom.z, 0.989)
        self.assertEqual(atom.species, 'Mn345')
        self.assertEqual(atom.element, 'Mn345')


class TestStructure(unittest.TestCase):
    """Base class to test kelpie.structure.Structure class"""

    def setUp(self):
        self.structure = Structure()

    def test_default_scaling_constant(self):
        self.assertAlmostEqual(self.structure.scaling_constant, 1.0)

    def test_non_float_scaling_constant(self):
        with self.assertRaises(StructureError):
            self.structure.scaling_constant = 'c'

    def test_no_lattice_vectors(self):
        self.assertEqual(self.structure.lattice_vectors, None)

    def test_non_float_lattice_vectors(self):
        with self.assertRaises(StructureError):
            self.structure.lattice_vectors = [['a']]

    def test_shape_of_lattice_vectors(self):
        with self.assertRaises(StructureError):
            self.structure.lattice_vectors = [[1, 0, 0], [0, 1, 0], [0, 1]]

    def test_nan_lattice_vector_component(self):
        with self.assertRaises(StructureError):
            self.structure.lattice_vectors = [[1, 0, 0], [0, 1, 0], [0, None, 1]]
        with self.assertRaises(StructureError):
            self.structure.lattice_vectors = [[1, 0, 0], [float('nan'), 1, 0], [0, 0, 1]]

    def test_no_coordinate_system(self):
        self.assertEqual(self.structure.coordinate_system, None)

    def test_unrecognized_coordinate_system(self):
        with self.assertRaises(StructureError):
            self.structure.coordinate_system = 'Fractionl'

    def test_default_comment(self):
        self.assertEqual(self.structure.comment, 'Comment')

    def test_no_atoms(self):
        self.assertListEqual(self.structure.atoms, [])

    def test_atoms_instance(self):
        with self.assertRaises(StructureError):
            self.structure.atoms = ['Si']

    def test_add_atom(self):
        # non-`Atom` instance
        with self.assertRaises(StructureError):
            self.structure.add_atom('Si')
        # correct usage
        self.structure.add_atom(Atom([0, 0, 0], 'Si12'))
        self.assertEqual(len(self.structure.atoms), 1)
        self.assertListEqual(self.structure.list_of_species, ['Si12'])

    def test_all_OK(self):
        self.structure.comment = 'bcc-CsCl'
        self.structure.lattice_vectors = [[3.42, 0, 0], [0, 3.42, 0], [0, 0, 3.42]]
        self.structure.coordinate_system = 'direct'
        self.structure.add_atom(Atom([0, 0, 0], 'Cs'))
        self.structure.add_atom(Atom([0.5, 0.5, 0.5], 'Cl'))
        # composition_dict
        self.assertDictEqual(self.structure.composition_dict, {'Cs': 1, 'Cl': 1})
        # list_of_species
        self.assertListEqual(self.structure.list_of_species, ['Cl', 'Cs'])
        poscar = """bcc-CsCl
  1.00000000000000
  3.42000000000000    0.00000000000000    0.00000000000000
  0.00000000000000    3.42000000000000    0.00000000000000
  0.00000000000000    0.00000000000000    3.42000000000000
  Cl   Cs
   1    1
Direct
  0.50000000000000    0.50000000000000    0.50000000000000
  0.00000000000000    0.00000000000000    0.00000000000000"""
        self.assertEqual(self.structure.POSCAR, poscar)


if __name__ == '__main__':
    unittest.main()

