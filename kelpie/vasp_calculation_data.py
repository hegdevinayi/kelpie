import numpy
import kelpie.vasp_output_parser as vasp_output_parser
import kelpie.dos as dos
from kelpie.utils.serialization import jsonable


class VaspCalculationDataError(Exception):
    """Base class to handle errors in the VASP calculation data container."""
    pass


class VaspCalculationData(object):
    """Base class to store output data from a VASP calculation."""

    def __init__(self, vasprunxml_file=None, vasp_outcar_file=None):
        """
        :param vasprunxml_file: Path to the vasprun.xml file to parse.
        """
        self._vasprunxml_file = None
        self.vasprunxml_file = vasprunxml_file

        self._vasp_outcar_file = None
        self.vasp_outcar_file = vasp_outcar_file

        # Data from vasp_output_parser.VasprunXMLParser accessible as properties
        self._vxparser = vasp_output_parser.VasprunXMLParser(vasprunxml_file=self.vasprunxml_file)

        # Data from dos.DOS accessible as properties
        self._density_of_states = dos.DOS(vasprunxml_file=self.vasprunxml_file)

        # Data from vasp_output_parser.VaspOutcarParser accessible as properties
        self._voutparser = vasp_output_parser.VaspOutcarParser(vasp_outcar_file=self.vasp_outcar_file)

    @property
    def vasprunxml_file(self):
        return self._vasprunxml_file

    @vasprunxml_file.setter
    def vasprunxml_file(self, vasprunxml_file):
        self._vasprunxml_file = vasprunxml_file

    @property
    def vxparser(self):
        return self._vxparser

    @property
    def vasp_outcar_file(self):
        return self._vasp_outcar_file

    @vasp_outcar_file.setter
    def vasp_outcar_file(self, vasp_outcar_file):
        self._vasp_outcar_file = vasp_outcar_file

    @property
    def voutparser(self):
        return self._voutparser

    @property
    def run_timestamp(self):
        return self.vxparser.read_run_timestamp()

    @property
    def composition_info(self):
        return self.vxparser.read_composition_information()

    @property
    def unit_cell_formula(self):
        return dict([(k, v['natoms']) for k, v in self.composition_info.items()])

    @property
    def list_of_atoms(self):
        return self.vxparser.read_list_of_atoms()

    @property
    def n_atoms(self):
        if not self.list_of_atoms:
            return
        return len(self.list_of_atoms)

    @property
    def n_ionic_steps(self):
        return self.vxparser.read_number_of_ionic_steps()

    @property
    def scf_energies(self):
        return self.vxparser.read_scf_energies()

    @property
    def entropies(self):
        return self.vxparser.read_entropies()

    @property
    def free_energies(self):
        return self.vxparser.read_free_energies()

    @property
    def forces(self):
        return self.vxparser.read_forces()

    @property
    def stress_tensors(self):
        return self.vxparser.read_stress_tensors()

    @property
    def lattice_vectors(self):
        return self.vxparser.read_lattice_vectors()

    @property
    def atomic_coordinates(self):
        return self.vxparser.read_atomic_coordinates()

    @property
    def cell_volumes(self):
        return self.vxparser.read_cell_volumes()

    @property
    def kpoint_mesh(self):
        return self.vxparser.read_kpoint_mesh()

    @property
    def irreducible_kpoints(self):
        return self.vxparser.read_irreducible_kpoints()

    @property
    def n_irreducible_kpoints(self):
        if self.irreducible_kpoints is None:
            return
        return len(self.irreducible_kpoints)

    @property
    def band_occupations(self):
        return self.vxparser.read_band_occupations()

    @property
    def n_bands(self):
        for spin in self.band_occupations:
            for kpoint in self.band_occupations[spin]:
                return len(self.band_occupations[spin][kpoint]['band_energy'])

    @property
    def scf_looptimes(self):
        return self.vxparser.read_scf_looptimes()

    @property
    def average_scf_looptimes(self):
        average_looptimes = {}
        for ionic_step, looptimes in self.scf_looptimes.items():
            average_looptimes[ionic_step] = sum(looptimes)/len(looptimes)
        return average_looptimes

    @property
    def average_scf_looptime(self):
        if self.average_scf_looptimes:
            return sum(self.average_scf_looptimes.values())/len(self.average_scf_looptimes.keys())

    @property
    def average_n_scf_steps_per_ionic_step(self):
        if self.scf_looptimes:
            return float(sum([len(v) for v in self.scf_looptimes.values()]))/self.n_ionic_steps

    @property
    def total_runtime(self):
        return self._calculate_total_runtime()

    def _calculate_total_runtime(self):
        """Sum up all SCF looptimes to calculate the total runtime in seconds.

        :return: total runtime for the calculation in seconds.
        :rtype: float
        """
        total_runtime = 0.
        for n_ionic_step, scstep_looptimes in self.scf_looptimes.items():
            total_runtime += sum(scstep_looptimes)
        return total_runtime

    @property
    def density_of_states(self):
        return self._density_of_states

    @property
    def fermi_energy(self):
        return self.density_of_states.fermi_energy

    @property
    def dos_energy_grid(self):
        return self.density_of_states.energies

    @property
    def total_dos(self):
        return self.density_of_states.total_dos

    @property
    def total_integrated_dos(self):
        return self.density_of_states.total_integrated_dos

    @property
    def is_metal(self):
        return self.density_of_states.is_metal

    @property
    def valence_band_maximum(self):
        return self.density_of_states.vbm

    @property
    def conduction_band_minimum(self):
        return self.density_of_states.cbm

    @property
    def dos_band_gap(self):
        return self.density_of_states.band_gap

    @property
    def orb_projected_charge(self):
        return self.voutparser.read_orb_projected_charge()

    @property
    def orb_projected_magnetization(self):
        return self.voutparser.read_orb_projected_magnetization()

    @property
    def total_orb_projected_charge(self):
        charges = self.orb_projected_charge
        if not charges:
            return
        return dict([(k, sum([charges[index][k] for index in charges])) for k in charges.get(1, {}).keys()])

    @property
    def total_orb_projected_magnetization(self):
        moments = self.orb_projected_magnetization
        if not moments:
            return
        return dict([(k, sum([moments[index][k] for index in moments])) for k in moments.get(1, {}).keys()])

    @property
    def initial_entropy(self):
        return self.entropies.get(0, None)

    @property
    def final_entropy(self):
        return self.entropies.get(self.n_ionic_steps - 1, None)

    @property
    def initial_free_energy(self):
        return self.free_energies.get(0, None)

    @property
    def final_free_energy(self):
        return self.free_energies.get(self.n_ionic_steps - 1, None)

    @property
    def initial_forces(self):
        return self.forces.get(0, None)

    @property
    def final_forces(self):
        return self.forces.get(self.n_ionic_steps - 1, None)

    @property
    def initial_stress_tensor(self):
        return self.stress_tensors.get(0, None)

    @property
    def final_stress_tensor(self):
        return self.stress_tensors.get(self.n_ionic_steps - 1, None)

    @property
    def initial_cell_volume(self):
        return self.cell_volumes.get(0, None)

    @property
    def final_cell_volume(self):
        return self.cell_volumes.get(self.n_ionic_steps - 1, None)

    @property
    def initial_volume_pa(self):
        if all([v is not None for v in [self.initial_cell_volume, self.n_atoms]]):
            return self.initial_cell_volume/self.n_atoms

    @property
    def final_volume_pa(self):
        if all([v is not None for v in [self.final_cell_volume, self.n_atoms]]):
            return self.final_cell_volume/self.n_atoms

    @property
    def initial_lattice_vectors(self):
        return self.lattice_vectors.get(0, None)

    @property
    def final_lattice_vectors(self):
        return self.lattice_vectors.get(self.n_ionic_steps - 1, None)

    @property
    def initial_atomic_coordinates(self):
        return self.atomic_coordinates.get(0, None)

    @property
    def final_atomic_coordinates(self):
        return self.atomic_coordinates.get(self.n_ionic_steps - 1, None)

    def is_scf_converged(self, threshold=1E-6, each_ionic_step=False):
        if not each_ionic_step:
            final_energy = self.scf_energies[self.n_ionic_steps - 1][-1]
            final_minus_energy = self.scf_energies[self.n_ionic_steps - 1][-2]
            return abs(final_energy - final_minus_energy) <= abs(threshold)
        else:
            converged = True
            for i in range(self.n_ionic_steps):
                final_energy = self.scf_energies[i][-1]
                final_minus_energy = self.scf_energies[i][-2]
                if abs(final_energy - final_minus_energy) > abs(2.0*threshold):
                    converged = False
                    break
            return converged

    @property
    def scf_converged(self):
        return self.is_scf_converged()

    def are_forces_converged(self, threshold=1E-2):
        converged = True
        for atom_forces in self.forces[self.n_ionic_steps - 1]:
            if any([abs(f) > abs(threshold) for f in atom_forces]):
                converged = False
                break
        return converged

    @property
    def forces_converged(self):
        return self.are_forces_converged()

    def is_number_of_bands_converged(self, threshold=1E-2):
        highest_band_energy = float('-inf')
        highest_band_occ = 1.
        for spin in self.band_occupations:
            for kpoint in self.band_occupations[spin]:
                for be, occ in zip(self.band_occupations[spin][kpoint]['band_energy'],
                                   self.band_occupations[spin][kpoint]['occupation']):
                    if be > highest_band_energy:
                        highest_band_energy = be
                        highest_band_occ = occ
                    else:
                        continue
        return highest_band_occ <= threshold

    @property
    def number_of_bands_converged(self):
        return self.is_number_of_bands_converged()

    def is_basis_converged(self, volume_only=False, threshold=1E-2):
        if volume_only:
            delta_vol = (self.final_cell_volume - self.initial_cell_volume)/self.initial_cell_volume
            return delta_vol <= abs(3.*threshold)
        else:
            converged = True
            for i in range(3):
                lv_final = numpy.linalg.norm(self.final_lattice_vectors[i])
                lv_initial = numpy.linalg.norm(self.initial_lattice_vectors[i])
                if (lv_final - lv_initial)/lv_initial > abs(threshold):
                    converged = False
                    break
            return converged

    @property
    def basis_converged(self):
        return self.is_basis_converged()

    def is_fully_converged(self, scf_thresh=1E-6,
                           each_ionic_step=False,
                           force_thresh=1E-2,
                           volume_only=False,
                           basis_thresh=1E-2,
                           band_occ_thresh=1E-2):
        converged = (self.is_scf_converged(threshold=scf_thresh, each_ionic_step=each_ionic_step) and
                     self.are_forces_converged(threshold=force_thresh) and
                     self.is_basis_converged(volume_only=volume_only, threshold=basis_thresh) and
                     self.is_number_of_bands_converged(threshold=band_occ_thresh))
        return converged

    @property
    def fully_converged(self):
        return self.is_fully_converged()

    def as_dict(self, list_of_properties=None):
        _PROPERTIES = [
            'run_timestamp',
            'composition_info',
            'unit_cell_formula',
            'list_of_atoms',
            'n_atoms',
            'n_ionic_steps',
            'scf_energies',
            'entropies',
            'free_energies',
            'forces',
            'stress_tensors',
            'lattice_vectors',
            'atomic_coordinates',
            'cell_volumes',
            'kpoint_mesh',
            'irreducible_kpoints',
            'n_irreducible_kpoints',
            'band_occupations',
            'n_bands',
            'scf_looptimes',
            'total_runtime',
            'fermi_energy',
            'dos_energy_grid',
            'total_dos',
            'total_integrated_dos',
            'is_metal',
            'valence_band_maximum',
            'conduction_band_minimum',
            'dos_band_gap',
            'orb_projected_magnetization',
            'orb_projected_charge',
            'total_orb_projected_magnetization',
            'total_orb_projected_charge',
            'initial_entropy',
            'final_entropy',
            'initial_free_energy',
            'final_free_energy',
            'initial_forces',
            'final_forces',
            'initial_stress_tensor',
            'final_stress_tensor',
            'initial_cell_volume',
            'final_cell_volume',
            'initial_volume_pa',
            'final_volume_pa',
            'initial_lattice_vectors',
            'final_lattice_vectors',
            'initial_atomic_coordinates',
            'final_atomic_coordinates',
            'average_scf_looptimes',
            'average_scf_looptime',
            'average_n_scf_steps_per_ionic_step',
            'scf_converged',
            'forces_converged',
            'number_of_bands_converged',
            'basis_converged',
            'fully_converged',
        ]

        if list_of_properties is not None:
            _PROPERTIES = list_of_properties
        return dict([(prop, jsonable(getattr(self, prop, None))) for prop in _PROPERTIES])
