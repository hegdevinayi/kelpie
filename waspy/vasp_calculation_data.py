import os
from waspy import vasp_output_parser


class VaspCalculationData:
    """Base class to store output data from a VASP calculation."""

    def __init__(self, vasprun_xml_file='vasprun.xml'):
        """

        :param vasprun_xml_file:
        """
        self.vasprun_xml_file = vasprun_xml_file
        vxparser = vasp_output_parser.VasprunXMLParser(self.vasprun_xml_file)

        self.run_timestamp = vxparser.read_run_timestamp()
        self.composition_info = vxparser.read_composition_information()
        self.list_of_atoms = vxparser.read_list_of_atoms()
        self.number_of_ionic_steps = vxparser.read_number_of_ionic_steps()
        self.scf_energies = vxparser.read_scf_energies()
        self.entropies = vxparser.read_entropies()
        self.free_energies = vxparser.read_free_energies()
        self.lattice_vectors = vxparser.read_lattice_vectors()
        self.cell_volumes = vxparser.read_cell_volumes()
        self.fermi_energy = vxparser.read_fermi_energy()
        self.band_occupations = vxparser.read_band_occupations()
        self.scf_looptimes = vxparser.read_scf_looptimes()

    @property
    def total_runtime(self):
        """Total calculation runtime in seconds."""
        return self._calculate_total_runtime(self.scf_looptimes)

    @staticmethod
    def _calculate_total_runtime(scf_looptimes):
        """Sum up all SCF looptimes to calculate the total runtime in seconds.

        :param scf_looptimes: loop times for each SCF in every ionic step.
                              - see `vasp_output_parser.VasprunXMLParser.read_scf_looptimes()`
        :type scf_looptimes: dict(int, list(float))
        :return: total runtime for the calculation in seconds.
        :rtype: float
        """
        total_runtime = 0.
        for n_ionic_step, scstep_looptimes in scf_looptimes.items():
            total_runtime += sum(scstep_looptimes)
        return total_runtime


