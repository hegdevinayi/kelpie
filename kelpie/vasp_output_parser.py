import os
import gzip
import numpy as np
import datetime
from lxml import etree


class VasprunXMLParserError(Exception):
    """Base class to handle errors related to parsing the vasprun.xml file."""
    pass


class VasprunXMLParser(object):
    """Base class to parse relevant output from a vasprun.xml file."""

    def __init__(self, vasprunxml_file=None):
        """
        :param vasprunxml_file: name of the vasprun.xml file (default: None)
        :type vasprunxml_file: str or None
        """
        self._vasprunxml_file = None
        self._xmlroot = None

        self.vasprunxml_file = vasprunxml_file

    @property
    def vasprunxml_file(self):
        return self._vasprunxml_file

    @vasprunxml_file.setter
    def vasprunxml_file(self, vasprunxml_file):
        if vasprunxml_file is None:
            return
        if not os.path.isfile(vasprunxml_file):
            error_message = 'Cannot find the specified vasprun.xml file: {}'.format(vasprunxml_file)
            raise VasprunXMLParserError(error_message)
        self._vasprunxml_file = os.path.abspath(vasprunxml_file)
        self._xmlroot = self._get_vasprunxml_root()

    def _get_vasprunxml_root(self):
        """Read contents from a vasprun.xml or vasprun.xml.gz file, convert it into
        etree.ElementTree and get the root element with tag 'modeling'

        :raises: VasprunXMLParserError if the root element is not 'modeling'
        :return: root element of vasprun.xml
        :rtype: etree._Element
        """
        if self.vasprunxml_file is None:
            return
        parser = etree.XMLParser(remove_blank_text=True)
        try:
            tree = etree.parse(self.vasprunxml_file, parser=parser)
        except etree.XMLSyntaxError:
            return
        xmlroot = tree.getroot()
        if xmlroot.tag != 'modeling':
            error_message = 'Root element of vasprun.xml "modeling" not found'
            raise VasprunXMLParserError(error_message)
        return xmlroot

    @property
    def xmlroot(self):
        return self._xmlroot

    def read_composition_information(self):
        """Read the list of elemental species in the unit cell, and number of atoms, atomic mass, number of valence
        electrons, VASP pseudopotential title tag for each species.

        :return: unit cell composition information.
                 - {element1: {'natoms': n1, 'atomic_mass': m1, 'valence': v1, 'pseudopotential': p1}, element2: ...}
        :rtype: dict(str, dict(str, int or float or str))
        """
        composition_info = {}
        if self.xmlroot is not None:
            atomtypes_array = self.xmlroot.findall('./atominfo/array')
            for array in atomtypes_array:
                if array.attrib['name'] != 'atomtypes':
                    continue
                for species in array.findall('./set/rc'):
                    natoms, elem, mass, valence, psp = [c.text.strip() for c in species.findall('c')]
                    composition_info.update({elem: {'natoms': int(natoms),
                                                    'atomic_mass': float(mass),
                                                    'valence': float(valence),
                                                    'pseudopotential': psp
                                                    }
                                            })
        return composition_info

    def read_list_of_atoms(self):
        """Read the list of atoms in the unit cell.

        :return: list of atoms ['atom1', 'atom1', 'atom2', 'atom2', 'atom2', ...]
        :rtype: list
        """
        atomslist = []
        if self.xmlroot is not None:
            atoms_array = self.xmlroot.findall('./atominfo/array')
            for array in atoms_array:
                if array.attrib['name'] != 'atoms':
                    continue
                for species in array.findall('./set/rc'):
                    atom_symbol, atomtype = [c.text.strip() for c in species.findall('c')]
                    atomslist.append(atom_symbol)
        return atomslist

    def read_number_of_ionic_steps(self):
        """Read number of ionic steps in the VASP run.

        :return: number of ionic steps
        :rtype: int
        """
        if self.xmlroot is not None:
            return len(self.xmlroot.findall('./calculation'))

    def read_scf_energies(self):
        """Read all the the energies in every ionic step.

        :return: {ionic_step_1: [e1, e2, e3, ...], ionic_step_2: [e1, e2, ...], ionic_step_3: ...}
        :rtype: dict(int, list(float))
        """
        scf_energies = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('./calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                scsteps = ionic_step.findall('scstep')
                scstep_energies = []
                for scstep in scsteps:
                    for energy in scstep.findall('./energy/i'):
                        if energy.attrib['name'] == 'e_fr_energy':
                            scstep_energies.append(float(energy.text.strip()))
                scf_energies[n_ionic_step] = scstep_energies
        return scf_energies

    def read_entropies(self):
        """Read entropy at the end of each ionic step.

        :return: {ionic_step_1: entropy_1, ionic_step_2: entropy_2, ionic_step_3: ...}
        :rtype: dict(int, float)
        """
        entropy_dict = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('./calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                entropy = None
                final_scstep = ionic_step.findall('scstep')[-1]
                for final_energy_block in final_scstep.findall('energy'):
                    for energy in final_energy_block.findall('i'):
                        if energy.attrib['name'] == 'eentropy':
                            entropy = float(energy.text.strip())
                entropy_dict[n_ionic_step] = entropy
        return entropy_dict

    def read_free_energies(self):
        """Read free energy at the end of each ionic step.

        :return: {ionic_step_1: free_energy_1, ionic_step_2: free_energy_2, ionic_step_3: ...}
        :rtype: dict(int, float)
        """
        free_energy_dict = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('./calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                free_energy = None
                final_scstep = ionic_step.findall('scstep')[-1]
                for final_energy_block in final_scstep.findall('energy'):
                    for energy in final_energy_block.findall('i'):
                        if energy.attrib['name'] == 'e_fr_energy':
                            free_energy = float(energy.text.strip())
                free_energy_dict[n_ionic_step] = free_energy
        return free_energy_dict

    def read_forces(self):
        """Read forces on all atoms in the unit cell at the end of each ionic step.

        :return: {ionic_step_1: [[fx_1, fy_1, fz_1], [fx_2, fy_2, fz_2], ...], ionic_step_2: ...}
        :rtype: dict(int, numpy.array)
                - numpy.array of shape (N_atoms, 3)
        """
        forces_dict = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('./calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                varrays = ionic_step.findall('varray')
                forces = []
                for varray in varrays:
                    if varray.attrib['name'] != 'forces':
                        continue
                    for force_on_atom in varray.findall('v'):
                        forces.append([float(e) for e in force_on_atom.text.split()])
                forces_dict[n_ionic_step] = np.array(forces)
        return forces_dict

    def read_stress_tensors(self):
        """Read stress (in kbar) on the unit cell at the end of each ionic step.

        :return: {ionic_step_1: [[Sxx, Sxy, Sxz], [Syx, Syy, Syz], [Szx, Szy, Szz]], ionic_step_2: ...}
        :rtype: dict(int, numpy.array)
                - numpy.array of shape (3, 3)
        """
        stress_tensor_dict = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('./calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                varrays = ionic_step.findall('varray')
                stress_tensor = []
                for varray in varrays:
                    if varray.attrib['name'] != 'stress':
                        continue
                    for stress_component in varray.findall('v'):
                        stress_tensor.append([float(e) for e in stress_component.text.split()])
                stress_tensor_dict[n_ionic_step] = np.array(stress_tensor)
        return stress_tensor_dict

    def read_lattice_vectors(self):
        """Read lattice vectors (in Angstrom) of the unit cell at the end of each ionic step.

        :return: {ionic_step_1: [[a11, a12, a13], [a21, a22, a23], [a31, a32, a33]], ionic_step_2: ...}
        :rtype: dict(key, numpy.array)
                - numpy.array of shape (3, 3)
        """
        lattice_vectors_dict = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('./calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                varrays = ionic_step.findall('./structure/crystal/varray')
                lattice_vectors = []
                for varray in varrays:
                    if varray.attrib['name'] != 'basis':
                        continue
                    for lattice_vector in varray.findall('v'):
                        lattice_vectors.append([float(e) for e in lattice_vector.text.split()])
                lattice_vectors_dict[n_ionic_step] = np.array(lattice_vectors)
        return lattice_vectors_dict

    def read_atomic_coordinates(self):
        """Read positions of all the atoms at the end of each ionic step.

        :return: {ionic_step_1: [[species_1, [x1, y1, z1]], [species_2, [x2, y2, z2]], ...], ionic_step_2: ...}
        :rtype: dict(int, list(list(str, numpy.array)))
        """
        atomic_coordinates = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                atomic_coordinates[n_ionic_step] = []
                varray = ionic_step.find('./structure/varray')
                if varray.attrib['name'] != 'positions':
                    continue
                for coordinates in varray.findall('v'):
                    atomic_coordinates[n_ionic_step].append([float(e) for e in coordinates.text.split()])
        return atomic_coordinates

    def read_cell_volumes(self):
        """Read the volume (in cubic Angstrom) of the unit cell at the end of each ionic step.

        :return: {ionic_step_1: float, ionic_step_2: float}
        :rtype: dict(int, float)
        """
        volume_dict = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                volume = float(ionic_step.find('./structure/crystal/i').text.strip())
                volume_dict[n_ionic_step] = volume
        return volume_dict

    def read_kpoint_mesh(self):
        """Read the k-point mesh (k_x, k_y, k_z) used in the calculation.

        :return: [k_x, k_y, k_z]
        :rtype: list(int)
        """
        if self.xmlroot is not None:
            kpoints_block = self.xmlroot.find('kpoints')
            for v in kpoints_block.findall('./generation/v'):
                if v.attrib['name'] == 'divisions':
                    kmesh = [int(k) for k in v.text.split()]
                    return kmesh

    def read_irreducible_kpoints(self):
        """Read all the irreducible k-points used in the calculation.

        :return: [[kx_1, ky_1, kz_1], [kx_2, ky_2, kz_2], ...]
        :rtype: list(list(float))
        """
        kpoints = []
        if self.xmlroot is not None:
            kpoints_block = self.xmlroot.find('kpoints')
            for kpointlist in kpoints_block.findall('varray'):
                if kpointlist.attrib['name'] == 'kpointlist':
                    for v in kpointlist.findall('v'):
                        kpoints.append([float(k) for k in v.text.split()])
        return kpoints

    def read_total_density_of_states(self):
        """
        :return: Total density of states data {'spin_1': [[energy1, dos1, intdos_1], ...], 'spin_2': ...}
        :rtype: dict(str, list(list(float)))
        """
        total_dos_data = {}
        if self.xmlroot is not None:
            dos_block = self.xmlroot.find('./calculation/dos')
            for spin in dos_block.findall('./total/array/set/set'):
                spin_data = []
                for gridpoint in spin.findall('r'):
                    spin_data.append([float(e) for e in gridpoint.text.strip().split()])
                total_dos_data[spin.attrib['comment'].replace(' ', '_')] = spin_data
        return total_dos_data

    def read_fermi_energy(self):
        """
        :return: the Fermi energy in eV
        :rtype: float or None
        """
        try:
            fermi_energy = float(self.xmlroot.find('./calculation/dos/i').text.strip())
        except (AttributeError, TypeError) as error:
            fermi_energy = None
        return fermi_energy

    def read_band_occupations(self):
        """Read occupation of every band at every k-point for each spin channel.

        :return: {'spin_1': {kpoint_1: {'band_energy': [band1, ...], 'occupation': [occ1, ...]}, 'kpoint_2': ...}}
        :rtype: dict(str, dict(int, dict(str, list(float))))
        """
        occupations_dict = {}
        if self.xmlroot is not None:
            final_ionic_step = self.xmlroot.findall('calculation')[-1]
            eigenvalues = final_ionic_step.find('eigenvalues')
            if eigenvalues is not None:
                for spin_set in eigenvalues.findall('./array/set/set'):
                    spin = spin_set.attrib['comment'].replace(' ', '_')
                    occupations_dict[spin] = {}
                    for kpoint_set in spin_set.findall('./set'):
                        kpoint = int(kpoint_set.attrib['comment'].split()[-1])
                        occupations_dict[spin][kpoint] = {'band_energy': [], 'occupation': []}
                        for band in kpoint_set.findall('./r'):
                            be, occ = [float(b) for b in band.text.strip().split()]
                            occupations_dict[spin][kpoint]['band_energy'].append(be)
                            occupations_dict[spin][kpoint]['occupation'].append(occ)
        return occupations_dict

    def read_run_timestamp(self):
        """Read the time and date when the calulation was run.

        :return: year, month, day, hour, minute, second when the calculation was run.
        :rtype: `datetime.datetime` object
        """
        if self.xmlroot is not None:
            date_and_time = self.xmlroot.findall('./generator/i')
            year = month = day = hour = minute = second = 0
            for field in date_and_time:
                if field.attrib['name'] == 'date':
                    year, month, day = [int(f) for f in field.text.strip().split()]
                if field.attrib['name'] == 'time':
                    hour, minute, second = [int(f) for f in field.text.strip().split(':')]
            return datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

    def read_scf_looptimes(self):
        """Read total time taken for each SCF loop during the run.

        :return: {ionic_step_1: [t1, t2, t3, ...], ionic_step_2: [t1, t2, ...], ...}
        :rtype: dict(int, list(float))
        """
        scf_looptimes = {}
        if self.xmlroot is not None:
            ionic_steps = self.xmlroot.findall('./calculation')
            for n_ionic_step, ionic_step in enumerate(ionic_steps):
                scsteps = ionic_step.findall('scstep')
                scstep_times = []
                for scstep in scsteps:
                    for time in scstep.findall('time'):
                        if time.attrib['name'] == 'total':
                            scstep_times.append(float(time.text.strip().split()[-1]))
                scf_looptimes[n_ionic_step] = scstep_times
        return scf_looptimes


class VaspOutcarParserError(Exception):
    """Base class to handle errors related to parsing the VASP OUTCAR file."""


class VaspOutcarParser(object):
    """Base class to parse relevant output from a VASP OUTCAR file. Currently only for data not present in the
    vasprun.xml file. For example, atom-projected charge and magnetic moment information.
    """

    def __init__(self, vasp_outcar_file=None):
        """
        :param vasp_outcar_file: name of the VASP OUTCAR file (default: None)
        :type vasp_outcar_file: str or None
        """
        self._vasp_outcar_file = None
        self._outcar = None

        self.vasp_outcar_file = vasp_outcar_file
        self._n_ions = self._get_n_ions()

    @property
    def vasp_outcar_file(self):
        return self._vasp_outcar_file

    @vasp_outcar_file.setter
    def vasp_outcar_file(self, vasp_outcar_file):
        if vasp_outcar_file is None:
            return
        if not os.path.isfile(vasp_outcar_file):
            error_message = 'Cannot find the specified VASP OUTCAR file: {}'.format(vasp_outcar_file)
            raise VaspOutcarParserError(error_message)
        self._vasp_outcar_file = os.path.abspath(vasp_outcar_file)
        self._outcar = self._get_outcar_contents()

    def _get_outcar_contents(self):
        """Return the contents of a given VASP OUTCAR file."""
        if self.vasp_outcar_file is None:
            return
        if os.path.splitext(self.vasp_outcar_file)[-1] == '.gz':
            try:
                with gzip.open(self.vasp_outcar_file, 'rb') as fr:
                    return fr.read().decode('utf-8')
            except OSError:
                pass
        with open(self.vasp_outcar_file, 'r') as fr:
            return fr.read()

    @property
    def outcar(self):
        return self._outcar

    def _get_n_ions(self):
        if self.outcar is None:
            return
        outcar_lines = self.outcar.splitlines()
        for line in outcar_lines:
            if 'NIONS' in line:
                n_ions = int(line.strip().split()[-1])
                return n_ions

    @property
    def n_ions(self):
        return self._n_ions

    def read_orb_projected_charge(self):
        """Read the orbital-projected charge block (example below) in a VASP OUTCAR file, if present.

         total charge

        # of ion       s       p       d       tot
        ------------------------------------------
            1        0.476   0.546   7.466   8.488
            2        0.476   0.545   7.465   8.486
            3        2.192   6.110   1.929  10.231
            4        2.192   6.110   1.935  10.237
            ...
           12        0.470   0.560   6.454   7.485
        --------------------------------------------------
        tot         14.948  32.175  35.925  83.048

        :return: {atom1: {'s': charge_s1, 'p': charge_p1, ...}, 2: {...}, ...}
        :rtype: dict(int, dict(str, float))
        """
        if self.outcar is None:
            return
        outcar_lines = self.outcar.splitlines()
        start_index = None
        for r_index, line in enumerate(outcar_lines[::-1]):
            if 'total charge' in line:
                if '# of ion' in outcar_lines[len(outcar_lines) - r_index + 1]:
                    start_index = len(outcar_lines) - r_index - 1
                    break
        if start_index is None or start_index < 0:
            return
        keys = outcar_lines[start_index+2].strip().split()[3:]
        charges = {}
        if self.n_ions is not None:
            for line in outcar_lines[start_index+4:start_index+4+self.n_ions]:
                index = int(line.strip().split()[0])
                charges[index] = dict([(k, float(v)) for k, v in zip(keys, line.strip().split()[1:])])
            return charges
        else:
            for line in outcar_lines[start_index+4:]:
                if line.startswith('----------------') or not line.strip():
                    break
                index = int(line.strip().split()[0])
                charges[index] = dict([(k, float(v)) for k, v in zip(keys, line.strip().split()[1:])])
            return charges

    def read_orb_projected_magnetization(self):
        """Read the orbital-projected magnetization block (example below) in a VASP OUTCAR file, if present.

         magnetization (x)

        # of ion       s       p       d       tot
        ------------------------------------------
            1       -0.000   0.018   0.033   0.050
            2       -0.000   0.018   0.034   0.052
            3       -0.003   0.004  -0.009  -0.008
            4       -0.002   0.004  -0.016  -0.014
            5       -0.008   0.001  -0.187  -0.195
            6       -0.008   0.000  -0.187  -0.196
            ...
           11        0.008   0.031   1.069   1.108
           12        0.009   0.030   1.058   1.097
        --------------------------------------------------
        tot         -0.005   0.147   1.792   1.934

        :return: {atom1: {'s': magmom_s1, 'p': magmom_p1, ...}, atom2: ...}
        :rtype: dict(int, dict(str, float))
        """
        if self.outcar is None:
            return
        outcar_lines = self.outcar.splitlines()
        start_index = None
        for r_index, line in enumerate(outcar_lines[::-1]):
            if 'magnetization (x)' in line:
                if '# of ion' in outcar_lines[len(outcar_lines) - r_index + 1]:
                    start_index = len(outcar_lines) - r_index - 1
                    break
        if start_index is None or start_index < 0:
            return
        keys = outcar_lines[start_index+2].strip().split()[3:]
        moments = {}
        if self.n_ions is not None:
            for line in outcar_lines[start_index+4:start_index+4+self.n_ions]:
                index = int(line.strip().split()[0])
                moments[index] = dict([(k, float(v)) for k, v in zip(keys, line.strip().split()[1:])])
            return moments
        else:
            for line in outcar_lines[start_index+4:]:
                if line.startswith('----------------') or not line.strip():
                    break
                index = int(line.strip().split()[0])
                moments[index] = dict([(k, float(v)) for k, v in zip(keys, line.strip().split()[1:])])
            return moments
