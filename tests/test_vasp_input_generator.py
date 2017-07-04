import unittest
from waspy import vasp_input_generator


class TestVaspInputGenerator(unittest.TestCase):
    """Base class to test waspy.vasp_input_generator.VaspInputGenerator class."""

    def test_tag_value_formatter(self):
        self.vig = vasp_input_generator.VaspInputGenerator('sample_vasp_input/POSCAR.all_OK')
        self.assertEqual(self.vig.vasp_tag_value_formatter([27, 'acc', 0.15, True]), '27 ACC 1.50E-01 .TRUE.')

    def test_format_vasp_tag(self):
        self.vig = vasp_input_generator.VaspInputGenerator('sample_vasp_input/POSCAR.all_OK')
        self.assertEqual(self.vig.format_vasp_tag('ediff', 1E-6), 'EDIFF          = 1.00E-06')

    def test_get_vasp_potcar(self):
        # normal POSCAR
        self.vig = vasp_input_generator.VaspInputGenerator('sample_vasp_input/POSCAR.all_OK')
        self.assertIsInstance(self.vig.POTCAR, str)
        with open('sample_vasp_input/POTCAR.LiMnO', 'r') as fr:
            potcar = fr.read()
        self.assertEqual(self.vig.POTCAR, potcar)
        # POSCAR with differently labeled element
        with self.assertRaises(vasp_input_generator.VaspInputError):
            vasp_input_generator.VaspInputGenerator('sample_vasp_input/POSCAR.structure_OK')

    def test_get_highest_enmax(self):
        self.vig = vasp_input_generator.VaspInputGenerator('sample_vasp_input/POSCAR.all_OK')
        self.assertAlmostEqual(self.vig.get_highest_enmax(self.vig.POTCAR), 499.034)

    def test_roundup_encut(self):
        self.assertEqual(vasp_input_generator.VaspInputGenerator.roundup_encut(271.335), 280)

    def test_set_calculation_encut(self):
        self.vig = vasp_input_generator.VaspInputGenerator('sample_vasp_input/POSCAR.all_OK')
        self.assertEqual(self.vig.calculation_settings['encut'], 520)

    def test_get_vasp_incar(self):
        self.vig = vasp_input_generator.VaspInputGenerator('sample_vasp_input/POSCAR.all_OK')
        self.assertEqual(self.vig.INCAR.split('\n')[0], '### general ###')

    def test_write_vasp_input_files(self):
        import os
        self.vig = vasp_input_generator.VaspInputGenerator('sample_vasp_input/POSCAR.all_OK')
        self.vig.write_vasp_input_files(location='write_vasp_input_files')
        self.assertTrue(os.path.isdir('write_vasp_input_files'))
        self.assertTrue(os.path.isfile('write_vasp_input_files/POSCAR'))
        self.assertTrue(os.path.isfile('write_vasp_input_files/POTCAR'))
        self.assertTrue(os.path.isfile('write_vasp_input_files/INCAR'))

if __name__ == '__main__':
    unittest.main()
