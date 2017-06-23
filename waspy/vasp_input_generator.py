import os
import sys
import math
import json
from waspy import vasp_settings
from waspy.vasp_settings.incar import VASP_INCAR_TAGS


class VASPInputGenerator:
    """Base class to generate VASP input files for a given POSCAR file."""

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


def vasp_format(key, value):
    return '{:14s} = {}'.format(key.upper(), value_formatter(value))


def get_elements_list(poscar='POSCAR'):
    """
    """
    with open(poscar, 'r') as fposcar:
        poscar_data = fposcar.readlines()
        elems = [e for e in poscar_data[5].strip().split()]
    return elems


def get_comp_dict(poscar='POSCAR'):
    """
    """
    with open(poscar, 'r') as fposcar:
        poscar_data = fposcar.readlines()
        elems = [e for e in poscar_data[5].strip().split()]
        natoms = [int(n) for n in poscar_data[6].strip().split()]
    comp_dict = {}
    for e, n in zip(elems, natoms):
        comp_dict[e] = n
    return comp_dict


def write_potcar(poscar='POSCAR', version='54', xc='PBE', **ext_pot_sett):
    """
    """
    pot_sett_path = os.path.join(os.path.dirname(vasp_settings.__file__), 'potcar',\
                    'pot_sett.yml')
    with open(pot_sett_path, 'r') as fpot_sett:
        pot_sett = yaml.safe_load(fpot_sett)

    base_key = "_".join([version.lower(), xc.lower()])
    if ext_pot_sett:
        for element, potcar_label in ext_pot_sett.items():
            pot_sett[base_key]['pot'].update({element: potcar_label})
    pot_dir = pot_sett[base_key]['path']
    elem_list = get_elements_list(poscar)
    pot_path = os.path.join(os.path.dirname(poscar), 'POTCAR')
    pot_enmax = 0.
    with open(pot_path, 'w') as fpotcar:
        for e in elem_list:
            vasp_pot_path = os.path.join(pot_dir, pot_sett[base_key]['pot'][e],\
                            'POTCAR')
            with open(vasp_pot_path, 'r') as fvasp_pot:
                for line in fvasp_pot:
                    fpotcar.write(line)
                    if 'ENMAX' in line:
                        enmax = float(line.strip().split()[2].strip(';'))
                        if pot_enmax < enmax:
                            pot_enmax = enmax
    sys.stdout.write('POTCAR written to {loc}\n'.format(loc=pot_path))
    sys.stdout.write('ENMAX = {enmax:0.1f} eV\n'.format(enmax=pot_enmax))
    sys.stdout.flush()
    return pot_enmax


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


def write_kpoints(poscar='POSCAR', scheme='auto', k_div=50, **ext_sett):
    """
    """
    kp_path = os.path.join(os.path.dirname(poscar), 'KPOINTS')
    with open(kp_path, 'w') as fkp:
        fkp.write('KPOINTS\n0\n')
        if scheme=='auto':
            fkp.write('Auto\n{k_div}\n'.format(k_div=k_div))
    sys.stdout.write('KPOINTS written to {loc}\n'.format(loc=kp_path))
    sys.stdout.flush()
    return


def roundup(x):
    return int(math.ceil(x/10.))*10
