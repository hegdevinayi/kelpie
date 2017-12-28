import os
from waspy.vasp_output_parser import VasprunXMLParser


class VaspCalculationError(Exception):
    pass


class VaspCalculationData(object):
    """Base class to store output data from a VASP calculation."""

    def __init__(self, vasprun_xml_file='vasprun.xml'):
        """
        :param vasprun_xml_file:
        """
        self._vasprun_xml_file = None
        self.vasprun_xml_file = vasprun_xml_file

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
        return VasprunXMLParser(self.vasprun_xml_file)

    @property
    def run_timestamp(self):
        return self.vxparser.read_run_timestamp()

    @property
    def composition_info(self):
        return self.vxparser.read_composition_information()

    @property
    def list_of_atoms(self):
        return self.vxparser.read_list_of_atoms()

    @property
    def number_of_ionic_steps(self):
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
    def lattice_vectors(self):
        return self.vxparser.read_lattice_vectors()

    @property
    def cell_volumes(self):
        return self.vxparser.read_cell_volumes()

    @property
    def fermi_energy(self):
        return self.vxparser.read_fermi_energy()

    @property
    def band_occupations(self):
        return self.vxparser.read_band_occupations()

    @property
    def scf_looptimes(self):
        return self.vxparser.read_scf_looptimes()

    @property
    def total_runtime(self):
        return self._calculate_total_runtime(self.scf_looptimes)

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


