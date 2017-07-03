import os
import sys
import math
from waspy.vasp_structure import VaspStructure
from waspy.vasp_settings.incar import VASP_INCAR_TAGS, VASP_INCAR_SETTINGS
from waspy.vasp_settings.potcar import VASP_RECO_POTCARS


class VaspInputGenerator:
    """Base class to generate VASP input files for a given POSCAR file."""

    def __init__(self,
                 poscar_file='POSCAR',
                 potcar_settings={'version': '54', 'xc': 'PBE'},
                 calculation_type='relaxation',
                 additional_settings={}):
        """
        :param poscar_file: name/relative path of the POSCAR. Defaults to 'POSCAR'.
        :type poscar_file: str
        :param potcar_settings: VASP POTCAR version, the xc functional to be used
        :type potcar_settings: dict
        :param calculation_type: type of DFT calculation (relaxation/static/hse/...). Defaults to 'relaxation'.
        :type calculation_type: str
        :param additional_settings: VASP INCAR tags and corresponding values, in addition to the default ones.
        :type additional_settings: dict(str, str or float or bool or list)
        """
        self.poscar_file = os.path.abspath(poscar_file)
        self.vasp_structure = VaspStructure(self.poscar_file)
        self.potcar_settings = potcar_settings
        self.calculation_type = calculation_type
        self.calculation_settings = VASP_INCAR_SETTINGS[self.calculation_type]
        self.calculation_settings.update(additional_settings)
        self.POTCAR = self.get_vasp_potcar(self.potcar_settings)
        self.INCAR = self.get_vasp_incar(self.calculation_type, self.calculation_settings)

    def _tag_value_formatter(self, value):
        if isinstance(value, list):
            return ' '.join(map(self._tag_value_formatter, value))
        elif isinstance(value, str):
            return value.upper()
        elif isinstance(value, bool):
            return '.{}.'.format(value.upper())
        elif isinstance(value, float):
            return '{:.3E}'.format(value)
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
        return '{:14s} = {}'.format(tag.upper(), self._tag_value_formatter(value))

    def get_vasp_potcar(self, potcar_settings={}):
        """Construct the VASP POTCAR file for `self.POSCAR` using info in the `VASP_POTCAR_SETTINGS` variable
        
        :param potcar_settings: VASP POTCAR version, the xc functional to be used; updates `self.potcar_settings`
        :type potcar_settings: dict
        :return: VASP POTCAR file
        :rtype: list(str)
        """
        vasp_potcar = []
        self.potcar_settings.update(potcar_settings)

        # concatenate all elemental POTCARs together
        potcar_dir = VASP_RECO_POTCARS[self.potcar_settings['version']][self.potcar_settings['xc']]['path']
        reco_pots = VASP_RECO_POTCARS[self.potcar_settings['version']][self.potcar_settings['xc']]['reco']
        for element in self.vasp_structure.list_of_elements:
            potcar_file = os.path.join(potcar_dir, reco_pots[element])
            with open(potcar_file, 'r') as fr:
                for line in fr.readlines():
                    vasp_potcar.append(line)
        return vasp_potcar

    def get_vasp_incar(self, calculation_type='relaxation', additional_settings={}):
        """
        
        :param calculation_type: type of DFT calculation (relaxation/static/hse/...). Defaults to 'relaxation'.
        :type calculation_type: str
        :param additional_settings: VASP INCAR tags and corresponding values, in addition to the default ones.
        :type additional_settings: dict(str, str or float or bool or list)
        :return: VASP INCAR file
        """
#     with open(pot_path, 'w') as fpotcar:
#         for e in elem_list:
#             vasp_pot_path = os.path.join(pot_dir, pot_sett[base_key]['pot'][e],\
#                             'POTCAR')
#             with open(vasp_pot_path, 'r') as fvasp_pot:
#                 for line in fvasp_pot:
#                     fpotcar.write(line)
#                     if 'ENMAX' in line:
#                         enmax = float(line.strip().split()[2].strip(';'))
#                         if pot_enmax < enmax:
#                             pot_enmax = enmax
#     sys.stdout.write('POTCAR written to {loc}\n'.format(loc=pot_path))
#     sys.stdout.write('ENMAX = {enmax:0.1f} eV\n'.format(enmax=pot_enmax))
#     sys.stdout.flush()
#     return pot_enmax


def write_incar(poscar='POSCAR', calc='relaxation', stdout=False, **ext_sett):
    incar_settings_file = 'incar_' + calc + '.yml'
    inc_sett_path = os.path.join(os.path.dirname(vasp_settings.__file__), 'incar',\
                    incar_settings_file)
    with open(inc_sett_path, 'r') as finc_sett:
        inc_sett = yaml.safe_load(finc_sett)
    if ext_sett:
        for tag, val in ext_sett.items():
            inc_sett[tag.lower()] = val

    incar = ""
    # VASP_INCAR_TAGS read from configuration/vasp_incar_format/incar_tag_groups.yml
    for block, tags in VASP_INCAR_TAGS.items():
        incar += '### {title} ###\n'.format(title=block)
        # if parallelization tags have been pased as kwargs, print them
        for tag in tags:
            if tag not in inc_sett.keys():
                continue
            incar += '%s\n' % vasp_format(tag, inc_sett[tag])
        incar += '\n'
    if stdout:
        sys.stdout.write(incar)

    inc_path = os.path.join(os.path.dirname(poscar), 'INCAR'+'.'+calc)
    with open(inc_path, 'w') as fincar:
        fincar.write('{}'.format(incar))
    sys.stdout.write('INCAR written to {loc}\n'.format(loc=inc_path))
    sys.stdout.flush()
    return


def roundup(x):
    return int(math.ceil(x/10.))*10

