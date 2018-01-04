import os
import unittest
import bs4

sample_vasp_output_dir = os.path.join(os.path.dirname(__file__), 'sample_vasp_output')


@unittest.skip
class TestVasprunXMLParserStatic(unittest.TestCase):

    def test_xml_to_soup_ungzipped(self):
        from waspy import vasp_output_parser as parser
        ungzipped_xml_file = os.path.join(sample_vasp_output_dir, 'vasprun.xml')
        self.assertIsInstance(parser.VasprunXMLParser._xml_to_soup(ungzipped_xml_file), bs4.BeautifulSoup)

    def test_xml_to_soup_gzipped(self):
        from waspy import vasp_output_parser as parser
        gzipped_xml_file = os.path.join(sample_vasp_output_dir, 'vasprun.xml.gz')
        self.assertIsInstance(parser.VasprunXMLParser._xml_to_soup(gzipped_xml_file), bs4.BeautifulSoup)


class TestVasprunXMLParser(unittest.TestCase):
    """Base class to test waspy.vasp_output_parser.VasprunXMLParser class."""

    def setUp(self):
        from waspy import vasp_output_parser as parser
        self.vxparser = parser.VasprunXMLParser(os.path.join(sample_vasp_output_dir, 'vasprun.xml'))

    def test_read_composition_information(self):
        composition_info = self.vxparser.read_composition_information()
        self.assertTrue({'Ca', 'F'}.issubset(set(composition_info.keys())))
        self.assertAlmostEqual(composition_info['Ca']['atomic_mass'], 40.078)
        self.assertEqual(composition_info['F']['pseudopotential'], 'PAW_PBE F 08Apr2002')

    def test_read_list_of_atoms(self):
        self.assertListEqual(self.vxparser.read_list_of_atoms(), ['Ca', 'F', 'F'])

    def test_read_number_of_ionic_steps(self):
        self.assertEqual(self.vxparser.read_number_of_ionic_steps(), 3)

    def test_read_scf_energies(self):
        scf_energies = self.vxparser.read_scf_energies()
        self.assertIsInstance(scf_energies, dict)
        self.assertAlmostEqual(scf_energies[1][1], -17.7085613)

    def test_read_entropies(self):
        entropies = self.vxparser.read_entropies()
        self.assertIsInstance(entropies, dict)
        self.assertAlmostEqual(entropies[1], 0.01828511)

    def test_read_free_energies(self):
        energies = self.vxparser.read_free_energies()
        self.assertIsInstance(energies, dict)
        self.assertAlmostEqual(energies[2], -17.56163366)

    def test_read_forces(self):
        forces = self.vxparser.read_forces()
        self.assertEqual(len(forces.keys()), 3)
        self.assertListEqual(list(forces[0][2]), [0., 0., 0.])
        self.assertEqual(forces[1][1][0], 0.)

    def test_read_stress_tensors(self):
        stress_tensor = self.vxparser.read_stress_tensors()
        self.assertTupleEqual(stress_tensor[0].shape, (3, 3))
        self.assertAlmostEqual(stress_tensor[0][2][2], 70.96233651)

    def test_read_lattice_vectors(self):
        lattice_vectors = self.vxparser.read_lattice_vectors()
        self.assertTupleEqual(lattice_vectors[0].shape, (3, 3))
        self.assertAlmostEqual(lattice_vectors[1][1][1], 3.38391318)

    def test_read_cell_volumes(self):
        volume = self.vxparser.read_cell_volumes()
        self.assertAlmostEqual(volume[2], 41.78289124)

    def test_read_fermi_energy(self):
        self.assertAlmostEqual(self.vxparser.read_fermi_energy(), -1.11803743)

    def test_read_band_occupations(self):
        occupations = self.vxparser.read_band_occupations()
        self.assertIsInstance(occupations, dict)
        self.assertAlmostEqual(occupations['spin_1'][1]['band_energy'][5], -18.1784)
        self.assertAlmostEqual(occupations['spin_1'][1]['occupation'][9], 1.0353)
        self.assertEqual(max(occupations['spin_2'].keys()), 402)

    def test_read_run_timestamp(self):
        import datetime
        stamp = self.vxparser.read_run_timestamp()
        self.assertIsInstance(stamp, datetime.datetime)
        self.assertListEqual([stamp.year, stamp.month, stamp.day, stamp.hour, stamp.minute], [2016, 9, 22, 20, 31])

    def test_read_scf_looptimes(self):
        scf_looptimes = self.vxparser.read_scf_looptimes()
        self.assertEqual(len(scf_looptimes[0]), 15)
        self.assertListEqual(scf_looptimes[2][:3], [2.58, 2.47, 3.12])

    @unittest.skip
    def test_calculate_total_runtime(self):
        scf_looptimes = self.vxparser.read_scf_looptimes()
        self.assertAlmostEqual(self.vxparser.calculate_total_runtime(scf_looptimes), 91.6)


if __name__ == '__main__':
    unittest.main()

