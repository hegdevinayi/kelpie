import os
import unittest


sample_vasp_output_dir = os.path.join(os.path.dirname(__file__), 'sample_vasp_output')

class TestDOS(unittest.TestCase):
    """Base class to test `kelpie.dos.DOS`."""

    from kelpie import dos
    relaxation_dos = dos.DOS(vasprunxml_file=os.path.join(sample_vasp_output_dir, 'relaxation_vasprun.xml.gz'))
    static_dos = dos.DOS(vasprunxml_file=os.path.join(sample_vasp_output_dir, 'static_vasprun.xml.gz'))

    def test_fermi_energy(self):
        self.assertAlmostEqual(self.relaxation_dos.fermi_energy, -1.1180374)
        self.assertAlmostEqual(self.static_dos.fermi_energy, -2.23588190)

    def test_energies(self):
        self.assertEqual(len(self.relaxation_dos.energies), 301)
        self.assertEqual(len(self.static_dos.energies), 3000)
        self.assertAlmostEqual(self.relaxation_dos.energies[4], -37.8519626)
        self.assertAlmostEqual(self.static_dos.energies[2], -21.77711810)

    def test_total_dos(self):
        self.assertListEqual(list(self.relaxation_dos.total_dos.keys()), ['spin_1', 'spin_2'])
        self.assertListEqual(list(self.static_dos.total_dos.keys()), ['spin_1'])
        self.assertEqual(len(self.relaxation_dos.total_dos['spin_1']), 301)
        self.assertEqual(len(self.static_dos.total_dos['spin_1']), 3000)
        self.assertAlmostEqual(self.relaxation_dos.total_dos['spin_2'][200], 3.8714)
        self.assertAlmostEqual(self.static_dos.total_dos['spin_1'][2000], 0.1536)

    def test_total_integrated_dos(self):
        self.assertEqual(len(self.relaxation_dos.total_integrated_dos['spin_1']), 301)
        self.assertEqual(len(self.static_dos.total_integrated_dos['spin_1']), 3000)
        self.assertAlmostEqual(self.relaxation_dos.total_integrated_dos['spin_2'][200], 7.7644)
        self.assertAlmostEqual(self.static_dos.total_integrated_dos['spin_1'][2000], 14.1469)

    def test_projected_dos(self):
        with self.assertRaises(NotImplementedError):
            self.relaxation_dos.get_projected_dos()
        with self.assertRaises(NotImplementedError):
            self.static_dos.get_projected_dos()

    def test_is_metal(self):
        self.assertListEqual(list(self.relaxation_dos.is_metal.keys()), ['spin_1', 'spin_2'])
        self.assertListEqual(list(self.static_dos.is_metal.keys()), ['spin_1'])
        self.assertTrue(self.relaxation_dos.is_metal['spin_2'])
        self.assertFalse(self.static_dos.is_metal['spin_1'])

    def test_find_vbm(self):
        self.assertIsNone(self.relaxation_dos.vbm['spin_2'])
        self.assertAlmostEqual(self.static_dos.vbm['spin_1'], -0.0166181)

    def test_find_cbm(self):
        self.assertIsNone(self.relaxation_dos.cbm['spin_1'])
        self.assertAlmostEqual(self.static_dos.cbm['spin_1'], 6.1307819)

    def test_calculate_band_gap(self):
        self.assertAlmostEqual(self.relaxation_dos.band_gap['spin_1'], 0.)
        self.assertAlmostEqual(self.relaxation_dos.band_gap['spin_2'], 0.)
        self.assertAlmostEqual(self.static_dos.band_gap['spin_1'], 6.1474)


if __name__ == '__main__':
    unittest.main()
