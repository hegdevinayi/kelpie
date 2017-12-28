import os
from waspy import structure
from waspy.vasp_input_generator import VaspInputGenerator
from waspy.vasp_output_parser import VasprunXMLParser
from waspy.vasp_settings.incar import DEFAULT_VASP_INCAR_SETTINGS
from waspy.batch_scheduler_settings import DEFAULT_BATCH_SCHEDULER_SETTINGS


class VaspRunManager(object):
    """Base class to manage VASP runs."""

    def __init__(self,
                 structure_file='POSCAR',
                 calculation_workflow='relaxation',
                 nondefault_calc_settings=None,
                 run_directory=None,
                 host_resource='cori',
                 batch_scheduler='slurm',
                 nondefault_scheduler_settings=None):
        """
        :param structure_file: location of the VASP POSCAR. Defaults to 'POSCAR'.
        :type structure_file: str
        :param calculation_workflow: type of DFT calculation (relaxation/static/hse/...). Defaults to 'relaxation'.
        :type calculation_workflow: str
        :param nondefault_calc_settings: nondefault INCAR, POTCAR settings for each calculation type. Defaults to None.
                                         - e.g. {"relaxation": {"ediff": 1E-8, "nsw": 80}, "static": {"sigma": 0.1}}
        :type nondefault_calc_settings: dict(str, dict(str, str or float or bool or list))
        :param run_directory: directory to run all the calculations in. Defaults to the location of the `structure_file`.
        :type run_directory: str
        :param batch_scheduler: slurm/PBS/... Defaults to "slurm". (Only slurm implemented so far.)
        :type batch_scheduler:
        :param nondefault_scheduler_settings: tag, values to go into the batch script. Tags:
                                   - job-name, partition, qos, account, constraint, license, nodes, time, output,
                                   - omp_threads, module (to load), executable,
                                   - n_mpi_per_node (# MPI tasks per node), n_cpu_bind (# CPUs to bind to an MPI task)
        :type nondefault_scheduler_settings: dict(str, str)
        :param host_resource: cori/edison/... Defaults to 'cori'.
        :type host_resource: str
        """

        #: VASP POSCAR file containing the structure (only VASP 5 format currently supported).
        self.structure_file = os.path.abspath(structure_file)

        #: `waspy.vasp_structure.VaspStructure` object containing VASP POSCAR data.
        self.vasp_structure = structure.VaspStructure(poscar_file=self.structure_file)

        #: type of DFT calculation: relaxation/static/hse/...
        if calculation_workflow not in ['relaxation', 'static']:
            raise NotImplementedError('Only relaxation and static workflows currently implemented.')
        self.calculation_workflow = calculation_workflow

        #: nondefault INCAR settings and POTCAR choices for different calculation types
        #: default INCAR, POTCAR settings defined by `waspy.vasp_settings.incar.DEFAULT_VASP_INCAR_SETTINGS`.
        #: VASP recommended POTCARs used by default are in `waspy.vasp_settings.potcar.VASP_RECO_POTCARS`.
        self.nondefault_calc_settings = nondefault_calc_settings

        #: relative/absolute path to run VASP calculations.
        if run_directory is None:
            self.run_location = os.path.dirname(self.structure_file)
        else:
            self.run_location = run_directory

        #: compute resource where the calculations are being run: cori/edison/quest/...
        self.host_resource = host_resource

        #: batch scheduler on the compute resource: slurm/PBS/...
        self.batch_scheduler = batch_scheduler

        #: dictionary of settings to go into the batch script.
        #: Will be updated with `nondefault_scheduler_settings` if provided during object creation.
        self.batch_scheduler_settings = DEFAULT_BATCH_SCHEDULER_SETTINGS[self.batch_scheduler][self.host_resource]
        if nondefault_scheduler_settings is not None:
            self.batch_scheduler_settings.update(nondefault_scheduler_settings)

    def single_vasp_run(self, structure, location, calc_type='relaxation'):
        """Run a single VASP calculation of type `calc_type`.

        :param structure: initial crystal structure.
        :type structure: `waspy.structure.VaspStructure`
        :param location: path where VASP calculation must be run.
        :type: str
        :param calc_type: type of DFT calculation: relaxation/static/hse (primarily for reading in settings)
        :type calc_type: str
        """
        settings = DEFAULT_VASP_INCAR_SETTINGS[calc_type]
        settings.update(self.nondefault_calc_settings[calc_type], {})
        vasp_input_gen = VaspInputGenerator(structure, settings, location)
        vasp_input_gen.write_vasp_input_files()
        self.run_vasp()



    def vasp_relaxation_workflow(self):
        """Workflow for performing a relaxation run using VASP. A final SCF is always run.
        
        1- if run_dir does not exist, create it
        2- if it does exist, delete all files in the run_dir except the structure_file, if present
        3- initiate the relaxation workflow: 
            A- while vasprun.xml is not completely converged
                I- generate VASP (relaxation) input files for the structure (CONTCAR if present, structure_file otherwise)
                II- run VASP
                III- parse the vasprun.xml file and add the CalculationData object to the workflow
                IV- create a "relaxation_{yyyy}{mm}{dd}{hh}{mm}{ss}" folder and move all files (except structure_file) to it
                    (if it is completely converged, write into "relaxation_final" directory?)
            B- generate VASP (static) input files for the final CONTCAR
            C- run VASP
            D- if the static run does not converge,
            E- delete all files and restart static; exit if unsuccessful on second attempt
            F- write the RelaxationWorkflowData.pickle file with all the necessary data
        4- touch empty file called DONE if everything is done?
        """
            
        # read in calculation settings
        # update with nondefault calculation settings, if any
        # generate_VASP_input
        # run VASP
        # extract data
        # did it converge (in all the different ways)?
        # if not, copy contents into relaxation_{n}
        # re-relax
        # if converged, copy contents into relaxation_final
        # do static

    def vasp_static_workflow(self):
        """Workflow for performing a single SCF calculation using VASP.
        1- if run_dir does not exist, create it
        2- if it does exist, delete all files in the run_dir except structure_file, if present
        3- initiate the static workflow:
            A- generate VASP (static) input files for structure_file
            B- run VASP
            C- if the static run does not converge,
            D- delete all files and restart static; exit if unsuccessful on second attempt
            E- write the StaticWorkflowData.pickle file with all the necessary data
        4- touch empty file called DONE if everything is done?
        """

        # read in calculation settings
        # update with nondefault calculation settings, if any
        # generate_VASP_input
        # run VASP
        # extract data
        # did it electronically converge?


def generate_VASP_input():

def generate_job_script():

def submit_job():

    def run_vasp():
        pass

def check_convergence():

def write_calculation_data():

