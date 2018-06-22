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
        self.assertTupleEqual(numpy.shape(self.static_vcd.forces[0]), (2, 3))

    def test_stress_tensors(self):
        import numpy
        self.assertTupleEqual(numpy.shape(self.relaxation_vcd.stress_tensors[2]), (3, 3))
        self.assertAlmostEqual(self.relaxation_vcd.stress_tensors[2][1][1], -1.07296801)
        self.assertTupleEqual(numpy.shape(self.static_vcd.stress_tensors[0]), (3, 3))
        self.assertAlmostEqual(self.static_vcd.stress_tensors[0][2][2], 0.14074542)

    def test_lattice_vectors(self):
        self.assertAlmostEqual(self.relaxation_vcd.lattice_vectors[2][1][0], -1.94748670)
        self.assertAlmostEqual(self.static_vcd.lattice_vectors[0][1][1], 2.34638389)

    def test_atomic_coordinates(self):
        import numpy
        self.assertTupleEqual(numpy.shape(self.relaxation_vcd.atomic_coordinates[0]), (3, 3))
        self.assertTupleEqual(numpy.shape(self.static_vcd.atomic_coordinates[0]), (2, 3))
        self.assertAlmostEqual(self.relaxation_vcd.atomic_coordinates[0][1][2], 0.24999888)
        self.assertAlmostEqual(self.static_vcd.atomic_coordinates[0][0][1], 0.5)

    def test_cell_volumes(self):
        self.assertListEqual(list(self.relaxation_vcd.cell_volumes.keys()), [0, 1, 2])
        self.assertListEqual(list(self.static_vcd.cell_volumes.keys()), [0])
        self.assertAlmostEqual(self.relaxation_vcd.cell_volumes[1], 42.18428983)
        self.assertAlmostEqual(self.static_vcd.cell_volumes[0], 25.83611454)

    def test_kpoint_mesh(self):
        self.assertListEqual(self.relaxation_vcd.kpoint_mesh, [11, 12, 11])
        self.assertListEqual(self.static_vcd.kpoint_mesh, [16, 16, 16])

    def test_irreducible_kpoints(self):
        self.assertAlmostEqual(self.relaxation_vcd.irreducible_kpoints[4][0], 0.36363636)
        self.assertAlmostEqual(self.static_vcd.irreducible_kpoints[2][0], 0.125)

    def test_n_irreducible_kpoints(self):
        self.assertEqual(self.relaxation_vcd.n_irreducible_kpoints, 402)
        self.assertEqual(self.static_vcd.n_irreducible_kpoints, 145)

    def test_band_occupations(self):
        self.assertListEqual(list(self.relaxation_vcd.band_occupations.keys()), ['spin_1', 'spin_2'])
        self.assertListEqual(list(self.static_vcd.band_occupations.keys()), ['spin_1'])
        self.assertAlmostEqual(self.relaxation_vcd.band_occupations['spin_2'][1]['band_energy'][0], -37.1897)
        self.assertAlmostEqual(self.relaxation_vcd.band_occupations['spin_2'][1]['occupation'][9], 1.0353)
        self.assertAlmostEqual(self.static_vcd.band_occupations['spin_1'][2]['band_energy'][3], -21.1815)
        self.assertAlmostEqual(self.static_vcd.band_occupations['spin_1'][2]['occupation'][9], 0.)

    def test_n_bands(self):
        self.assertEqual(self.relaxation_vcd.n_bands, 18)
        self.assertEqual(self.static_vcd.n_bands, 11)

    def test_scf_looptimes(self):
        self.assertListEqual(list(self.relaxation_vcd.scf_looptimes.keys()), [0, 1, 2])
        self.assertListEqual(list(self.static_vcd.scf_looptimes.keys()), [0])
        self.assertAlmostEqual(self.relaxation_vcd.scf_looptimes[0][14], 2.24)
        self.assertAlmostEqual(self.static_vcd.scf_looptimes[0][10], 1.28)

    def test_average_scf_looptimes(self):
        self.assertAlmostEqual(self.relaxation_vcd.average_scf_looptimes[0], 2.55933333)
        self.assertAlmostEqual(self.static_vcd.average_scf_looptimes[0], 1.586363636)

    def test_average_scf_looptime(self):
        self.assertAlmostEqual(self.relaxation_vcd.average_scf_looptime, 2.7169629629)
        self.assertAlmostEqual(self.static_vcd.average_scf_looptime, 1.58636363)

    def test_average_n_scf_steps_per_ionic_step(self):
        self.assertAlmostEqual(self.relaxation_vcd.average_n_scf_steps_per_ionic_step, 11.333333333)
        self.assertAlmostEqual(self.static_vcd.average_n_scf_steps_per_ionic_step, 11.)

    def test_total_runtime(self):
        self.assertAlmostEqual(self.relaxation_vcd.total_runtime, 91.6)
        self.assertAlmostEqual(self.static_vcd.total_runtime, 17.45)

    def test_density_of_states(self):
        from kelpie.dos import DOS
        self.assertIsInstance(self.relaxation_vcd.density_of_states, DOS)
        self.assertIsInstance(self.static_vcd.density_of_states, DOS)

    def test_fermi_energy(self):
        self.assertAlmostEqual(self.relaxation_vcd.fermi_energy, -1.11803743)
        self.assertAlmostEqual(self.static_vcd.fermi_energy, -2.23588190)

    def test_dos_energy_grid(self):
        self.assertEqual(len(self.relaxation_vcd.dos_energy_grid), 301)
        self.assertEqual(len(self.static_vcd.dos_energy_grid), 3000)
        self.assertAlmostEqual(self.relaxation_vcd.dos_energy_grid[0], -38.59096257)
        self.assertAlmostEqual(self.static_vcd.dos_energy_grid[1], -21.7919181)

    def test_total_dos(self):
        self.assertListEqual(list(self.relaxation_vcd.total_dos.keys()), ['spin_1', 'spin_2'])
        self.assertListEqual(list(self.static_vcd.total_dos.keys()), ['spin_1'])
        self.assertEqual(len(self.relaxation_vcd.total_dos['spin_2']), 301)
        self.assertEqual(len(self.static_vcd.total_dos['spin_1']), 3000)
        self.assertAlmostEqual(self.relaxation_vcd.total_dos['spin_2'][99], -0.0836)
        self.assertAlmostEqual(self.static_vcd.total_dos['spin_1'][2000], 0.1536)

    def test_total_integrated_dos(self):
        self.assertListEqual(list(self.relaxation_vcd.total_integrated_dos.keys()), ['spin_1', 'spin_2'])
        self.assertListEqual(list(self.static_vcd.total_integrated_dos.keys()), ['spin_1'])
        self.assertEqual(len(self.relaxation_vcd.total_integrated_dos['spin_2']), 301)
        self.assertEqual(len(self.static_vcd.total_integrated_dos['spin_1']), 3000)
        self.assertAlmostEqual(self.relaxation_vcd.total_integrated_dos['spin_2'][99], 0.9830)
        self.assertAlmostEqual(self.static_vcd.total_integrated_dos['spin_1'][2000], 14.1469)

    def test_is_metal(self):
        self.assertTrue(self.relaxation_vcd.is_metal['spin_2'])
        self.assertFalse(self.static_vcd.is_metal['spin_1'])

    def test_valence_band_maximum(self):
        self.assertIsNone(self.relaxation_vcd.valence_band_maximum['spin_1'])
        self.assertAlmostEqual(self.static_vcd.valence_band_maximum['spin_1'], -0.0166181)

    def test_conduction_band_minimum(self):
        self.assertIsNone(self.relaxation_vcd.conduction_band_minimum['spin_1'])
        self.assertAlmostEqual(self.static_vcd.conduction_band_minimum['spin_1'], 6.1307819)

    def test_dos_band_gap(self):
        self.assertAlmostEqual(self.relaxation_vcd.dos_band_gap['spin_2'], 0.)
        self.assertAlmostEqual(self.static_vcd.dos_band_gap['spin_1'], 6.1474)

    def test_orb_projected_charge(self):
        self.assertIsNone(self.relaxation_vcd.orb_projected_charge)
        self.assertListEqual(list(self.static_vcd.orb_projected_charge.keys()), list(range(1, 13)))
        self.assertListEqual(list(self.static_vcd.orb_projected_charge[1].keys()), ['s', 'p', 'd', 'tot'])
        self.assertAlmostEqual(self.static_vcd.orb_projected_charge[1]['s'], 0.476)
        self.assertAlmostEqual(self.static_vcd.orb_projected_charge[3]['p'], 6.110)
        self.assertAlmostEqual(self.static_vcd.orb_projected_charge[7]['d'], 0.085)
        self.assertAlmostEqual(self.static_vcd.orb_projected_charge[12]['tot'], 7.485)

    def test_orb_projected_magnetization(self):
        self.assertIsNone(self.relaxation_vcd.orb_projected_magnetization)
        self.assertListEqual(list(self.static_vcd.orb_projected_magnetization.keys()), list(range(1, 13)))
        self.assertListEqual(list(self.static_vcd.orb_projected_magnetization[1].keys()), ['s', 'p', 'd', 'tot'])
        self.assertAlmostEqual(self.static_vcd.orb_projected_magnetization[3]['s'], -0.003)
        self.assertAlmostEqual(self.static_vcd.orb_projected_magnetization[1]['p'], 0.018)
        self.assertAlmostEqual(self.static_vcd.orb_projected_magnetization[11]['d'], 1.069)
        self.assertAlmostEqual(self.static_vcd.orb_projected_magnetization[12]['tot'], 1.097)

    def test_total_orb_projected_charge(self):
        self.assertIsNone(self.relaxation_vcd.total_orb_projected_charge)
        self.assertListEqual(list(self.static_vcd.total_orb_projected_charge.keys()), ['s', 'p', 'd', 'tot'])
        self.assertAlmostEqual(self.static_vcd.total_orb_projected_charge['s'], 14.948)
        self.assertAlmostEqual(self.static_vcd.total_orb_projected_charge['p'], 32.175)
        self.assertAlmostEqual(self.static_vcd.total_orb_projected_charge['d'], 35.923)
        self.assertAlmostEqual(self.static_vcd.total_orb_projected_charge['tot'], 83.047)

    def test_total_orb_projected_magnetization(self):
        self.assertIsNone(self.relaxation_vcd.total_orb_projected_magnetization)
        self.assertListEqual(list(self.static_vcd.total_orb_projected_magnetization.keys()), ['s', 'p', 'd', 'tot'])
        self.assertAlmostEqual(self.static_vcd.total_orb_projected_magnetization['s'], -0.004)
        self.assertAlmostEqual(self.static_vcd.total_orb_projected_magnetization['p'], 0.148)
        self.assertAlmostEqual(self.static_vcd.total_orb_projected_magnetization['d'], 1.793)
        self.assertAlmostEqual(self.static_vcd.total_orb_projected_magnetization['tot'], 1.935)

    def test_initial_entropy(self):
        self.assertAlmostEqual(self.relaxation_vcd.initial_entropy, 0.01621571)
        self.assertAlmostEqual(self.static_vcd.initial_entropy, 0.)

    def test_final_entropy(self):
        self.assertAlmostEqual(self.relaxation_vcd.final_entropy, 0.01803879)
        self.assertAlmostEqual(self.static_vcd.final_entropy, 0.)

    def test_initial_free_energy(self):
        self.assertAlmostEqual(self.relaxation_vcd.initial_free_energy, -17.50045148)
        self.assertAlmostEqual(self.static_vcd.initial_free_energy, -8.57103792)

    def test_final_free_energy(self):
        self.assertAlmostEqual(self.relaxation_vcd.final_free_energy, -17.56163366)
        self.assertAlmostEqual(self.static_vcd.final_free_energy, -8.57103792)

    def test_initial_forces(self):
        self.assertAlmostEqual(self.relaxation_vcd.initial_forces[1][1], 0.)
        self.assertAlmostEqual(self.static_vcd.initial_forces[1][2], 0.)

    def test_final_forces(self):
        self.assertAlmostEqual(self.relaxation_vcd.final_forces[2][0], 0.)
        self.assertAlmostEqual(self.static_vcd.final_forces[1][0], 0.)

    def test_initial_stress_tensor(self):
        self.assertAlmostEqual(self.relaxation_vcd.initial_stress_tensor[1][1], 70.96233651)
        self.assertAlmostEqual(self.static_vcd.initial_stress_tensor[2][2], 0.14074542)

    def test_final_stress_tensor(self):
        self.assertAlmostEqual(self.relaxation_vcd.final_stress_tensor[1][1], -1.07296801)
        self.assertAlmostEqual(self.static_vcd.final_stress_tensor[2][2], 0.14074542)

    def test_initial_cell_volume(self):
        self.assertAlmostEqual(self.relaxation_vcd.initial_cell_volume, 38.86638710)
        self.assertAlmostEqual(self.static_vcd.initial_cell_volume, 25.83611454)

    def test_final_cell_volume(self):
        self.assertAlmostEqual(self.relaxation_vcd.final_cell_volume, 41.78289124)
        self.assertAlmostEqual(self.static_vcd.final_cell_volume, 25.83611454)

    def test_initial_volume_pa(self):
        self.assertAlmostEqual(self.relaxation_vcd.initial_volume_pa, 12.9554623666)
        self.assertAlmostEqual(self.static_vcd.initial_volume_pa, 12.91805727)

    def test_final_volume_pa(self):
        self.assertAlmostEqual(self.relaxation_vcd.final_volume_pa, 13.927630413)
        self.assertAlmostEqual(self.static_vcd.final_volume_pa, 12.91805727)

    def test_initial_lattice_vectors(self):
        self.assertAlmostEqual(self.relaxation_vcd.initial_lattice_vectors[2][1], -2.19517474)
        self.assertAlmostEqual(self.relaxation_vcd.initial_lattice_vectors[2][2], 3.10444588)
        self.assertAlmostEqual(self.static_vcd.initial_lattice_vectors[1][1], 2.34638389)
        self.assertAlmostEqual(self.static_vcd.initial_lattice_vectors[2][2], 2.34638389)

    def test_final_lattice_vectors(self):
        self.assertAlmostEqual(self.relaxation_vcd.final_lattice_vectors[2][1], -2.24876394)
        self.assertAlmostEqual(self.relaxation_vcd.final_lattice_vectors[2][2], 3.18023246)
        self.assertAlmostEqual(self.static_vcd.final_lattice_vectors[1][1], 2.34638389)
        self.assertAlmostEqual(self.static_vcd.final_lattice_vectors[2][2], 2.34638389)

    def test_initial_atomic_coordinates(self):
        self.assertAlmostEqual(self.relaxation_vcd.initial_atomic_coordinates[2][2], 0.74999888)
        self.assertAlmostEqual(self.static_vcd.initial_atomic_coordinates[0][1], 0.5)

    def test_final_atomic_coordinates(self):
        self.assertAlmostEqual(self.relaxation_vcd.final_atomic_coordinates[2][1], 0.49999888)
        self.assertAlmostEqual(self.static_vcd.final_atomic_coordinates[0][1], 0.5)

    def test_is_scf_converged(self):
        self.assertTrue(self.relaxation_vcd.is_scf_converged())
        self.assertFalse(self.relaxation_vcd.is_scf_converged(threshold=1E-9, each_ionic_step=True))
        self.assertTrue(self.static_vcd.is_scf_converged())
        self.assertFalse(self.static_vcd.is_scf_converged(threshold=1E-9, each_ionic_step=True))

    def test_are_forces_converged(self):
        self.assertTrue(self.relaxation_vcd.are_forces_converged())
        self.assertTrue(self.relaxation_vcd.are_forces_converged(threshold=1E-6))
        self.assertTrue(self.static_vcd.are_forces_converged())
        self.assertTrue(self.static_vcd.are_forces_converged(threshold=1E-6))

    def test_is_number_of_bands_converged(self):
        self.assertTrue(self.relaxation_vcd.is_number_of_bands_converged())
        self.assertTrue(self.static_vcd.is_number_of_bands_converged())

    def test_is_basis_converged(self):
        self.assertFalse(self.relaxation_vcd.is_basis_converged())
        self.assertTrue(self.relaxation_vcd.is_basis_converged(threshold=5E-2))
        self.assertFalse(self.relaxation_vcd.is_basis_converged(volume_only=True))
        self.assertTrue(self.relaxation_vcd.is_basis_converged(volume_only=True, threshold=3E-2))
        self.assertTrue(self.static_vcd.is_basis_converged())

    def test_is_fully_converged(self):
        self.assertFalse(self.relaxation_vcd.is_fully_converged())
        self.assertTrue(self.relaxation_vcd.is_fully_converged(scf_thresh=1E-6, each_ionic_step=True,
                                                               force_thresh=1E-6, basis_thresh=3E-2))
        self.assertTrue(self.static_vcd.is_fully_converged())


if __name__ == '__main__':
    unittest.main()
