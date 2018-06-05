import os
from kelpie.vasp_output_parser import VasprunXMLParser

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
        self.vasprunxml_file = vasprunxml_file

        self._doscar_file = None
        self.doscar_file = doscar_file

        self.unshifted_fermi_energy = self.read_fermi_energy()
        self.energies = self.read_energies()
        self.total_dos = self.read_total_dos()
        self.total_integrated_dos = self.read_total_integrated_dos()
        self.projected_dos = self.read_projected_dos()

    @property
    def vasprunxml_file(self):
        return self._vasprunxml_file

    @vasprunxml_file.setter
    def vasprunxml_file(self, vasprunxml_file):
        if vasprunxml_file:
            if os.path.isfile(vasprunxml_file):
                self._vasprunxml_file = vasprunxml_file
            else:
                error_message = 'Cannot find the vasprun.xml file specified: {}'.format(vasprunxml_file)
                raise DOSError(error_message)

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

    def read_fermi_energy(self):
        if self.vasprunxml_file is not None:
            return self.read_fermi_energy_from_xml()
        elif self.doscar_file is not None:
            return self.read_fermi_energy_from_doscar()

    def read_fermi_energy_from_xml(self):
        vxp = VasprunXMLParser(vasprunxml_file=self.vasprunxml_file)
        return vxp.read_fermi_energy()

    def read_fermi_energy_from_doscar(self):
        raise NotImplementedError

    def read_energies(self):
        if self.vasprunxml_file is not None:
            return self.read_energies_from_xml()
        elif self.doscar_file is not None:
            return self.read_energies_from_doscar()

    def read_energies_from_xml(self):
        vxp = VasprunXMLParser(vasprunxml_file=self.vasprunxml_file)
        dos_data = vxp.read_total_dos()
        if dos_data is None:
            return
        return np.array([gridpoint[0] - self.fermi_energy for gridpoint in dos_data['spin_1']])

    def read_energies_from_poscar(self):
        raise NotImplementedError

    def read_total_dos(self):
        if self.vasprunxml_file is not None:
            return self.read_total_dos_from_xml()
        elif self.doscar_file is not None:
            return self.read_total_dos_from_doscar()

    def read_total_dos_from_xml(self):
        vxp = VasprunXMLParser(vasprunxml_file=self.vasprunxml_file)
        dos_data = vxp.read_total_dos()
        if dos_data is None:
            return
        total_dos = {}
        for spin in dos_data:
            total_dos[spin] = np.array([gridpoint[1] for gridpoint in dos_data[spin]])
        return total_dos

    def read_total_dos_from_doscar(self):
        raise NotImplementedError

    def read_total_integrated_dos(self):
        if self.vasprunxml_file is not None:
            return self.read_total_integrated_dos_from_xml()
        elif self.doscar_file is not None:
            return self.read_total_integrated_dos_from_doscar()

    def read_total_integrated_dos_from_xml(self):
        vxp = VasprunXMLParser(vasprunxml_file=self.vasprunxml_file)
        dos_data = vxp.read_total_dos()
        if dos_data is None:
            return
        total_intdos = {}
        for spin in dos_data:
            total_intdos[spin] = np.array([gridpoint[2] for gridpoint in dos_data[spin]])

    def read_total_integrated_dos_from_doscar(self):
        raise NotImplementedError

    def read_projected_dos(self):
        if self.vasprunxml_file is not None:
            return self.read_projected_dos_from_xml()
        elif self.doscar_file is not None:
            return self.read_projected_dos_from_doscar()

    def read_projected_dos_from_xml(self):
        raise NotImplementedError

    def read_projected_dos_from_doscar(self):
        raise NotImplementedError

    def is_metal(self, tol=1e-3):
        if any([v is None for v in [self.total_dos, self.energies]]):
            self.read_total_dos()
            self.read_energies()
            if any([v is None for v in [self.total_dos, self.energies]]):
                error_message = 'Cannot read DOS data from file'
                raise DOSError(error_message)
        efermi_index = np.abs(self.energies).argmin()
        if self.energies[efermi_index] < 0:
            bracket_index = efermi_index + 1
        elif self.energies[efermi_index] > 0:
            bracket_index = efermi_index - 1
        return ((self.total_dos[efermi_index] > tol) and (self.total_dos[bracket_index] > tol))

    def find_vbm(self, tol=1e-3):
        if self.is_metal(tol=tol):
            return
        efermi_index = np.abs(self.energies).argmin()
        if self.energies[efermi_index] < 0:
            efermi_index += 1
        index = efermi_index
        while self.total_dos[index] < tol:
            index -= 1
        return self.energies[index]

    @property
    def vbm(self):
        return self.find_vbm()

    def find_cbm(self, tol=1e-3):
        if self.is_metal(tol=tol):
            return
        efermi_index = np.abs(self.energies).argmin()
        if self.energies[efermi_index] > 0:
            efermi_index -= 1
        index = efermi_index
        while self.total_dos[index] < tol:
            index += 1
        return self.energies[index]

    @property
    def cbm(self):
        return self.find_cbm()

    def calculate_band_gap(self, tol=1e-3):
        if self.is_metal(tol=tol):
            return 0.0
        return self.cbm - self.vbm

    @property
    def band_gap(self):
        return self.calculate_band_gap()

