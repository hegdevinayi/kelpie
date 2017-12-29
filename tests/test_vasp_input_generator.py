import unittest
from waspy.vasp_input_generator import VaspInputGenerator, VaspInputError


class TestVaspInputGenerator(unittest.TestCase):
    """Base class to test waspy.vasp_input_generator.VaspInputGenerator class."""

    def test_structure_setter(self):
        from waspy import io
        s = io.read_poscar('sample_vasp_input/POSCAR.all_OK')
        ig = VaspInputGenerator(structure=s)
        self.assertEqual(ig.structure, s)

    ig = VaspInputGenerator(structure='sample_vasp_input/POSCAR.all_OK')

    def test_structure_setter_error(self):
        with self.assertRaises(VaspInputError):
            VaspInputGenerator(structure='non_existent_POSCAR')

    def test_calculation_settings_setter_defaults(self):
        self.assertTrue(self.ig.calculation_settings['lcharg'])
        self.assertAlmostEqual(self.ig.calculation_settings['potim'], 0.187)

    def test_calculation_settings_setter_encut_ediff(self):
        self.assertAlmostEqual(self.ig.calculation_settings['encut'], 600.)
        self.assertAlmostEqual(self.ig.calculation_settings['ediff'], 15E-08)

    def test_write_location_setter_default(self):
        self.assertEqual(self.ig.write_location, 'Li6Mn2O7')

    def test_tag_value_formatter(self):
        self.assertEqual(self.ig.vasp_tag_value_formatter([27, 'acc', 0.15, True]), '27 ACC 1.50E-01 .TRUE.')

    def test_format_vasp_tag(self):
        self.assertEqual(self.ig.format_vasp_tag('ediff', 1E-6), 'EDIFF          = 1.00E-06')

    def test_get_vasp_potcar_normal(self):
        self.assertIsInstance(self.ig.POTCAR, str)
        with open('sample_vasp_input/POTCAR.LiMnO', 'r') as fr:
            self.assertEqual(self.ig.POTCAR, fr.read())

    def test_get_vasp_potcar_different_label(self):
        from waspy.vasp_settings.incar import DEFAULT_VASP_INCAR_SETTINGS
        calc_sett = DEFAULT_VASP_INCAR_SETTINGS['relaxation']
        calc_sett['potcar_settings'].update({'element_potcars': {'Mn1': 'Mn_pv', 'Mn2': 'Mn'}})
        ig = VaspInputGenerator(structure='sample_vasp_input/POSCAR.structure_OK',
                                calculation_settings=calc_sett)
        with open('sample_vasp_input/Li_sv__Mn_pv__Mn__O.POTCAR') as fr:
            self.assertEqual(ig.POTCAR, fr.read())

    def test_get_highest_enmax(self):
        self.assertAlmostEqual(self.ig.get_highest_enmax(self.ig.POTCAR), 499.034)

    def test_roundup_encut(self):
        self.assertEqual(VaspInputGenerator.roundup_encut(271.335), 280)

    def test_set_calculation_encut(self):
        self.assertEqual(self.ig.calculation_settings['encut'], 600)

    def test_scale_ediff_per_atom(self):
        self.assertAlmostEqual(self.ig.calculation_settings.get('ediff'), 15E-8)

    def test_get_vasp_incar(self):
        self.assertEqual(self.ig.INCAR.split('\n')[0], '### general ###')

    def test_write_vasp_input_files(self):
        import os
        import shutil
        self.ig.write_vasp_input_files()
        self.assertTrue(os.path.isdir('Li6Mn2O7'))
        self.assertTrue(os.path.isfile('Li6Mn2O7/POSCAR'))
        self.assertTrue(os.path.isfile('Li6Mn2O7/POTCAR'))
        self.assertTrue(os.path.isfile('Li6Mn2O7/INCAR'))
        shutil.rmtree('Li6Mn2O7')


if __name__ == '__main__':
    unittest.main()
