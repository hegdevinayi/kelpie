import os
import math
import six
import kelpie
from kelpie import io
from kelpie.structure import Structure
from kelpie.vasp_settings.incar import DEFAULT_VASP_INCAR_SETTINGS, VASP_INCAR_TAGS, HUBBARD_U_VALUES
from kelpie.vasp_settings.potcar import VASP_RECO_POTCARS
from kelpie.data import STD_ATOMIC_WEIGHTS, VALENCE_ELECTRONS


class VaspInputError(Exception):
    """Base class for errors in VASP input files."""
    pass


class VaspInputGenerator(object):
    """Base class to generate VASP input files for a given POSCAR file."""

    def __init__(self,
                 structure=None,
                 calculation_settings=None,
                 write_location=None,
                 **kwargs):
        """
        :param structure: `kelpie.structure.Structure` object or String with the location of a valid VASP5 POSCAR file
        :param calculation_settings: Dictionary of VASP INCAR tags, values, and POTCAR choices.
                                     Defaults to pre-defined full relaxation calculation.
        :param write_location: String with the location where the VASP input files should be written.
                               Defaults to current working directory
        :param kwargs: Dictionary of other miscellaneous parameters, if any.
        """

        #: `kelpie.structure.VaspStructure` object containing the VASP POSCAR data
        self._structure = None
        self.structure = structure

        #: VASP INCAR tags, values and POTCAR choices for generating input files.
        self._calculation_settings = None
        self.calculation_settings = calculation_settings

        #: where the VASP input files should be written
        self._write_location = None
        self.write_location = write_location

        #: other miscellaneous keyword arguments
        self.kwargs = kwargs

    @property
    def structure(self):
        return self._structure

    @structure.setter
    def structure(self, structure):
        if isinstance(structure, Structure):
            structure.check_structure_is_complete()
            self._structure = structure
        elif isinstance(structure, six.string_types):
            if os.path.isfile(structure):
                structure = io.read_poscar(poscar_file=structure)
                self._structure = structure
            else:
                error_message = 'POSCAR file {} not found'.format(structure)
                raise VaspInputError(error_message)
        else:
            error_message = '`structure` must be `structure.Structure` object or path to a valid POSCAR'
            raise VaspInputError(error_message)

    @property
    def calculation_settings(self):
        return self._calculation_settings

    @calculation_settings.setter
    def calculation_settings(self, calculation_settings):
        if not calculation_settings:
            self._calculation_settings = DEFAULT_VASP_INCAR_SETTINGS['relaxation']
        else:
            self._calculation_settings = calculation_settings

        # if ENCUT is not set in calculation settings, set it manually
        if self._calculation_settings.get('encut') is None:
            self.set_calculation_encut()

        # Scale EDIFF with the number of atoms in the unit cell
        if self._calculation_settings.get('scale_ediff_per_atom'):
            self.scale_ediff_per_atom()

        # if the structure contains elements with unfilled d or f shells, set ISPIN = 2, and
        # appropriate MAGMOM tag
        if self._calculation_settings.get('magnetism', None) is not None:
            self.set_magnetism()

        # if the structure contains O and one of the TMs for which Hubbard U value to use is known,
        # set the appropriate VASP INCAR TAGS
        hubbard_values_scheme = self._calculation_settings.get('hubbards', None)
        if hubbard_values_scheme is not None:
            self.set_hubbards(scheme=hubbard_values_scheme)

    @property
    def write_location(self):
        return self._write_location

    @write_location.setter
    def write_location(self, write_location):
        if not write_location:
            self._write_location = os.path.abspath(os.getcwd())
        else:
            self._write_location = write_location

    def vasp_tag_value_formatter(self, value):
        if isinstance(value, list):
            return ' '.join(map(self.vasp_tag_value_formatter, value))
        elif isinstance(value, six.string_types):
            return value.upper()
        elif isinstance(value, bool):
            return '.{}.'.format(str(value).upper())
        elif isinstance(value, float):
            return '{:.2E}'.format(value)
        else:
            return str(value)

    def format_vasp_tag(self, tag, value):
        """Format INCAR tags and corresponding values to be printed in the INCAR.

        :param tag: VASP INCAR tag
        :type tag: str
        :param value: value corresponding to the INCAR tag
        :type value: str or bool or float or list(str or bool or float)
        :return: formatted tag, value
        :rtype: str
        """
        return '{:14s} = {}'.format(tag.upper(), self.vasp_tag_value_formatter(value))

    @staticmethod
    def _concatenate_potcars(list_of_potcar_files):
        """Concatenate a list of POTCAR files into a single POTCAR.

        :param list_of_potcar_files: relative/absolute path of a list of VASP POTCAR files.
        :type list_of_potcar_files: list(str)
        :return: contents of the concatenated VASP POTCAR
        :rtype: str

        """
        concatenated_potcar = ''
        for potcar_file in list_of_potcar_files:
            with open(potcar_file, 'r') as fr:
                concatenated_potcar += fr.read()
        return concatenated_potcar

    @property
    def POTCAR(self):
        """VASP POTCAR file for `self.vasp_structure` and `self.calculation settings`.

        :return: contents of the VASP POTCAR file.
        :rtype: str
        """
        return self._get_vasp_potcar()

    def _get_vasp_potcar(self):
        """Construct the VASP POTCAR for `self.POSCAR`.

        If `self.calculation_settings['potcar_settings']['element_potcars'] dictionary:
        (a) is empty: defaults are used from `kelpie.vasp_settings.potcar.VASP_RECO_POTCARS`.
        (b) has actual location of POTCARs as values to element keys, they are used directly.
        (c) has VASP POTCAR tag (e.g. "Mn_pv") as values to element keys, corresponding POTCARs are used from the
            local POTCAR library.

        :return: VASP POTCAR file
        :rtype: str
        :raise VaspInputError: if POTCAR file for any element is not found.
        """
        potcar_settings = self.calculation_settings['potcar_settings']
        version = potcar_settings['version']
        xc = potcar_settings['xc']
        element_potcars = potcar_settings.get('element_potcars', {})

        list_of_potcars = []
        for species in self.structure.list_of_species:
            element_potcar = element_potcars.get(species)

            # if POTCAR choices are not specified in the calculation settings, use defaults.
            if element_potcar is None:
                potcar_dir = VASP_RECO_POTCARS[version][xc]['path']
                reco_pots = VASP_RECO_POTCARS[version][xc]['reco']
                try:
                    potcar_file = os.path.join(potcar_dir, reco_pots[species], 'POTCAR')
                except KeyError:
                    error_message = 'POTCAR for {} not found'.format(species)
                    raise VaspInputError(error_message)
                else:
                    list_of_potcars.append(potcar_file)

            # if actual location of the POTCARs are specified in the calculation settings, use them.
            elif os.path.isfile(element_potcar):
                list_of_potcars.append(element_potcar)

            # if VASP POTCAR keys (e.g. "Li_sv", "Mn_pv") are specified, read them from the local POTCAR library.
            else:
                potcar_dir = VASP_RECO_POTCARS[version][xc]['path']
                potcar_file = os.path.join(potcar_dir, element_potcar, 'POTCAR')
                if os.path.isfile(potcar_file):
                    list_of_potcars.append(potcar_file)
                else:
                    error_message = 'POTCAR file {} for {} not found'.format(potcar_file, species)
                    raise VaspInputError(error_message)
        return self._concatenate_potcars(list_of_potcars)

    @staticmethod
    def get_highest_enmax(vasp_potcar):
        """Make a list of all ENMAX values in the POTCAR, return the highest among them.

        :param vasp_potcar: VASP POTCAR file
        :type vasp_potcar: str (with linebreaks)
        :return: highest ENMAX value from the POTCAR
        :rtype: float
        """
        list_of_enmax = []
        for line in vasp_potcar.split('\n'):
            if 'ENMAX' in line:
                list_of_enmax.append(float(line.strip().split()[2].strip(';')))
        return max(list_of_enmax)

    @staticmethod
    def roundup_encut(encut):
        """Roundup the encut value to the nearest ten.
        :param encut: ENCUT for VASP INCAR
        :type encut: float
        :return: encut rounded up to the nearest ten
        :rtype: int
        """
        return int(math.ceil(encut/10.))*10

    def set_calculation_encut(self):
        """Update `self.calculation_settings['encut']` = encut_scaling_factor*(highest ENMAX from `self.POTCAR`).

        If `encut_scaling_factor` is not specified in calculation settings, 1.5 is used as default.
        If `maximum_encut` is not specified in calculation settings, 600 (in eV) is used as default.
        """
        encut_scaling_factor = self.calculation_settings.get('encut_scaling_factor', 1.5)
        maximum_encut = self.calculation_settings.get('maximum_encut', 600)
        encut = self.roundup_encut(encut_scaling_factor*self.get_highest_enmax(self.POTCAR))
        if encut > maximum_encut:
            encut = maximum_encut
        self._calculation_settings.update({'encut': encut})

    def scale_ediff_per_atom(self):
        """Scale EDIFF with number of atoms in the unit cell. EDIFF' = EDIFF*number of atoms in the cell."""
        ediff = self._calculation_settings.get('ediff', DEFAULT_VASP_INCAR_SETTINGS['relaxation']['ediff'])
        self._calculation_settings.update({'ediff': ediff*self.structure.natoms, 'scale_ediff_per_atom': False})

    def set_magnetism(self):
        if self._calculation_settings['magnetism'] != 'ferro':
            error_message = 'Only ferromagnetic initial configuration implemented'
            raise NotImplementedError(error_message)
        for atom in self.structure.atoms:
            element = sorted([e for e in STD_ATOMIC_WEIGHTS if atom.species.startswith(e)])[-1]
            if 0 < VALENCE_ELECTRONS[element]['d_elec'] < 10:
                atom.magmom = 5.0
            if 0 < VALENCE_ELECTRONS[element]['f_elec'] < 14:
                atom.magmom = 7.0
        self.set_ispin()
        self.set_magmom_tag()

    def set_ispin(self):
        if any([a.magmom for a in self.structure.atoms]):
            self._calculation_settings.update({'ispin': 2})
        else:
            self._calculation_settings.update({'ispin': 1})

    def set_magmom_tag(self):
        if self._calculation_settings.get('ispin') == 1:
            return
        else:
            self._calculation_settings.update({'magmom': self.structure.MAGMOM})

    def get_hubbards(self, scheme='wang'):
        if scheme not in HUBBARD_U_VALUES:
            error_message = 'Cannot find the specified scheme "{}" for Hubbard U values to use'.format(scheme)
            raise VaspInputError(error_message)
        if 'O' not in self.structure.list_of_species:
            hubbards = {'ldau': False}
            return hubbards
        ldaul = []
        ldauu = []
        ldauj = []
        for species in self.structure.list_of_species:
            element = sorted([e for e in STD_ATOMIC_WEIGHTS if species.startswith(e)])[-1]
            if element in HUBBARD_U_VALUES[scheme]:
                ldaul.append(2)
                ldauu.append(HUBBARD_U_VALUES[scheme][element])
            else:
                ldaul.append(-1)
                ldauu.append(0.)
            ldauj.append(0.)
        # if no species has a Hubbard U value to use, switch off LDAU
        if all([v == -1 for v in ldaul]):
            hubbards = {'ldau': False}
            return hubbards
        # otherwise, generate the VASP INCAR TAGS and return as a Dictionary
        ldaul = ' '.join(['{}'.format(v) for v in ldaul])
        ldauu = ' '.join(['{:.2f}'.format(v) for v in ldauu])
        ldauj = ' '.join(['{:.2f}'.format(v) for v in ldauj])
        hubbards = {
            'ldau': True,
            'ldautype': 2,
            'ldaul': ldaul,
            'ldauu': ldauu,
            'ldauj': ldauj,
            'ldaprint': 1,
            'lmaxmix': 4
        }
        return hubbards

    def set_hubbards(self, scheme='wang'):
        self._calculation_settings.update(self.get_hubbards(scheme=scheme))

    @property
    def INCAR(self):
        """VASP INCAR for the `self.vasp_structure` and `self.calculation_settings`.

        :return: contents of the VASP INCAR file.
        :rtype: str
        """
        return self._get_vasp_incar()

    def _get_vasp_incar(self):
        """Construct the VASP INCAR file for `self.POSCAR` using `self.calculation_settings`

        :return: VASP INCAR file
        :rtype: str
        """
        vasp_incar = ''
        for tag_block in VASP_INCAR_TAGS['tags']:
            vasp_incar += '### {} ###\n'.format(tag_block)
            for tag in VASP_INCAR_TAGS[tag_block]:
                value = self.calculation_settings.get(tag)
                if value is None:
                    continue
                vasp_incar += self.format_vasp_tag(tag, value) + '\n'
            vasp_incar += '\n'
        vasp_incar += '# [autogenerated by kelpie v{}] #'.format(kelpie.__version__)
        return vasp_incar

    @staticmethod
    def _write_vasp_input_file(file_contents, file_location, overwrite=True):
        """Write the `file_contents` as is into `file_location`; confirm overwrite if file already exists.

        :param file_contents: contents to be written into file
        :type file_contents: str
        :param file_location: absolute or relative path to the file
        :type file_location: str
        :param overwrite: if `file_location` already exists, should it be overwritten?
        """
        if os.path.isfile(file_location) and not overwrite:
            return
        with open(file_location, 'w') as fw:
            fw.write(file_contents)
        return

    def write_vasp_input_files(self, overwrite=True):
        """Write VASP POSCAR, POTCAR, and INCAR files into the folder specified by `self.write_location`.

        :param overwrite: Should files be overwritten if they already exist? Defaults to True."""
        # write the POSCAR file
        poscar_file = os.path.join(self.write_location, 'POSCAR')
        self._write_vasp_input_file(self.structure.POSCAR, poscar_file, overwrite=overwrite)

        # write the POTCAR file
        potcar_file = os.path.join(self.write_location, 'POTCAR')
        self._write_vasp_input_file(self.POTCAR, potcar_file, overwrite=overwrite)

        # write the INCAR file
        incar_file = os.path.join(self.write_location, 'INCAR')
        self._write_vasp_input_file(self.INCAR, incar_file, overwrite=overwrite)

