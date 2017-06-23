import os
import sys
from bs4 import BeautifulSoup
import numpy as np
import gzip

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
        self.elements_list = self.get_elements_list()
        self.number_of_atoms_list = self.get_number_of_atoms_list()
        self.coord_system = self.get_coord_system()
        self.atoms_list = self.get_atoms_list()

    def _read_poscar_file(self):
        """
        Read a structure in the VASP 5 format.
        :return: lines (str) in the POSCAR file, with linebreaks stripped ['title', '1.0', ...]
        :rtype: list of str
        """
        if not os.path.isfile(self.poscar_file):
            sys.stdout.write('[Error] POSCAR file not found.\n')
            return
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
            return scaling_factor
        except TypeError:
            sys.stdout.write('[Error] Scaling factor (Line 2) should be floating point.\n')
            return

    def get_lattice_vectors(self):
        """
        Parse the lattice vectors of the structure (lines 3-5)
        :return: lattice vectors [[a11, a12, a13], [a21, a22, a23], ...]
        :rtype: list of 1x3 lists of float
        """
        try:
            lattice_vectors = []
            for line in self.poscar_lines[2:5]:
                lattice_vectors.append([float(a) for a in line.split()])
            return lattice_vectors
        except TypeError:
            sys.stdout.write('[Error] Check the lattice vectors block (Lines 3-5).\n')
            return

    def get_elements_list(self):
        """
        Parse the elements in the compound (line 6)
        :return: list of elements
        :rtype: list of str
        """
        elements_list = self.poscar_lines[5].split()
        # assert that each element is str and in the list of elements
        # VASP 4?
        return elements_list

    def get_number_of_atoms_list(self):
        """
        Parse the number of atoms of each element in the structure (line 7)
        :return: list of number of atoms
        :rtype: list of int
        """
        try:
            number_of_atoms_list = [int(n) for n in self.poscar_lines[6].split()]
            return number_of_atoms_list
        except TypeError:
            sys.stdout.write('[Error] Check the number of atoms of each kind (Line 7).\n')
            return

    def get_coord_system(self):
        return

    def get_atoms_list(self):
        return

