import os
import numpy as np
import kelpie.vasp_output_parser as vasp_output_parser


class DOSError(Exception):
    """Base class to handle error(s) related to density of states."""
    pass


class DOS(object):
    """Base class to store density of states data from a calculation."""

    def __init__(self, vasprunxml_file=None, doscar_file=None):
        """
        :param vasprunxml_file: String with the path to the vasprun.xml file from the calculation.
                                (takes preference over doscar_file)
        :param doscar_file: String with the path to the DOSCAR file from the calculation.
        """
        self._vasprunxml_file = None
        self._vxparser = None
        self.vasprunxml_file = vasprunxml_file

        self._doscar_file = None
        self.doscar_file = doscar_file
        self._doscarparser = None

        self._total_dos_data = self.get_total_dos_data()
        self._fermi_energy = self.get_fermi_energy()
        self._energies = self.get_energies()
        self._total_dos = self.get_total_dos()
        self._total_integrated_dos = self.get_total_integrated_dos()
        self._projected_dos = None

    @property
    def vasprunxml_file(self):
        return self._vasprunxml_file

    @vasprunxml_file.setter
    def vasprunxml_file(self, vasprunxml_file):
        if vasprunxml_file:
            if os.path.isfile(vasprunxml_file):
                self._vasprunxml_file = vasprunxml_file
                self._vxparser = vasp_output_parser.VasprunXMLParser(vasprunxml_file=vasprunxml_file)
            else:
                error_message = 'Cannot find the vasprun.xml file specified: {}'.format(vasprunxml_file)
                raise DOSError(error_message)

    @property
    def vxparser(self):
        return self._vxparser

    @property
    def doscar_file(self):
        return self._doscar_file

    @doscar_file.setter
    def doscar_file(self, doscar_file):
        if doscar_file:
            if os.path.isfile(doscar_file):
                self._doscar_file = doscar_file
            else:
                error_message = 'Cannot find the DOSCAR file specified: {}'.format(doscar_file)
                raise DOSError(error_message)

    @property
    def total_dos_data(self):
        return self._total_dos_data

    def get_total_dos_data(self):
        if self.vxparser is None:
            return
        return self.vxparser.read_total_density_of_states()

    @property
    def fermi_energy(self):
        return self._fermi_energy

    def get_fermi_energy(self):
        if self.vasprunxml_file is not None:
            return self.get_fermi_energy_from_xml()
        elif self.doscar_file is not None:
            return self.get_fermi_energy_from_doscar()

    def get_fermi_energy_from_xml(self):
        return self.vxparser.read_fermi_energy()

    def get_fermi_energy_from_doscar(self):
        raise NotImplementedError

    @property
    def energies(self):
        return self._energies

    def get_energies(self):
        if self.vasprunxml_file is not None:
            return self.get_energies_from_xml()
        elif self.doscar_file is not None:
            return self.get_energies_from_doscar()

    def get_energies_from_xml(self):
        if not self.total_dos_data:
            return
        return np.array([gridpoint[0] - self.fermi_energy for gridpoint in self.total_dos_data['spin_1']])

    def get_energies_from_doscar(self):
        raise NotImplementedError

    @property
    def total_dos(self):
        return self._total_dos

    def get_total_dos(self):
        if self.vasprunxml_file is not None:
            return self.get_total_dos_from_xml()
        elif self.doscar_file is not None:
            return self.get_total_dos_from_doscar()

    def get_total_dos_from_xml(self):
        if not self.total_dos_data:
            return
        total_dos = {}
        for spin in self.total_dos_data:
            total_dos[spin] = np.array([gridpoint[1] for gridpoint in self.total_dos_data[spin]])
        return total_dos

    def get_total_dos_from_doscar(self):
        raise NotImplementedError

    @property
    def total_integrated_dos(self):
        return self._total_integrated_dos

    def get_total_integrated_dos(self):
        if self.vasprunxml_file is not None:
            return self.get_total_integrated_dos_from_xml()
        elif self.doscar_file is not None:
            return self.get_total_integrated_dos_from_doscar()

    def get_total_integrated_dos_from_xml(self):
        if not self.total_dos_data:
            return
        total_intdos = {}
        for spin in self.total_dos_data:
            total_intdos[spin] = np.array([gridpoint[2] for gridpoint in self.total_dos_data[spin]])
        return total_intdos

    def get_total_integrated_dos_from_doscar(self):
        raise NotImplementedError

    @property
    def projected_dos(self):
        return self._projected_dos

    def get_projected_dos(self):
        if self.vasprunxml_file is not None:
            return self.get_projected_dos_from_xml()
        elif self.doscar_file is not None:
            return self.get_projected_dos_from_doscar()

    def get_projected_dos_from_xml(self):
        raise NotImplementedError

    def get_projected_dos_from_doscar(self):
        raise NotImplementedError

    def _check_if_metal(self, spin='spin_1', tol=1e-3):
        if self.energies is None or not self.energies.size:
            return
        efermi_index = np.abs(self.energies).argmin()
        if self.energies[efermi_index] < 0:
            bracket_index = efermi_index + 1
        else:
            bracket_index = efermi_index - 1
        return (self.total_dos[spin][efermi_index] > tol) and (self.total_dos[spin][bracket_index] > tol)

    def check_if_metal(self, tol=1e-3):
        return dict([(spin, self._check_if_metal(spin=spin, tol=tol)) for spin in self.total_dos])

    @property
    def is_metal(self):
        return self.check_if_metal()

    def _find_vbm(self, spin='spin_1', tol=1e-3):
        is_metal = self._check_if_metal(spin=spin, tol=tol)
        if is_metal is None or is_metal:
            return
        efermi_index = np.abs(self.energies).argmin()
        if self.energies[efermi_index] < 0:
            efermi_index += 1
        index = efermi_index
        while self.total_dos[spin][index] < tol:
            index -= 1
        return self.energies[index]

    def find_vbm(self, tol=1e-3):
        return dict([(spin, self._find_vbm(spin=spin, tol=tol)) for spin in self.total_dos])

    @property
    def vbm(self):
        return self.find_vbm()

    def _find_cbm(self, spin='spin_1', tol=1e-3):
        is_metal = self._check_if_metal(spin=spin, tol=tol)
        if is_metal is None or is_metal:
            return
        efermi_index = np.abs(self.energies).argmin()
        if self.energies[efermi_index] > 0:
            efermi_index -= 1
        index = efermi_index
        while self.total_dos[spin][index] < tol:
            index += 1
        return self.energies[index]

    def find_cbm(self, tol=1e-3):
        return dict([(spin, self._find_cbm(spin=spin, tol=tol)) for spin in self.total_dos])

    @property
    def cbm(self):
        return self.find_cbm()

    def _calculate_band_gap(self, spin='spin_1', tol=1e-3):
        is_metal = self._check_if_metal(spin=spin, tol=tol)
        if is_metal is not None:
            return (self.cbm[spin] - self.vbm[spin]) if not is_metal else 0.0

    def calculate_band_gap(self, tol=1e-3):
        return dict([(spin, self._calculate_band_gap(spin=spin, tol=tol)) for spin in self.total_dos])

    @property
    def band_gap(self):
        return self.calculate_band_gap()

