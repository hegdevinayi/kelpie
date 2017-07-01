import unittest
import bs4


@unittest.skip
class TestVasprunXMLParserStatic(unittest.TestCase):

    def test_xml_to_soup_ungzipped(self):
        from waspy import vasp_output_parser as parser
        self.assertIsInstance(parser.VasprunXMLParser._xml_to_soup('vasprun.xml'), bs4.BeautifulSoup)

    def test_xml_to_soup_gzipped(self):
        from waspy import vasp_output_parser as parser
        self.assertIsInstance(parser.VasprunXMLParser._xml_to_soup('vasprun.xml.gz'), bs4.BeautifulSoup)


class TestVasprunXMLParser(unittest.TestCase):
    """Base class to test waspy.vasp_output_parser.VasprunXMLParser class."""

    def setUp(self):
        from waspy import vasp_output_parser as parser
        self.vxparser = parser.VasprunXMLParser('vasprun.xml')

    def test_read_composition(self):
        self.assertDictEqual(self.vxparser.read_composition(), {'Ca': 1, 'F': 2})

    def test_read_atomslist(self):
        self.assertListEqual(self.vxparser.read_atomslist(), ['Ca', 'F', 'F'])

    def test_read_number_of_ionic_steps(self):
        self.assertEqual(self.vxparser.read_number_of_ionic_steps(), 3)

    def test_read_scf_energies(self):
        scf_energies = self.vxparser.read_scf_energies()
        self.assertIsInstance(scf_energies, dict)
        self.assertAlmostEqual(scf_energies[1][1], -17.7085613)

    def test_read_entropy(self):
        entropies = self.vxparser.read_entropy()
        self.assertIsInstance(entropies, dict)
        self.assertAlmostEqual(entropies[1], 0.01828511)

    def test_read_free_energy(self):
        energies = self.vxparser.read_free_energy()
        self.assertIsInstance(energies, dict)
        self.assertAlmostEqual(energies[2], -17.56163366)

    def test_read_forces(self):
        forces = self.vxparser.read_forces()
        self.assertEqual(len(forces.keys()), 3)
        self.assertListEqual(list(forces[0][2]), [0., 0., 0.])
        self.assertEqual(forces[1][1][0], 0.)

    def test_read_stress_tensor(self):
        stress_tensor = self.vxparser.read_stress_tensor()
        self.assertTupleEqual(stress_tensor[0].shape, (3, 3))
        self.assertAlmostEqual(stress_tensor[0][2][2], 70.96233651)

    def test_read_lattice_vectors(self):
        lattice_vectors = self.vxparser.read_lattice_vectors()
        self.assertTupleEqual(lattice_vectors[0].shape, (3, 3))
        self.assertAlmostEqual(lattice_vectors[1][1][1], 3.38391318)

    def test_read_volume_of_cell(self):
        volume = self.vxparser.read_volume_of_cell()
        self.assertAlmostEqual(volume[2], 41.78289124)

    def test_read_fermi_energy(self):
        self.assertAlmostEqual(self.vxparser.read_fermi_energy(), -1.11803743)

    def test_read_occupations(self):
        occupations = self.vxparser.read_occupations()
        self.assertIsInstance(occupations, dict)
        self.assertAlmostEqual(occupations['spin_1'][1]['band_energy'][5], -18.1784)
        self.assertAlmostEqual(occupations['spin_1'][1]['occupation'][9], 1.0353)
        self.assertEqual(max(occupations['spin_2'].keys()), 402)


if __name__ == '__main__':
    unittest.main()

