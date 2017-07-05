import os
from waspy.vasp_input_generator import VaspInputGenerator
from waspy.vasp_output_parser import VasprunXMLParser


class VaspRunManager:
    """Base class to manage VASP runs."""

    def __init__(self,
                 structure_file='POSCAR',
                 potcar_settings=None,
                 calculation_type='relaxation',
                 nondefault_calc_settings=None,
                 run_location=None,
                 host_resource='cori',
                 batch_scheduler='slurm',
                 nondefault_scheduler_settings=None):
        """
        :param structure_file: location of the VASP POSCAR. Defaults to 'POSCAR'.
        :type structure_file: str
        :param potcar_settings: VASP release version, XC function, VASP recommended for each element. Defaults to None.
        :type potcar_settings: dict(str, str)
        :param calculation_type: type of DFT calculation (relaxation/static/hse/...). Defaults to 'relaxation'.
        :type calculation_type: str
        :param nondefault_calc_settings: VASP INCAR tags, values apart from the default ones. Defaults to None.
        :type nondefault_calc_settings: dict(str, str or float or bool or list)
        :param run_location: directory to run all the calculations in. Defaults to the location of the `structure_file`.
        :type run_location: str
        :param batch_scheduler: slurm/PBS/... Defaults to "slurm". (Only slurm implemented so far.)
        :type batch_scheduler:
        :param nondefault_scheduler_settings: tag, values to go into the batch script. Tags:
                                   - job-name, partition, account, constraint, license, nodes, time, output,
                                   - omp_threads, module (to load), executable,
                                   - n_mpi (number of MPI tasks), n_cpu_bind (number of CPUs to bind to each MPI task)
        :type nondefault_scheduler_settings: dict(str, str)
        :param host_resource: cori/edison/... Defaults to 'cori'.
        :type host_resource: str
        """

        self.poscar_file = os.path.abspath(structure_file)
        self.potcar_settings = {'version': '54', 'xc': 'PBE'}
        if potcar_settings is not None:
            self.potcar_settings.update(potcar_settings)
        self.calculation_type = calculation_type
        self.nondefault_calc_settings = nondefault_calc_settings
        if run_location is None:
            self.run_location = os.path.dirname(self.poscar_file)
        else:
            self.run_location = run_location
        self.host_resource = host_resource
        self.batch_scheduler = batch_scheduler
        self.batch_scheduler_settings = DEFAULT_SLURM_SETTINGS[self.host_resource]
        if nondefault_scheduler_settings is not None:
            self.batch_scheduler_settings.update(nondefault_scheduler_settings)

def generate_VASP_input():

def generate_job_script():

def submit_job():

def run_VASP():

def check_convergence():

def write_calculation_data():

