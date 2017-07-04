import os
import sys


class VaspStructureError(Exception):
    """Base class for error(s) in a VASP POSCAR file."""
    pass


class VaspStructure:
    """Base class to store VASP POSCAR data."""

    def __init__(self, poscar_file='POSCAR'):
        """
        :param poscar_file: name/relative path of the POSCAR (default='POSCAR')
        :type poscar_file: str
        """
        self.poscar_file = os.path.abspath(poscar_file)
        self.poscar_lines = self._read_poscar_file()
        self.system_title = self.get_system_title()
        self.scaling_factor = self.get_scaling_factor()
        self.lattice_vectors = self.get_lattice_vectors()
        self.list_of_elements = self.get_list_of_elements()
        self.list_of_number_of_atoms = self.get_list_of_number_of_atoms()
        self.coordinate_system = self.get_coordinate_system()
        self.list_of_atomic_coordinates = self.get_list_of_atomic_coordinates()

    def _read_poscar_file(self):
        """
        Read a structure in the VASP 5 format.
        
        :return: lines in the POSCAR file, with linebreaks stripped ['title', '1.0', ...]
        :rtype: list(str)
        :raise FileNotFoundError: if the POSCAR file is not found
        """
        # sys.stdout.write('Reading POSCAR file {}... '.format(self.poscar_file))
        if not os.path.isfile(self.poscar_file):
            error_message = '{} file not found'.format(self.poscar_file)
            raise FileNotFoundError(error_message)
        with open(self.poscar_file, 'r') as fr:
            poscar_lines = [line.strip() for line in fr.readlines()]
            # sys.stdout.write('done.\n')
            return poscar_lines

    def get_system_title(self):
        """
        Parse, literally, the system title (line 1).
        
        :return: system title
        :rtype: str
        """
        return self.poscar_lines[0]

    def get_scaling_factor(self):
        """
        Parse the scaling factor for the structure (line 2).
        
        :return: scaling factor
        :rtype: float
        :raise ValueError: if the scaling factor cannot be converted to float
        """
        try:
            scaling_factor = float(self.poscar_lines[1])
        except ValueError:
            error_message = '[Error] Scaling factor (Line 2) should be floating point.\n'
            sys.stdout.write(error_message)
            raise
        else:
            return scaling_factor

    def get_lattice_vectors(self):
        """
        Parse the lattice vectors of the structure (lines 3-5).
        
        :return: lattice vectors [[a11, a12, a13], [a21, a22, a23], ...]
        :rtype: list(list(float))
                - outer list of shape (3, 3)
        :raise ValueError: if any lattice vector component cannot be converted to float
        """
        lattice_vectors = []
        try:
            for line in self.poscar_lines[2:5]:
                lattice_vectors.append([float(a) for a in line.split()])
        except ValueError:
            error_message = '[Error] All lattice vector components (Lines 3-5) should be floating point.\n'
            sys.stdout.write(error_message)
            raise
        else:
            return lattice_vectors

    def get_list_of_elements(self):
        """
        Parse the elements in the compound (line 6).
        
        :return: list of elements
        :rtype: list(str)
        :raise VaspStructureError: if any of the elements contains only integers
        """
        elements_list = self.poscar_lines[5].split()
        # check if all are legitimate elements?
        # ^ may be too restrictive; for now, allow "artificial elements"
        if any([e.isdigit() for e in elements_list]):
            error_message = '[Error] Check list of elements (Line 6). [Use VASP 5 format.]\n'
            sys.stdout.write(error_message)
            raise VaspStructureError
        return elements_list

    def get_list_of_number_of_atoms(self):
        """
        Parse the number of atoms of each element in the structure (line 7).
        
        :return: list of number of atoms
        :rtype: list(int)
        :raise ValueError: if any of the number of atoms cannot be converted to int
        """
        try:
            list_of_number_of_atoms = [int(n) for n in self.poscar_lines[6].split()]
        except ValueError:
            error_message = '[Error] Number of atoms of each species (Line 7) should be integers.\n'
            sys.stdout.write(error_message)
            raise
        else:
            return list_of_number_of_atoms

    def get_coordinate_system(self):
        """
        Are the atomic positions in direct/fractional or cartesian coordinates? (line 8)
        
        :return: 'Direct' or 'Cartesian'
        :rtype: str
        :raise NotImplementedError: for Selective Dynamics
        :raise VaspStructureError: if coordinate system is not VASP-recognizable
        """
        coordinate_system = self.poscar_lines[7]
        first_char = coordinate_system.lower()[0]  # VASP only recognizes the first character
        if first_char == 'd':
            return 'Direct'
        elif first_char in ['c', 'k']:
            return 'Cartesian'
        elif first_char == 's':
            error_message = 'Selective dynamics I/O handling currently not implemented.\n'
            raise NotImplementedError(error_message)
        else:
            error_message = '[Error] Coordinate system (Line 8) can only be direct or cartesian.\n'
            raise VaspStructureError(error_message)

    def get_list_of_atomic_coordinates(self):
        """
        Parse all the atomic coordinates (line 9-(9+number of atoms)).
        
        :return: list of atomic coordinates [[c11, c12, c13], [c21, c22, c23], ...]
        :rtype: list(list(float))
                - outer list of shape (N_atoms, 3)
        :raise ValueError: is any atomic coordinate component cannot be converted to float
        """
        atomic_coordinates = []
        for line in self.poscar_lines[8:8+sum(self.list_of_number_of_atoms)]:
            try:
                coord = [float(c) for c in line.split()[:3]]
            except ValueError:
                error_message = '[Error] Check the atomic coordinates block (Line 9-).\n'
                sys.stdout.write(error_message)
                raise
            else:
                atomic_coordinates.append(coord)
        return atomic_coordinates

    @property
    def POSCAR(self):
        poscar = ''

        # system title
        poscar += self.system_title

        # scaling factor
        poscar += '{:18.12f}'.format(self.scaling_factor)

        # lattice_vectors
        for lv in self.lattice_vectors
        # list of elements
        # list of number of atoms
        # coordinate system
        # atomic coordinates


