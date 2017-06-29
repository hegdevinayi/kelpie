import os
import sys


class VASPStructure:
    """Base class to store a crystal structure."""

    def __init__(self, poscar_file='POSCAR'):
        """
        :param poscar_file (str): name/relative path of the POSCAR (default='POSCAR')
        """
        self.poscar_file = os.path.abspath(poscar_file)
        self.poscar_lines = self._read_poscar_file()
        self.system_title = self.get_system_title()
        self.scaling_factor = self.get_scaling_factor()
        self.lattice_vectors = self.get_lattice_vectors()
        self.elements_list = self.get_list_of_elements()
        self.number_of_atoms_list = self.get_list_of_number_of_atoms()
        self.coord_system = self.get_coord_system()
        self.atom_coordinates_list = self.get_list_of_atomic_positions()

    def _read_poscar_file(self):
        """
        Read a structure in the VASP 5 format.
        :return: lines (str) in the POSCAR file, with linebreaks stripped ['title', '1.0', ...]
        :rtype: list of str
        """
        if not os.path.isfile(self.poscar_file):
            err_msg = 'POSCAR file not found'
            raise FileNotFoundError(err_msg)
        with open(self.poscar_file, 'r') as fr:
            return [line.strip() for line in fr.readlines()]

    def get_system_title(self):
        """
        Parse, literally, the system title (line 1)
        :return: system title
        :rtype: str
        """
        return self.poscar_lines[0]

    def get_scaling_factor(self):
        """
        Parse the scaling factor for the structure (line 2)
        :return: scaling factor
        :rtype: float
        """
        try:
            scaling_factor = float(self.poscar_lines[1])
        except TypeError:
            sys.stdout.write('[Error] Scaling factor (Line 2) should be floating point.\n')
            return None
        else:
            return scaling_factor

    def get_lattice_vectors(self):
        """
        Parse the lattice vectors of the structure (lines 3-5)
        :return: lattice vectors [[a11, a12, a13], [a21, a22, a23], ...]
        :rtype: list of three 1x3 lists of float
        """
        lattice_vectors = []
        try:
            for line in self.poscar_lines[2:5]:
                lattice_vectors.append([float(a) for a in line.split()])
        except TypeError:
            sys.stdout.write('[Error] Check the lattice vectors block (Lines 3-5).\n')
            return None
        else:
            return lattice_vectors

    def get_list_of_elements(self):
        """
        Parse the elements in the compound (line 6)
        :return: list of elements
        :rtype: list of str
        """
        elements_list = self.poscar_lines[5].split()
        # check if all are legitimate elements?
        if any([e.isdigit() for e in elements_list]):
            sys.stdout.write('[Error] List of elements missing from POSCAR (Line 6). Use VASP 5 format.\n')
            return None
        return elements_list

    def get_list_of_number_of_atoms(self):
        """
        Parse the number of atoms of each element in the structure (line 7)
        :return: list of number of atoms
        :rtype: list of int
        """
        try:
            number_of_atoms_list = [int(n) for n in self.poscar_lines[6].split()]
        except TypeError:
            sys.stdout.write('[Error] Check the number of atoms of each kind (Line 7).\n')
            return None
        else:
            return number_of_atoms_list

    def get_coord_system(self):
        """
        Are the atomic positions in direct/fractional or cartesian coordinates? (line 8)
        :return: 'Direct' or 'Cartesian'
        :rtype: str
        """
        coord_system = self.poscar_lines[7]
        first_char = coord_system.lower()[0] # VASP only recognizes the first character in the line
        if first_char == 'd':
            return 'Direct'
        elif first_char in ['c', 'k']:
            return 'Cartesian'
        elif first_char == 's':
            err_msg = 'Selective dynamics I/O not currently implemented'
            raise NotImplementedError(err_msg)
        else:
            sys.stdout.write('[Error] Check the coordinate system specified (Line 8).\n')
            return None

    def get_list_of_atomic_positions(self):
        atomic_coordinates = []
        for line in self.poscar_lines[8:]:
            try:
                coord = [float(c) for c in line.split()[:3]]
            except TypeError:
                sys.stdout.write('[Error] Check the atomic coordinates block (Line 9-).\n')
            else:
                atomic_coordinates.append(coord)
        return atomic_coordinates


