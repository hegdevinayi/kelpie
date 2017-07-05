import os
import sys
import math
import waspy
from waspy.vasp_structure import VaspStructure
from waspy.vasp_settings.incar import VASP_INCAR_TAGS, VASP_INCAR_SETTINGS
from waspy.vasp_settings.potcar import VASP_RECO_POTCARS


class VaspInputError(Exception):
    """Base class for errors in VASP input files."""
    pass


class VaspInputGenerator:
    """Base class to generate VASP input files for a given POSCAR file."""

    def __init__(self,
                 poscar_file='POSCAR',
                 potcar_settings=None,
                 calculation_type='relaxation',
                 nondefault_calc_settings=None):
        """
        :param poscar_file: name/relative path of the POSCAR. Defaults to 'POSCAR'.
        :type poscar_file: str
        :param potcar_settings: VASP POTCAR version, the xc functional to be used. Defaults to None.
        :type potcar_settings: dict(str, str)
        :param calculation_type: type of DFT calculation (relaxation/static/hse/...). Defaults to 'relaxation'.
        :type calculation_type: str
        :param nondefault_calc_settings: VASP INCAR tags and corresponding values, in addition to the default ones.
        :type nondefault_calc_settings: dict(str, str or float or bool or list)
        """
        #: VASP POSCAR file containing the structure (only VASP 5 format currently supported)
        self.poscar_file = os.path.abspath(poscar_file)

        #: `waspy.vasp_structure.VaspStructure` object containing the VASP POSCAR data
        self.vasp_structure = VaspStructure(self.poscar_file)

        #: VASP POTCAR release version, XC functional, recommendation for each element from `VASP_RECO_POTCARS`
        self.potcar_settings = {'version': '54', 'xc': 'PBE'}
        if potcar_settings is not None:
            self.potcar_settings.update(potcar_settings)

        #: VASP elemental POTCAR files concatenated suitably for the given composition
        self.POTCAR = self.get_vasp_potcar()

        #: type of DFT calculation: relaxation/static/hse/...
        self.calculation_type = calculation_type

        #: VASP INCAR tags, values corresponding to the type of DFT calculation read from `VASP_INCAR_SETTINGS`
        self.calculation_settings = VASP_INCAR_SETTINGS[self.calculation_type]

        # if custom settings are provided during object creation, update the settings dictionary
        if nondefault_calc_settings is not None:
            self.calculation_settings.update(nondefault_calc_settings)

        # if calculation type is 'relaxation', set ENCUT depending on the highest ENMAX in the POTCAR
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

    def get_vasp_potcar(self):
        """Construct the VASP POTCAR for `self.POSCAR` using info in the `VASP_POTCAR_SETTINGS` variable
        
        :return: VASP POTCAR file
        :rtype: str
        """
        vasp_potcar = ''

        # concatenate all elemental POTCARs together
        potcar_dir = VASP_RECO_POTCARS[self.potcar_settings['version']][self.potcar_settings['xc']]['path']
        reco_pots = VASP_RECO_POTCARS[self.potcar_settings['version']][self.potcar_settings['xc']]['reco']
        for element in self.vasp_structure.list_of_elements:
            try:
                potcar_file = os.path.join(potcar_dir, reco_pots[element], 'POTCAR')
            except KeyError:
                error_message = 'POTCAR for {} not found.'.format(element)
                raise VaspInputError(error_message)
            with open(potcar_file, 'r') as fr:
                vasp_potcar += fr.read()
        return vasp_potcar

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
        """Update `self.calculation_settings['encut']` = 1.3*(highest ENMAX from `self.POTCAR`).
        """
        if self.calculation_type == 'relaxation':
            encut_scaling_factor = VASP_INCAR_SETTINGS[self.calculation_type].get('encut_scaling_factor', 1.3)
            encut = encut_scaling_factor*self.get_highest_enmax(self.POTCAR)
            if encut > 520:
                encut = 520
            self.calculation_settings.update({'encut': self.roundup_encut(encut)})

    def get_vasp_incar(self):
        """Construct the VASP INCAR file for `self.POSCAR`, `self.calculation_type` using global variables
        `VASP_INCAR_SETTINGS` and `VASP_INCAR_TAGS`.

        :return: VASP INCAR file
        :rtype: str
        """
        vasp_incar = ''
        for tag_block in VASP_INCAR_TAGS['tags']:
            vasp_incar += '### {} ###\n'.format(tag_block)
            for tag in VASP_INCAR_TAGS[tag_block]:
                value = VASP_INCAR_SETTINGS[self.calculation_type].get(tag, None)
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

    def write_vasp_input_files(self, location=''):
        """Write VASP POSCAR, POTCAR, and INCAR files into the folder specified by `location`.

        :param location: Folder to write VASP input files into. Creates one if it does not exist already. Defaults to
                         the directory containing `self.poscar_file`.
        :type location: str
        """
        if not location:
            location = os.path.dirname(self.poscar_file)
        else:
            try:
                os.mkdir(location)
            except FileExistsError:
                pass

        sys.stdout.write('Writing VASP input files into "{}"... '.format(location))
        sys.stdout.flush()

        # write the POSCAR file
        poscar_file = os.path.join(location, 'POSCAR')
        self._write_vasp_input_file(self.vasp_structure.POSCAR, poscar_file)

        # write the POTCAR file
        potcar_file = os.path.join(location, 'POTCAR')
        self._write_vasp_input_file(self.POTCAR, potcar_file)

        # write the INCAR file
        incar_file = os.path.join(location, 'INCAR')
        self._write_vasp_input_file(self.INCAR, incar_file)

        sys.stdout.write('done.\n')
        sys.stdout.flush()

