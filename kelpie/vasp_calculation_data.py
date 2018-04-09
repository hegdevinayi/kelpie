import os
import json
import numpy
from kelpie.vasp_output_parser import VasprunXMLParser


class VaspCalculationError(Exception):
    pass


class VaspCalculationData(object):
    """Base class to store output data from a VASP calculation."""

    def __init__(self, vasprun_xml_file='vasprun.xml'):
        """
        :param vasprun_xml_file: Path to the vasprun.xml file to parse.
        """
        self._vasprun_xml_file = None
        self.vasprun_xml_file = vasprun_xml_file

        self._vxparser = VasprunXMLParser(self.vasprun_xml_file)
        self._run_timestamp = self.vxparser.read_run_timestamp()
        self._composition_info = self.vxparser.read_composition_information()
        self._list_of_atoms = self.vxparser.read_list_of_atoms()
        self._n_ionic_steps = self.vxparser.read_number_of_ionic_steps()
        self._scf_energies = self.vxparser.read_scf_energies()
        self._entropies = self.vxparser.read_entropies()
        self._free_energies = self.vxparser.read_free_energies()
        self._forces = self.vxparser.read_forces()
        self._stress_tensors = self.vxparser.read_stress_tensors()
        self._lattice_vectors = self.vxparser.read_lattice_vectors()
        self._cell_volumes = self.vxparser.read_cell_volumes()
        self._fermi_energy = self.vxparser.read_fermi_energy()
        self._band_occupations = self.vxparser.read_band_occupations()
        self._scf_looptimes = self.vxparser.read_scf_looptimes()
        self._total_runtime = self._calculate_total_runtime(self.scf_looptimes)

    @property
    def vasprun_xml_file(self):
        return self._vasprun_xml_file

    @vasprun_xml_file.setter
    def vasprun_xml_file(self, vasprun_xml_file):
        if os.path.isfile(vasprun_xml_file):
            self._vasprun_xml_file = vasprun_xml_file
        else:
            error_msg = 'VASP output file {} not found'.format(vasprun_xml_file)
            raise VaspCalculationError(error_msg)

    @property
    def vxparser(self):
        return self._vxparser

    @staticmethod
    def timestamp_to_str(time):
        return '{:4d}{:0>2d}{:0>2d}{:0>2d}{:0>2d}'.format(time.year, time.month, time.day, time.hour, time.minute)

    @property
    def run_timestamp(self):
        return self._run_timestamp

    @property
    def composition_info(self):
        return self._composition_info

    @property
    def list_of_atoms(self):
        return self._list_of_atoms

    @property
    def n_ionic_steps(self):
        return self._n_ionic_steps

    @property
    def scf_energies(self):
        return self._scf_energies

    @property
    def entropies(self):
        return self._entropies

    @property
    def free_energies(self):
        return self._free_energies

    @property
    def forces(self):
        return self._forces

    @property
    def stress_tensors(self):
        return self._stress_tensors

    @property
    def lattice_vectors(self):
        return self._lattice_vectors

    @property
    def cell_volumes(self):
        return self._cell_volumes

    @property
    def fermi_energy(self):
        return self._fermi_energy

    @property
    def band_occupations(self):
        return self._band_occupations

    @property
    def nbands(self):
        for spin in self.band_occupations:
            for kpoint in self.band_occupations[spin]:
                return len(self.band_occupations[spin][kpoint]['band_energy'])

    @property
    def scf_looptimes(self):
        return self._scf_looptimes

    @property
    def total_runtime(self):
        return self._total_runtime

    @staticmethod
    def _calculate_total_runtime(scf_looptimes):
        """Sum up all SCF looptimes to calculate the total runtime in seconds.

        :param scf_looptimes: loop times for each SCF in every ionic step.
                              - see `VasprunXMLParser.read_scf_looptimes()`
        :type scf_looptimes: dict(int, list(float))
        :return: total runtime for the calculation in seconds.
        :rtype: float
        """
        total_runtime = 0.
        for n_ionic_step, scstep_looptimes in scf_looptimes.items():
            total_runtime += sum(scstep_looptimes)
        return total_runtime

    def is_scf_converged(self, threshold=1E-6, each_ionic_step=False):
        if not each_ionic_step:
            final_energy = self.scf_energies[self.n_ionic_steps - 1][-1]
            final_minus_energy = self.scf_energies[self.n_ionic_steps - 1][-2]
            return final_energy - final_minus_energy <= abs(threshold)
        else:
            converged = True
            for i in range(self.n_ionic_steps):
                final_energy = self.scf_energies[i][-1]
                final_minus_energy = self.scf_energies[i][-2]
                if abs(final_energy - final_minus_energy) > abs(threshold):
                    converged = False
                    break
            return converged

    def are_forces_converged(self, threshold=1E-2):
        converged = True
        for atom_forces in self.forces[self.n_ionic_steps - 1]:
            if any([abs(f) > abs(threshold) for f in atom_forces]):
                converged = False
                break
        return converged

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

    def is_basis_converged(self, volume_only=False, threshold=1E-2):
        if volume_only:
            delta_vol = (self.cell_volumes[self.n_ionic_steps - 1] - self.cell_volumes[0])/self.cell_volumes[0]
            return delta_vol <= abs(threshold)
        else:
            converged = True
            for i in range(3):
                lv_final = numpy.linalg.norm(self.lattice_vectors[self.n_ionic_steps - 1][i])
                lv_initial = numpy.linalg.norm(self.lattice_vectors[0][i])
                if (lv_final - lv_initial)/lv_initial > abs(threshold):
                    converged = False
                    break
            return converged

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
    def calculation_data_as_dict(self):
        calculation_data = {
            'run_timestamp': self.timestamp_to_str(self.run_timestamp),
            'composition_info': self.composition_info,
            'list_of_atoms': self.list_of_atoms,
            'n_ionic_steps': self.n_ionic_steps,
            'free_energies': self.free_energies,
            'forces': self.forces[self.n_ionic_steps - 1].tolist(),
            'initial_stress': self.stress_tensors[0].tolist(),
            'final_stress': self.stress_tensors[self.n_ionic_steps - 1].tolist(),
            'initial_lattice_vectors': self.lattice_vectors[0].tolist(),
            'final_lattice_vectors': self.lattice_vectors[self.n_ionic_steps - 1].tolist(),
            'initial_volume': self.cell_volumes[0],
            'final_volume': self.cell_volumes[self.n_ionic_steps - 1],
            'fermi_energy': self.fermi_energy,
            'total_runtime': self.total_runtime,
            'scf_converged': self.is_scf_converged(),
            'forces_converged': self.are_forces_converged(),
            'bands_converged': self.is_number_of_bands_converged(),
            'basis_converged': self.is_basis_converged(),
            'fully_converged': self.is_fully_converged()
        }
        return calculation_data

    def write_calculation_data(self, filename='calculation_data.json'):
        with open(filename, 'w') as fw:
            json.dump(self.calculation_data_as_dict, fw, indent=2)

