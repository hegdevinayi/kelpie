import os
import sys
from bs4 import BeautifulSoup
import numpy as np
import gzip


class VasprunXMLParser:
    """Base class to parse relevant output from a vasprun.xml file."""

    def __init__(self, vasprun_xml_file='vasprun.xml'):
        """
        :param vasprun_xml_file: name of the vasprun.xml file (default='vasprun.xml')
        :type vasprun_xml_file: str
        """
        self.vasprun_xml_file = os.path.abspath(vasprun_xml_file)
        self.vasprun_soup = self._xml_to_soup(self.vasprun_xml_file)

    @staticmethod
    def _xml_to_soup(xml_file, from_encoding='ISO-8859-1'):
        """Read contents from a vasprun.xml or vasprun.xml.gz file and convert it into soup.
        
        :param from_encoding: encoding of the XML document (default='ISO-8859-1')
        :type from_encoding: str
        :return: a BeautifulSoup object of the XML data
        :rtype: bs4.BeautifulSoup
        """
        sys.stdout.write('Reading file {}.'.format(xml_file))
        sys.stdout.write(' Making soup from XML stream...')
        sys.stdout.flush()
        if 'gz' in os.path.splitext(xml_file)[-1]:
            with gzip.open(xml_file, 'rb') as xml_stream:
                soup = BeautifulSoup(xml_stream, 'xml', from_encoding=from_encoding)
        else:
            with open(xml_file, 'rb') as xml_stream:
                soup = BeautifulSoup(xml_stream, 'xml', from_encoding=from_encoding)
        sys.stdout.write(' done.\n')
        sys.stdout.flush()
        return soup

    def read_composition(self):
        """Read the species and number of atoms for each species in the unit cell.
        
        :return: unit cell composition dictionary {'element1': n1, 'element2': n2, ...}
        :rtype: dict
        """
        atomtypes_array = self.vasprun_soup.modeling.atominfo.find_all('array', recursive=False)
        composition_dict = {}
        for array in atomtypes_array:
            if array['name'] != 'atomtypes':
                continue
            for species in array.set.find_all('rc', recursive=False):
                natoms, element, *others = [c.string.strip() for c in species.find_all('c', recursive=False)]
                composition_dict.update({element: int(natoms)})
        return composition_dict

    def read_atomslist(self):
        """Read the list of atoms in the unit cell.
        
        :return: list of atoms ['atom1', 'atom1', 'atom2', 'atom2', 'atom2', ...]
        :rtype: list
        """
        atomtypes_array = self.vasprun_soup.modeling.atominfo.find_all('array', recursive=False)
        atomslist = []
        for array in atomtypes_array:
            if array['name'] != 'atoms':
                continue
            for species in array.set.find_all('rc', recursive=False):
                atom, atomtype = [c.string.strip() for c in species.find_all('c', recursive=False)]
                atomslist.append(atom)
        return atomslist

    def read_number_of_ionic_steps(self):
        """Read number of ionic steps in the VASP run.
        
        :return: number of ionic steps
        :rtype: int
        """
        return len(self.vasprun_soup.modeling.find_all('calculation', recursive=False))

    def read_scf_energies(self):
        """Read all the the energies in every ionic step.
        
        :return: {ionic_step_1: [e1, e2, e3, ...], ionic_step_2: [e1, e2, ...], ionic_step_3: ...}
        :rtype: dict(int, list(float))
        """
        ionic_steps = self.vasprun_soup.modeling.find_all('calculation', recursive=False)
        scf_energies = {}
        for n_ionic_step, ionic_step in enumerate(ionic_steps):
            scsteps = ionic_step.find_all('scstep', recursive=False)
            scstep_energies = []
            for scstep in scsteps:
                for energy in scstep.energy.find_all('i', recursive=False):
                    if energy['name'] == 'e_fr_energy':
                        scstep_energies.append(float(energy.string.strip()))
            scf_energies[n_ionic_step] = scstep_energies
        return scf_energies

    def read_entropy(self):
        """Read entropy at the end of each ionic step.
        
        :return: {ionic_step_1: entropy_1, ionic_step_2: entropy_2, ionic_step_3: ...}
        :rtype: dict(int, float)
        """
        ionic_steps = self.vasprun_soup.modeling.find_all('calculation', recursive=False)
        entropy_dict = {}
        for n_ionic_step, ionic_step in enumerate(ionic_steps):
            entropy = None
            final_scstep = ionic_step.find_all('scstep', recursive=False)[-1]
            for final_energy_block in final_scstep.find_all('energy', recursive=False):
                for energy in final_energy_block.find_all('i', recursive=False):
                    if energy['name'] == 'eentropy':
                        entropy = float(energy.string.strip())
            entropy_dict[n_ionic_step] = entropy
        return entropy_dict

    def read_free_energy(self):
        """Read free energy at the end of each ionic step.
        
        :return: {ionic_step_1: free_energy_1, ionic_step_2: free_energy_2, ionic_step_3: ...}
        :rtype: dict(int, float)
        """
        ionic_steps = self.vasprun_soup.modeling.find_all('calculation', recursive=False)
        free_energy_dict = {}
        for n_ionic_step, ionic_step in enumerate(ionic_steps):
            free_energy = None
            final_scstep = ionic_step.find_all('scstep', recursive=False)[-1]
            for final_energy_block in final_scstep.find_all('energy', recursive=False):
                for energy in final_energy_block.find_all('i', recursive=False):
                    if energy['name'] == 'e_fr_energy':
                        free_energy = float(energy.string.strip())
            free_energy_dict[n_ionic_step] = free_energy
        return free_energy_dict

    def read_forces(self):
        """Read forces on all atoms in the unit cell at the end of each ionic step.
        
        :return: {ionic_step_1: [[fx_1, fy_1, fz_1], [fx_2, fy_2, fz_2], ...], ionic_step_2: ...}
        :rtype: dict(int, numpy.array)
                - numpy.array of shape (N_atoms, 3)
        """
        ionic_steps = self.vasprun_soup.modeling.find_all('calculation', recursive=False)
        forces_dict = {}
        for n_ionic_step, ionic_step in enumerate(ionic_steps):
            varrays = ionic_step.find_all('varray', recursive=False)
            forces = []
            for varray in varrays:
                if varray['name'] != 'forces':
                    continue
                for force_on_atom in varray.find_all('v', recursive=False):
                    forces.append([float(e) for e in force_on_atom.string.split()])
            forces_dict[n_ionic_step] = np.array(forces)
        return forces_dict

    def read_stress_tensor(self):
        """Read stress (in kbar) on the unit cell at the end of each ionic step.
        
        :return: {ionic_step_1: [[Sxx, Sxy, Sxz], [Syx, Syy, Syz], [Szx, Szy, Szz]], ionic_step_2: ...}
        :rtype: dict(int, numpy.array)
                - numpy.array of shape (3, 3)
        """
        ionic_steps = self.vasprun_soup.modeling.find_all('calculation', recursive=False)
        stress_tensor_dict = {}
        for n_ionic_step, ionic_step in enumerate(ionic_steps):
            varrays = ionic_step.find_all('varray', recursive=False)
            stress_tensor = []
            for varray in varrays:
                if varray['name'] != 'stress':
                    continue
                for stress_component in varray.find_all('v', recursive=False):
                    stress_tensor.append([float(e) for e in stress_component.string.split()])
            stress_tensor_dict[n_ionic_step] = np.array(stress_tensor)
        return stress_tensor_dict

    def read_lattice_vectors(self):
        """Read lattice vectors (in Angstrom) of the unit cell at the end of each ionic step.
        
        :return: {ionic_step_1: [[a11, a12, a13], [a21, a22, a23], [a31, a32, a33]], ionic_step_2: ...}
        :rtype: dict(key, numpy.array)
                - numpy.array of shape (3, 3)
        """
        ionic_steps = self.vasprun_soup.modeling.find_all('calculation', recursive=False)
        lattice_vectors_dict = {}
        for n_ionic_step, ionic_step in enumerate(ionic_steps):
            varrays = ionic_step.structure.crystal.find_all('varray', recursive=False)
            lattice_vectors = []
            for varray in varrays:
                if varray['name'] != 'basis':
                    continue
                for lattice_vector in varray.find_all('v', recursive=False):
                    lattice_vectors.append([float(e) for e in lattice_vector.string.split()])
            lattice_vectors_dict[n_ionic_step] = np.array(lattice_vectors)
        return lattice_vectors_dict

    def read_volume_of_cell(self):
        """Read the volume (in cubic Angstrom) of the unit cell at the end of each ionic step.
        
        :return: {ionic_step_1: float, ionic_step_2: float}
        :rtype: dict(int, float)
        """
        ionic_steps = self.vasprun_soup.modeling.find_all('calculation', recursive=False)
        volume_dict = {}
        for n_ionic_step, ionic_step in enumerate(ionic_steps):
            volume = float(ionic_step.structure.crystal.i.string.strip())
            volume_dict[n_ionic_step] = volume
        return volume_dict

    def read_fermi_energy(self):
        """
        :return: Fermi energy
        :rtype: float
        """
        return float(self.vasprun_soup.find('dos').i.string.strip())

    def read_occupations(self):
        """Read occupation of every band at every k-point for each spin channel.
        
        :return: {'spin_1': {kpoint_1: {'band_energy': [band1, ...], 'occupation': [occ1, ...]}, 'kpoint_2': ...}}
        :rtype: dict(str, dict(int, dict(str, list(float))))
        """
        final_ionic_step = self.vasprun_soup.modeling.find_all('calculation', recursive=False)[-1]
        eigenvalues = final_ionic_step.find('eigenvalues').set
        occupations_dict = {}
        for spin_set in eigenvalues.find_all('set', recursive=False):
            spin = spin_set['comment'].replace(' ', '_')
            occupations_dict[spin] = {}
            for kpoint_set in spin_set.find_all('set', recursive=False):
                kpoint = int(kpoint_set['comment'].split()[-1])
                occupations_dict[spin][kpoint] = {'band_energy': [], 'occupation': []}
                for band in kpoint_set.find_all('r', recursive=False):
                    be, occ = [float(b) for b in band.string.strip().split()]
                    occupations_dict[spin][kpoint]['band_energy'].append(be)
                    occupations_dict[spin][kpoint]['occupation'].append(occ)
        return occupations_dict

