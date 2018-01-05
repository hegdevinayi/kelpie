import os
from kelpie.structure import Atom
from kelpie.structure import Structure
from kelpie.data import STD_ATOMIC_WEIGHTS


class KelpieIOError(Exception):
    """Base class for I/O related error handling."""
    pass


def read_poscar(poscar_file='POSCAR'):
    """
    :param poscar_file: Location of the VASP POSCAR (version 5) file
                        NOTE: Names of all species (line 6) need to begin with the symbol of a real element.
    :return: `kelpie.structure.Structure` object
    """
    if not os.path.isfile(poscar_file):
        error_message = 'Specified POSCAR file {} not found'.format(poscar_file)
        raise FileNotFoundError(error_message)

    with open(poscar_file, 'r') as fr:
        poscar_lines = [line.strip() for line in fr.readlines()]

    if not _consistent_number_of_atoms(poscar_lines):
        error_message = 'Mismatch between the number of atoms (Line 7) and the number of atomic coordinates (Lines 9-)'
        raise KelpieIOError(error_message)

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
        poscar_as_dict[block] = globals()['_{}'.format(block)](poscar_lines)

    s = Structure()
    s.comment = poscar_as_dict['system_title']
    s.scaling_constant = poscar_as_dict['scaling_constant']
    s.lattice_vectors = poscar_as_dict['lattice_vectors']
    s.coordinate_system = poscar_as_dict['coordinate_system']
    for ac, sp in zip(poscar_as_dict['list_of_atomic_coordinates'], poscar_as_dict['repeating_list_of_species']):
        atom = Atom(coordinates=ac, species=sp)
        s.add_atom(atom)

    return s


def _consistent_number_of_atoms(poscar_lines):
    """Is the total number of atoms (Line 7) consistent with the number of atomic coordinates specified?

    :return: Boolean """
    return len(_repeating_list_of_species(poscar_lines)) == len(_list_of_atomic_coordinates(poscar_lines))


def _system_title(poscar_lines):
    """:return: String with the system title
    """
    return poscar_lines[0]


def _scaling_constant(poscar_lines):
    """ Parse the scaling constant for the structure (line 2).

    :return: Float with the scaling constant
    :raise KelpieIOError: if the scaling constant cannot be converted to float
    """
    try:
        scaling_constant = float(poscar_lines[1])
    except ValueError:
        error_message = 'Scaling factor (Line 2 in POSCAR) should be float'
        raise KelpieIOError(error_message)
    else:
        return scaling_constant


def _lattice_vectors(poscar_lines):
    """Parse the lattice vectors of the structure (lines 3-5).

    :return: 3x3-shaped List of Float with the lattice vectors [[a11, a12, a13], [a21, a22, a23], ...]
    :raise KelpieIOError: if any lattice vector component cannot be converted to float
    """
    lattice_vectors = []
    try:
        for line in poscar_lines[2:5]:
            lattice_vectors.append([float(a) for a in line.split()])
    except ValueError:
        error_message = 'Lattice vector components (Lines 3-5) should be floating point'
        raise KelpieIOError(error_message)
    else:
        return lattice_vectors


def _list_of_species(poscar_lines):
    """Parse the species in the structure (line 6).

    :return: List of String with the species symbols
    :raise KelpieIOError: if any of the species names contains only integers
    """
    species_list = poscar_lines[5].split()
    for species in species_list:
        if not any([species.startswith(e) for e in STD_ATOMIC_WEIGHTS]):
            error_message = 'All species names (Line 6) must begin with the symbol of a real element.'
            error_message += '\nNOTE: Only VASP 5 POSCAR format is supported'
            raise KelpieIOError(error_message)
    return species_list


def _list_of_number_of_atoms(poscar_lines):
    """Parse the number of atoms of each species in the structure (line 7).

    :return: List of Int with the number of atoms of each species
    :raise KelpieIOError: if any of the number of atoms cannot be converted to int
    """
    try:
        list_of_number_of_atoms = [int(n) for n in poscar_lines[6].split()]
    except ValueError:
        error_message = 'Number of atoms of each species (Line 7) should be integers'
        raise KelpieIOError(error_message)
    else:
        return list_of_number_of_atoms


def _repeating_list_of_species(poscar_lines):
    repeating_list_of_species = []
    for s, n in zip(_list_of_species(poscar_lines), _list_of_number_of_atoms(poscar_lines)):
        repeating_list_of_species += [s]*n
    return repeating_list_of_species


def _coordinate_system(poscar_lines):
    """
    Are the atomic positions in direct/fractional or cartesian coordinates? (line 8)

    :return: "Direct" or "Cartesian"
    :raise NotImplementedError: for Selective Dynamics
    :raise KelpieIOError: if coordinate system is not VASP-recognizable
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
        raise KelpieIOError(error_message)


def _list_of_atomic_coordinates(poscar_lines):
    """
    Parse all the atomic coordinates (line 9-(9+number of atoms)).

    :return: Nx3-shaped List of Float with the atomic coordinates [[c11, c12, c13], [c21, c22, c23], ...]
    :raise KelpieIOError: if any atomic coordinate component cannot be converted to float
    """
    atomic_coordinates = []
    for i, line in enumerate(poscar_lines[8:]):
        if line[0] == '#':
            break
        try:
            coord = [float(c) for c in line.split()[:3]]
        except ValueError:
            error_message = 'Check the atomic coordinates block (Line {}) for non-float values'.format(9+i)
            raise KelpieIOError(error_message)
        else:
            atomic_coordinates.append(coord)
        if i == sum(_list_of_number_of_atoms(poscar_lines))-1:
            break
    return atomic_coordinates
