import os
import unittest
from kelpie.vasp_calculation_data import VaspCalculationData


sample_vasp_output_dir = os.path.join(os.path.dirname(__file__), 'sample_vasp_output')


class TestVaspCalculationData(unittest.TestCase):
    """Base class to test :class:`kelpie.vasp_calculation_data.VaspCalculationData`."""

    relaxation_xml = os.path.join(sample_vasp_output_dir, 'relaxation_vasprun.xml.gz')
    relaxation_vcd = VaspCalculationData(vasprunxml_file=relaxation_xml)

    static_xml = os.path.join(sample_vasp_output_dir, 'static_vasprun.xml.gz')
    static_outcar = os.path.join(sample_vasp_output_dir, 'static_OUTCAR.gz')
    static_vcd = VaspCalculationData(vasprunxml_file=static_xml, vasp_outcar_file=static_outcar)

    def test_vasprunxml_file(self):
        self.assertEqual(self.relaxation_vcd.vasprunxml_file, os.path.join(sample_vasp_output_dir,
                                                                           'relaxation_vasprun.xml.gz'))
        self.assertEqual(self.static_vcd.vasprunxml_file, os.path.join(sample_vasp_output_dir,
                                                                       'static_vasprun.xml.gz'))

    def test_vxparser(self):
        from kelpie.vasp_output_parser import VasprunXMLParser
        self.assertIsInstance(self.relaxation_vcd.vxparser, VasprunXMLParser)
        self.assertIsInstance(self.static_vcd.vxparser, VasprunXMLParser)

    def test_vasp_outcar_file(self):
        self.assertIsNone(self.relaxation_vcd.vasp_outcar_file)
        self.assertEqual(self.static_vcd.vasp_outcar_file, os.path.join(sample_vasp_output_dir, 'static_OUTCAR.gz'))

    def test_voutparser(self):
        from kelpie.vasp_output_parser import VaspOutcarParser
        self.assertIsInstance(self.relaxation_vcd.voutparser, VaspOutcarParser)
        self.assertIsNone(self.relaxation_vcd.voutparser.vasp_outcar_file)
        self.assertIsInstance(self.static_vcd.voutparser, VaspOutcarParser)

    def test_runtimestamp(self):
        from datetime import datetime
        relaxation_timestamp = datetime(year=2016, month=9, day=22, hour=20, minute=31, second=26)
        static_timestamp = datetime(year=2018, month=3, day=20, hour=1, minute=12, second=11)
        self.assertEqual(relaxation_timestamp, self.relaxation_vcd.run_timestamp)
        self.assertEqual(static_timestamp, self.static_vcd.run_timestamp)

    def test_composition_info(self):
        self.assertSetEqual(set(self.relaxation_vcd.composition_info.keys()), {'Ca', 'F'})
        self.assertEqual(self.relaxation_vcd.composition_info['F']['natoms'], 2)
        self.assertAlmostEqual(self.static_vcd.composition_info['Na']['atomic_mass'], 22.99)
        self.assertAlmostEqual(self.relaxation_vcd.composition_info['Ca']['valence'], 10.)
        self.assertEqual(self.static_vcd.composition_info['Na']['pseudopotential'], 'PAW_PBE Na_pv 19Sep2006')

    def test_unit_cell_formula(self):
        self.assertDictEqual(self.relaxation_vcd.unit_cell_formula, {'Ca': 1, 'F': 2})
        self.assertDictEqual(self.static_vcd.unit_cell_formula, {'Na': 1, 'F': 1})

    def test_list_of_atoms(self):
        self.assertListEqual(self.relaxation_vcd.list_of_atoms, ['Ca', 'F', 'F'])
        self.assertListEqual(self.static_vcd.list_of_atoms, ['F', 'Na'])

    def test_n_atoms(self):
        self.assertEqual(self.relaxation_vcd.n_atoms, 3)
        self.assertEqual(self.static_vcd.n_atoms, 2)

    def test_n_ionic_steps(self):
        self.assertEqual(self.relaxation_vcd.n_ionic_steps, 3)
        self.assertEqual(self.static_vcd.n_ionic_steps, 1)

    def test_scf_energies(self):
        self.assertSetEqual(set(self.relaxation_vcd.scf_energies.keys()), {0, 1, 2})
        self.assertAlmostEqual(self.relaxation_vcd.scf_energies[1][-1], -17.5606492)
        self.assertAlmostEqual(self.static_vcd.scf_energies[0][-2], -8.57103789)

    def test_entropies(self):
        self.assertAlmostEqual(self.relaxation_vcd.entropies[1], 0.01828511)
        self.assertAlmostEqual(self.static_vcd.entropies[0], 0.)

    def test_free_energies(self):
        self.assertAlmostEqual(self.relaxation_vcd.free_energies[2], -17.5616337)
        self.assertAlmostEqual(self.static_vcd.free_energies[0], -8.57103792)

    def test_forces(self):
        import numpy
        self.assertAlmostEqual(self.relaxation_vcd.forces[0][1][1], 0.)
        self.assertTrue(numpy.shape(self.static_vcd.forces[0]), (2, 3))

    def test_stress_tensors(self):
        import numpy
        self.assertTrue(numpy.shape(self.relaxation_vcd.stress_tensors[2]), (3, 3))
        self.assertAlmostEqual(self.relaxation_vcd.stress_tensors[2][1][1], -1.07296801)
        self.assertTrue(numpy.shape(self.static_vcd.stress_tensors[0]), (3, 3))
        self.assertAlmostEqual(self.static_vcd.stress_tensors[0][2][2], 0.14074542)

    def test_lattice_vectors(self):
        self.assertAlmostEqual(self.relaxation_vcd.lattice_vectors[2][1][0], -1.94748670)
        self.assertAlmostEqual(self.static_vcd.lattice_vectors[0][1][1], 2.34638389)

    def test_atomic_coordinates(self):
        pass

    def test_cell_volumes(self):
        pass

    def test_kpoint_mesh(self):
        pass

    def test_irreducible_kpoints(self):
        pass

    def test_n_irreducible_kpoints(self):
        pass

    def test_band_occupations(self):
        pass

    def test_nbands(self):
        pass

    def test_scf_looptimes(self):
        pass

    def test_average_scf_looptimes(self):
        pass

    def test_average_scf_looptime(self):
        pass

    def test_average_n_scf_steps_per_ionic_step(self):
        pass

    def test_total_runtime(self):
        pass

    def test_density_of_states(self):
        pass

    def test_fermi_energy(self):
        pass

    def test_dos_energy_grid(self):
        pass

    def test_total_dos(self):
        pass

    def test_total_integrated_dos(self):
        pass

    def test_is_metal(self):
        pass

    def test_valence_band_maximum(self):
        pass

    def test_conduction_band_minimum(self):
        pass

    def dos_band_gap(self):
        pass

    def test_orb_projected_charge(self):
        pass

    def test_orb_projected_magnetization(self):
        pass

    def test_total_orb_projected_charge(self):
        pass

    def test_total_orb_projected_magnetization(self):
        pass

    def test_initial_entropy(self):
        pass

    def test_final_entropy(self):
        pass

    def test_initial_free_energy(self):
        pass

    def test_final_free_energy(self):
        pass

    def test_initial_forces(self):
        pass

    def test_final_forces(self):
        pass

    def test_initial_stress_tensor(self):
        pass

    def test_final_stress_tensor(self):
        pass

    def test_initial_cell_volume(self):
        pass

    def test_final_cell_volume(self):
        pass

    def test_initial_volume_pa(self):
        pass

    def test_final_volume_pa(self):
        pass

    def test_initial_lattice_vectors(self):
        pass

    def test_final_lattice_vectors(self):
        pass

    def test_initial_atomic_coordinates(self):
        pass

    def test_final_atomic_coordinates(self):
        pass

    def test_is_scf_converged(self):
        pass

    def test_are_forces_converged(self):
        pass

    def test_is_number_of_bands_converged(self):
        pass

    def test_is_basis_converged(self):
        pass

    def test_is_fully_converged(self):
        pass

    def test_as_dict(self):
        pass


if __name__ == '__main__':
    unittest.main()
