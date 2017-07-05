import os
import sys
import math
import waspy
from waspy.vasp_settings.incar import VASP_INCAR_TAGS
from waspy.vasp_settings.potcar import VASP_RECO_POTCARS


class VaspInputError(Exception):
    """Base class for errors in VASP input files."""
    pass


class VaspInputGenerator:
    """Base class to generate VASP input files for a given POSCAR file."""

    def __init__(self,
                 vasp_structure,
                 calculation_settings,
                 write_location=None):
        """
        :param vasp_structure: VASP POSCAR converted into `waspy.vasp_structure.VaspStructure` object. Required.
        :type vasp_structure: `waspy.vasp_structure.VaspStructure`
        :param calculation_settings: VASP INCAR tags, values, and POTCAR choices. Required.
        :type calculation_settings: dict(str, str or float or bool or list or dict)
        :param write_location: where the VASP input files should be written.
                               Defaults to the location of the `vasp_structure.poscar_file`.
        :type write_location: str
        """

        #: `waspy.vasp_structure.VaspStructure` object containing the VASP POSCAR data
        self.vasp_structure = vasp_structure

        #: VASP INCAR tags, values and POTCAR choices for generating input files.
        self.calculation_settings = calculation_settings

        #: where the VASP input files should be written
        if write_location is None:
            self.write_location = os.path.dirname(self.vasp_structure.poscar_file)
        else:
            self.write_location = write_location

        #: VASP elemental POTCAR files concatenated suitably for the given composition
        self.POTCAR = self.get_vasp_potcar()

        # if ENCUT is not set in calculation settings, set it manually
        if self.calculation_settings.get('encut') is None:
            self.set_calculation_encut()

        #: VASP INCAR for the settings in `self.calculation_settings`
        self.INCAR = self.get_vasp_incar()

    def vasp_tag_value_formatter(self, value):
        if isinstance(value, list):
            return ' '.join(map(self.vasp_tag_value_formatter, value))
        elif isinstance(value, str):
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

    def get_vasp_potcar(self):
        """Construct the VASP POTCAR for `self.POSCAR`.

        If `self.calculation_settings['potcar_settings']['element_potcars'] dictionary:
        (a) is empty: defaults are used from `waspy.vasp_settings.potcar.VASP_RECO_POTCARS`.
        (b) has actual location of POTCARs as values to element keys, they are used directly.
        (c) has VASP POTCAR tag (e.g. "Mn_pv") as values to element keys, corresponding POTCARs are used from the
            local POTCAR library.
        
        :return: VASP POTCAR file
        :rtype: str
        :raise VaspInputError: if POTCAR file for any element is not found.
        """
        potcar_settings = self.calculation_settings['potcar_settings']
        element_potcars = potcar_settings.get('element_potcars', {})

        list_of_potcars = []
        for element in self.vasp_structure.list_of_elements:
            element_potcar = element_potcars.get(element)

            # if POTCAR choices are not specified in the calculation settings, use defaults.
            if element_potcar is None:
                potcar_dir = VASP_RECO_POTCARS[potcar_settings['version']][potcar_settings['xc']]['path']
                reco_pots = VASP_RECO_POTCARS[potcar_settings['version']][potcar_settings['xc']]['reco']
                try:
                    potcar_file = os.path.join(potcar_dir, reco_pots[element], 'POTCAR')
                except KeyError:
                    error_message = 'POTCAR for {} not found.'.format(element)
                    raise VaspInputError(error_message)
                else:
                    list_of_potcars.append(potcar_file)

            # if actual location of the POTCARs are specified in the calculation settings, use them.
            elif os.path.isfile(element_potcar):
                list_of_potcars.append(element_potcar)

            # if VASP POTCAR keys (e.g. "Li_sv", "Mn_pv") are specified, read them from the local POTCAR library.
            else:
                potcar_dir = VASP_RECO_POTCARS[potcar_settings['version']][potcar_settings['xc']]['path']
                potcar_file = os.path.join(potcar_dir, element_potcar, 'POTCAR')
                if os.path.isfile(potcar_file):
                    list_of_potcars.append(potcar_file)
                else:
                    error_message = '{} file not found.'.format(potcar_file)
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

        If `encut_scaling_factor` is not specified in calculation settings, 1.3 is used as default.
        If `maximum_encut` is not specified in calculation settings, 520 (in eV) is used as default.
        """
        encut_scaling_factor = self.calculation_settings.get('encut_scaling_factor', 1.3)
        maximum_encut = self.calculation_settings.get('maximum_encut', 520)
        encut = self.roundup_encut(encut_scaling_factor*self.get_highest_enmax(self.POTCAR))
        if encut > maximum_encut:
            encut = maximum_encut
        self.calculation_settings.update({'encut': encut})

    def get_vasp_incar(self):
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
        vasp_incar += '# [autogenerated by waspy v{}] #'.format(waspy.VERSION)
        return vasp_incar

    @staticmethod
    def _write_vasp_input_file(file_contents, file_location):
        """Write the `file_contents` as is into `file_location`; confirm overwrite if file already exists.

        :param file_contents: contents to be written into file
        :type file_contents: str
        :param file_location: absolute or relative path to the file
        :type file_location: str
        """
        if os.path.isfile(file_location):
            sys.stdout.write('File {} already exists.'.format(file_location))
            user_input = input('Overwrite? [y/n]: ')
            while user_input.lower() not in ['y', 'n']:
                user_input = input('Type "y" or "n": ')
            if user_input.lower() == 'n':
                sys.stdout.write('OK, skipped writing {}.\n'.format(file_location))
                sys.stdout.flush()
                return

        with open(file_location, 'w') as fw:
            fw.write(file_contents)
        return

    def write_vasp_input_files(self):
        """Write VASP POSCAR, POTCAR, and INCAR files into the folder specified by `location`."""
        try:
            os.mkdir(self.write_location)
        except FileExistsError:
            pass

        sys.stdout.write('Writing VASP input files into "{}"... '.format(self.write_location))
        sys.stdout.flush()

        # write the POSCAR file
        poscar_file = os.path.join(self.write_location, 'POSCAR')
        self._write_vasp_input_file(self.vasp_structure.POSCAR, poscar_file)

        # write the POTCAR file
        potcar_file = os.path.join(self.write_location, 'POTCAR')
        self._write_vasp_input_file(self.POTCAR, potcar_file)

        # write the INCAR file
        incar_file = os.path.join(self.write_location, 'INCAR')
        self._write_vasp_input_file(self.INCAR, incar_file)

        sys.stdout.write('done.\n')
        sys.stdout.flush()

