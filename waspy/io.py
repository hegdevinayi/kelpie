import os
from waspy.structure import Atom
from waspy.structure import Structure, StructureError
from waspy.data import STD_ATOMIC_WEIGHTS


class WaspyIOError(Exception):
    """Base class for I/O related error handling."""
    pass


def read_poscar(poscar_file='POSCAR'):
    """
    :param poscar_file: Location of the VASP POSCAR (version 5) file
                        NOTE: Names of all species (line 6) need to begin with the symbol of a real element.
    :return: `waspy.structure.Structure` object
    """
    if not os.path.isfile(poscar_file):
        error_message = 'Specified POSCAR file {} not found'.format(poscar_file)
        raise FileNotFoundError(error_message)

    with open(poscar_file, 'r') as fr:
        poscar_lines = [line.strip() for line in fr.readlines()]

    poscar_blocks = ['system_title',
                     'scaling_constant',
                     'lattice_vectors',
                     'list_of_species',
                     'list_of_number_of_atoms',
                     'repeating_list_of_species',
                     'coordinate_system',
                     'list_of_atomic_coordinates'
                     ]

    poscar_as_dict = {}
    for block in poscar_blocks:
        poscar_as_dict[block] = globals()['_get_{}'.format(block)](poscar_lines)

    if len(poscar_as_dict['repeating_list_of_species']) != len(poscar_as_dict['list_of_atomic_coordinates']):
        error_message = 'Mismatch between the number of atoms (Line 7) and the number of atomic coordinates (Lines 9-)'
        raise WaspyIOError(error_message)

    s = Structure()
    s.comment = poscar_as_dict['system_title']
    s.scaling_constant = poscar_as_dict['scaling_constant']
    s.lattice_vectors = poscar_as_dict['lattice_vectors']
    s.coordinate_system = poscar_as_dict['coordinate_system']
    for ac, sp in zip(poscar_as_dict['list_of_atomic_coordinates'], poscar_as_dict['repeating_list_of_species']):
        atom = Atom(coordinates=ac, species=sp)
        s.add_atom(atom)

    return s


def _get_system_title(poscar_lines):
    """:return: String with the system title
    """
    return poscar_lines[0]


def _get_scaling_constant(poscar_lines):
    """ Parse the scaling constant for the structure (line 2).

    :return: Float with the scaling constant
    :raise WaspyIOError: if the scaling constant cannot be converted to float
    """
    try:
        scaling_constant = float(poscar_lines[1])
    except ValueError:
        error_message = 'Scaling factor (Line 2 in POSCAR) should be float'
        raise WaspyIOError(error_message)
    else:
        return scaling_constant


def _get_lattice_vectors(poscar_lines):
    """Parse the lattice vectors of the structure (lines 3-5).

    :return: 3x3-shaped List of Float with the lattice vectors [[a11, a12, a13], [a21, a22, a23], ...]
    :raise WaspyIOError: if any lattice vector component cannot be converted to float
    """
    lattice_vectors = []
    try:
        for line in poscar_lines[2:5]:
            lattice_vectors.append([float(a) for a in line.split()])
    except ValueError:
        error_message = 'Lattice vector components (Lines 3-5) should be floating point'
        raise WaspyIOError(error_message)
    else:
        return lattice_vectors


def _get_list_of_species(poscar_lines):
    """Parse the species in the structure (line 6).

    :return: List of String with the species symbols
    :raise WaspyIOError: if any of the species names contains only integers
    """
    species_list = poscar_lines[5].split()
    for species in species_list:
        if not any([species.startswith(e) for e in STD_ATOMIC_WEIGHTS]):
            error_message = 'All species names (Line 6) must begin with the symbol of a real element.'
            error_message += '\nNOTE: Only VASP 5 POSCAR format is supported'
            raise WaspyIOError(error_message)
    return species_list


def _get_list_of_number_of_atoms(poscar_lines):
    """Parse the number of atoms of each species in the structure (line 7).

    :return: List of Int with the number of atoms of each species
    :raise WaspyIOError: if any of the number of atoms cannot be converted to int
    """
    try:
        list_of_number_of_atoms = [int(n) for n in poscar_lines[6].split()]
    except ValueError:
        error_message = 'Number of atoms of each species (Line 7) should be integers'
        raise WaspyIOError(error_message)
    else:
        return list_of_number_of_atoms


def _get_repeating_list_of_species(poscar_lines):
    repeating_list_of_species = []
    for s, n in zip(_get_list_of_species(poscar_lines), _get_list_of_number_of_atoms(poscar_lines)):
        repeating_list_of_species += [s]*n
    return repeating_list_of_species


def _get_coordinate_system(poscar_lines):
    """
    Are the atomic positions in direct/fractional or cartesian coordinates? (line 8)

    :return: "Direct" or "Cartesian"
    :raise NotImplementedError: for Selective Dynamics
    :raise WaspyIOError: if coordinate system is not VASP-recognizable
    """
    coordinate_system = poscar_lines[7]
    first_char = coordinate_system.lower()[0]  # VASP only recognizes the first character
    if first_char == 'd':
        return 'Direct'
    elif first_char in ['c', 'k']:
        return 'Cartesian'
    elif first_char == 's':
        error_message = 'Selective dynamics I/O handling currently not implemented'
        raise NotImplementedError(error_message)
    else:
        error_message = 'Coordinate system (Line 8) can only be direct or cartesian'
        raise WaspyIOError(error_message)


def _get_list_of_atomic_coordinates(poscar_lines):
    """
    Parse all the atomic coordinates (line 9-(9+number of atoms)).

    :return: Nx3-shaped List of Float with the atomic coordinates [[c11, c12, c13], [c21, c22, c23], ...]
    :raise WaspyIOError: if any atomic coordinate component cannot be converted to float
    """
    atomic_coordinates = []
    for i, line in enumerate(poscar_lines[8:8+sum(_get_list_of_number_of_atoms(poscar_lines))]):
        try:
            coord = [float(c) for c in line.split()[:3]]
        except ValueError:
            error_message = 'Check the atomic coordinates block (Line {}) for non-float values'.format(9+i)
            raise WaspyIOError(error_message)
        else:
            atomic_coordinates.append(coord)
    return atomic_coordinates
