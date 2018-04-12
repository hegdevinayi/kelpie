import numpy
from collections import defaultdict
from kelpie.data import STD_ATOMIC_WEIGHTS


class AtomError(Exception):
    """Base class for error(s) in Atom objects."""
    pass


class Atom(object):
    """Base class to store an atom."""

    def __init__(self,
                 coordinates=None,
                 species=None,
                 magmom=None):
        """Constructor.

        :param coordinates: Iterable of the x, y, z coordinates of the atom (fractional or cartesian)
        :param species: Elemental species at the site.
        """
        self._coordinates = None
        self.coordinates = coordinates

        self._species = None
        self.species = species

        self._magmom = None
        self.magmom = magmom

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
    def magmom(self):
        return self._magmom

    @magmom.setter
    def magmom(self, magmom):
        if magmom is None:
            self._magmom = 0.
            return
        try:
            self._magmom = float(magmom)
        except (ValueError, TypeError) as error:
            error_message = 'Magnetic moment on an atom should be a decimal or integer'
            raise AtomError(error_message)

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
        :param atoms: List of `kelpie.Atom' objects.
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

    @staticmethod
    def get_volume(lattice_vectors=None):
        """
        Return the volume of the lattice vectors specified as their absolute determinant.
        Return None if lattice vectors are not specified.
        """
        if lattice_vectors is None:
            return
        return abs(numpy.linalg.det(lattice_vectors))

    @property
    def volume(self):
        """Volume of the structure."""
        return self.get_volume(lattice_vectors=self.lattice_vectors)

    @property
    def volume_pa(self):
        """Volume of the structure per atom."""
        if not self.atoms:
            return
        return self.volume/float(self.natoms)

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
            error_message = '`atoms` must be an iterable of `kelpie.Atom` objects'
            raise StructureError(error_message)
        self._atoms = atoms

    def add_atom(self, atom):
        """Add `atom` to the structure.

        :raise StructureError: if `atom` is not a `structure.Atom` object."""
        if not isinstance(atom, Atom):
            error_message = '`atom` must be a `kelpie.structure.Atom` object'
            raise StructureError(error_message)
        self._atoms.append(atom)

    @property
    def natoms(self):
        return len(self.atoms)

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

    @property
    def structural_formula(self):
        return ''.join(['{}{}'.format(e, self.composition_dict[e]) for e in self.list_of_species])

    def _get_magmom_tag(self):
        if 'A' in self._missing_structure_components():
            error_message = 'The structure has no atoms to generate the MAGMOM tag from'
            raise StructureError(error_message)
        magmoms = []
        for species in self.list_of_species:
            for atom in self.atoms:
                if atom.species == species:
                    magmoms.append(atom.magmom)
        magmom_str = []
        m_count = 1
        for i in range(len(magmoms))[1:]:
            if abs(magmoms[i] - magmoms[i-1]) < 1E-3:
                m_count += 1
            else:
                magmom_str.append('{}*{:.3f}'.format(m_count, magmoms[i-1]))
                m_count = 1
        magmom_str.append('{}*{:.3f}'.format(m_count, magmoms[-1]))
        return ' '.join(magmom_str)

    @property
    def MAGMOM(self):
        return self._get_magmom_tag()

    def _get_vasp_poscar(self):
        """Construct the VASP POSCAR.

        :return: String with the contents of a VASP 5 POSCAR file
        """
        self.check_structure_is_complete()
        poscar = []
        # system title
        poscar.append(self.comment)
        # scaling factor
        poscar.append('{:18.14f}'.format(self.scaling_constant))
        # lattice_vectors
        for lv in self.lattice_vectors:
            poscar.append('  '.join(['{:>18.14f}'.format(_lv) for _lv in lv]))
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

    def check_structure_is_complete(self):
        """Check if structure has all components required for a DFT calculation.

        :raise StructureError: if any necessary component is missing.
        """
        missing = self._missing_structure_components()
        if missing:
            error_message = ["Structure incomplete. Following components are missing:"]
            for m in missing:
                error_message.append(self._missing_components_message(m))
            raise StructureError('\n'.join(error_message))

    def _missing_structure_components(self):
        missing = []
        if not self.lattice_vectors:
            missing.append('L')
        if not self.atoms:
            missing.append('A')
        if not self.coordinate_system:
            missing.append('C')
        return missing

    @staticmethod
    def _missing_components_message(m):
        m_dict = {'L': 'Lattice vectors',
                  'A': 'Atoms',
                  'C': 'Coordinate system'}
        return '[{}]: {}'.format(m, m_dict[m])

