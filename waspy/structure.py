import numpy
from collections import defaultdict
from waspy.data import STD_ATOMIC_WEIGHTS


class AtomError(Exception):
    """Base class for error(s) in Atom objects."""
    pass


class Atom(object):
    """Base class to store an atom."""

    def __init__(self,
                 coordinates=None,
                 species=None):
        """Constructor.

        :param coordinates: Iterable of the x, y, z coordinates of the atom (fractional or cartesian)
        :param species: Elemental species at the site.
        """
        self._coordinates = None
        self.coordinates = coordinates

        self._species = None
        self.species = species

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates):
        if coordinates is None:
            error_message = 'Atomic coordinates must be specified'
            raise AtomError(error_message)
        try:
            coord = numpy.array(coordinates, dtype='float')
        except ValueError:
            error_message = 'Could not convert atomic coordinates into float'
            raise AtomError(error_message)
        else:
            if numpy.shape(coord) != (3,):
                error_message = 'coordinates must be a 1x3-shaped iterable'
                raise AtomError(error_message)
            for i in range(3):
                if numpy.isnan(coord[i]):
                    error_message = 'Atom coordinate ({}) is None'.format(i)
                    raise AtomError(error_message)
        self._coordinates = coord.tolist()

    @property
    def species(self):
        return self._species

    @species.setter
    def species(self, species):
        if species is None:
            error_message = 'Atomic species at the site must be specified'
            raise AtomError(error_message)
        try:
            if not any([species.startswith(e) for e in STD_ATOMIC_WEIGHTS]):
                error_message = 'Species label must start with a known element symbol'
                raise AtomError(error_message)
        except AttributeError:
            error_message = 'Atomic species input must be a String'
            raise AtomError(error_message)
        else:
            self._species = species

    @property
    def x(self):
        return self._coordinates[0]

    @property
    def y(self):
        return self._coordinates[1]

    @property
    def z(self):
        return self._coordinates[2]

    @property
    def element(self):
        return self._species


class StructureError(Exception):
    """Base class for error(s) in Structure objects."""
    pass


class Structure(object):
    """Base class to store a crystal structure."""

    def __init__(self,
                 scaling_constant=None,
                 lattice_vectors=None,
                 coordinate_system=None,
                 atoms=None,
                 comment=None):
        """Constructor.

        :param scaling_constant: Float to scale all the lattice vectors with. Defaults to 1.0
        :param lattice_vectors: A 3x3 Iterable of Float with the cell vectors.
        :param atoms: List of `waspy.Atom' objects.
        :param coordinate_system: String specifying the coordinate system ("Cartesian"/"Direct")
        """

        self._scaling_constant = None
        self.scaling_constant = scaling_constant

        self._lattice_vectors = None
        self.lattice_vectors = lattice_vectors

        self._coordinate_system = None
        self.coordinate_system = coordinate_system

        self._atoms = None
        self.atoms = atoms

        self._comment = None
        self.comment = comment

    @property
    def scaling_constant(self):
        return self._scaling_constant

    @scaling_constant.setter
    def scaling_constant(self, scaling_constant):
        if scaling_constant is None:
            self._scaling_constant = 1.0
        else:
            try:
                self._scaling_constant = float(scaling_constant)
            except ValueError:
                error_message = 'Could not convert scaling constant to float'
                raise StructureError(error_message)

    @property
    def lattice_vectors(self):
        return self._lattice_vectors

    @lattice_vectors.setter
    def lattice_vectors(self, lattice_vectors):
        if lattice_vectors is None:
            return
        try:
            lv = numpy.array(lattice_vectors, dtype='float')
        except ValueError:
            error_message = 'Could not convert lattice vector component(s) into float'
            raise StructureError(error_message)
        else:
            if numpy.shape(lv) != (3, 3):
                error_message = '`lattice_vectors` must be a 3x3-shaped iterable'
                raise StructureError(error_message)
            for i in range(3):
                for j in range(3):
                    if numpy.isnan(lv[i][j]):
                        error_message = 'Lattice vector component ({}, {}) is None'.format(i, j)
                        raise StructureError(error_message)
            self._lattice_vectors = lv.tolist()

    @property
    def coordinate_system(self):
        return self._coordinate_system

    @coordinate_system.setter
    def coordinate_system(self, coordinate_system):
        if coordinate_system is None:
            return
        elif coordinate_system.lower() in ['direct', 'crystal', 'fractional']:
            self._coordinate_system = 'Direct'
        elif coordinate_system.lower() in ['cartesian', 'angstrom']:
            self._coordinate_system = 'Cartesian'
        else:
            error_message = 'Coordinate system not recognized. Options: Direct/Crystal/Fractional or Cartesian/Angstrom'
            raise StructureError(error_message)

    @property
    def atoms(self):
        return self._atoms

    @atoms.setter
    def atoms(self, atoms):
        if atoms is None:
            self._atoms = []
            return
        if not all([isinstance(atom, Atom) for atom in atoms]):
            error_message = '`atoms` must be an iterable of `waspy.Atom` objects'
            raise StructureError(error_message)
        self._atoms = atoms

    def add_atom(self, atom):
        if not isinstance(atom, Atom):
            error_message = '`atom` must be a `waspy.Atom` object'
            raise StructureError(error_message)
        self._atoms.append(atom)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        if comment is None:
            comment = 'Comment'
        self._comment = comment

    @property
    def composition_dict(self):
        if self.atoms is None:
            return {}
        composition_dict = defaultdict(int)
        for atom in self.atoms:
            composition_dict[atom.species] += 1
        return composition_dict

    @property
    def list_of_species(self):
        if self.atoms is None:
            return []
        return sorted(set([atom.species for atom in self.atoms]))

    def _get_vasp_poscar(self):
        """Construct the VASP POSCAR.

        :return: String with the contents of a VASP 5 POSCAR file
        """
        poscar = []

        # system title
        poscar.append(self.comment)

        # scaling factor
        poscar.append('{:18.14f}'.format(self.scaling_constant))

        # lattice_vectors
        if self.lattice_vectors is None:
            error_message = 'Lattice vectors not specified'
            raise StructureError(error_message)
        for lv in self.lattice_vectors:
            poscar.append('  '.join(['{:>18.14f}'.format(_lv) for _lv in lv]))

        # list of species, number of atoms, coordinate_system, atomic coordinates
        if self.atoms is None:
            error_message = 'No atoms in the structure'
            raise StructureError(error_message)
        if self.coordinate_system is None:
            error_message = 'No coordinate system specified'
            raise StructureError(error_message)
        # list of species
        poscar.append(' '.join(['{:>4s}'.format(species) for species in self.list_of_species]))
        # list of number of atoms of each species
        poscar.append(' '.join(['{:>4d}'.format(self.composition_dict[e]) for e in self.list_of_species]))
        # coordinate system
        poscar.append('{}'.format(self.coordinate_system))
        # list of atomic coordinates
        for species in self.list_of_species:
            for atom in self.atoms:
                if atom.species == species:
                    poscar.append('  '.join(['{:>18.14f}'.format(ac) for ac in atom.coordinates]))
        return '\n'.join(poscar)

    @property
    def POSCAR(self):
        """Structure in the VASP 5 POSCAR format."""
        return self._get_vasp_poscar()

