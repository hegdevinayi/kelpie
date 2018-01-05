import os
import subprocess
import datetime
from contextlib import contextmanager
import json
from kelpie import io
from kelpie.scheduler_settings import DEFAULT_SCHEDULER_SETTINGS
from kelpie.scheduler_templates import SCHEDULER_TEMPLATES
from kelpie.vasp_settings.incar import DEFAULT_VASP_INCAR_SETTINGS
from kelpie.vasp_input_generator import VaspInputGenerator
from kelpie.vasp_output_parser import VasprunXMLParser


@contextmanager
def _change_dir(new_dir):
    current_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(current_dir)


class VaspRunManagerError(Exception):
    """Base class to handle errors associated with the run manager"""
    pass


class VaspSingleRunManager(object):
    """Base class to manage VASP runs."""

    def __init__(self,
                 structure_file=None,
                 calculation_workflow=None,
                 custom_calculation_settings=None,
                 run_location=None,
                 host_scheduler_settings=None,
                 custom_scheduler_settings=None,
                 batch_script_template=None,
                 **kwargs):
        """Constructor.

        :param structure_file: String with the location of the VASP5 POSCAR file.
                               (Default: './POSCAR')
        :param calculation_workflow: String with type of DFT calculation (relaxation/static/hse/...).
                                     (Default: "relaxation")
        :param custom_calculation_settings: Dictionary of *nondefault* INCAR, POTCAR settings for each
                                            calculation type. (The default settings dictionary will be updated.)
                                            - e.g. {"relaxation": {"ediff": 1E-8, "nsw": 80}, "static": {"sigma": 0.1}}
                                            (Default: None)
        :param run_location: String with the location where VASP calculations should be performed.
                             (Default: location of the specified `structure_file`)
        :param host_scheduler_settings: String with the name of a predefined host or path to a JSON file with the
                                        scheduler settings. Must be one of the hosts defined in
                                        `kelpie.scheduler_settings` (with a corresponding
                                        "[host_scheduler_tag].json" file) OR path to a JSON file with settings.
                                        Path to a JSON file takes precedence.
                                        E.g. "cori_knl", "cori_haswell" (predefined) OR "/path/to/settings.json"
                                        (Default: "cori_knl")
        :param custom_scheduler_settings: Dictionary of tags, and *nondefault* values to go into the batch script.
                                          (The default settings dictionary, loaded for the specified
                                          `host_scheduler_settings` above will be updated)
                                          Possible tags:
                                          - job-name
                                          - partition
                                          - qos
                                          - account
                                          - constraint
                                          - license
                                          - nodes
                                          - walltime
                                          - output
                                          - omp_threads
                                          - modules (to load)
                                          - executable
                                          - n_mpi_per_node (# MPI tasks per node)
                                          - n_cpu_bind (# CPUs to bind to an MPI task)
        :param batch_script_template: String with the path to a batch script template file OR the name of a
                                      predefined template in the "scheduler_settings" directory. Path to a file takes
                                      precedence.
                                      (Default: "cori.q")
        :param kwargs: Dictionary of other miscellaneous parameters, if any.
        """

        #: VASP POSCAR file containing the structure (only VASP 5 format currently supported).
        #: `kelpie.structure.Structure` object containing VASP POSCAR data.
        self._structure_file = None
        self._structure = None
        self.structure_file = structure_file

        #: Type of DFT calculation workflow: relaxation/static/hse/...
        self._calculation_workflow = None
        self.calculation_workflow = calculation_workflow

        #: Nondefault INCAR settings and POTCAR choices for different calculation types
        #: default INCAR, POTCAR settings defined by `kelpie.vasp_settings.incar.DEFAULT_VASP_INCAR_SETTINGS` for the
        # calculation workflow specified.
        #: VASP recommended POTCARs used by default are in `kelpie.vasp_settings.potcar.VASP_RECO_POTCARS`.
        self._custom_calculation_settings = None
        self.custom_calculation_settings = custom_calculation_settings

        #: Relative/absolute path to run VASP calculations.
        self._run_location = None
        self.run_location = run_location

        #: Dictionary of batch scheduler settings corresponding to the host where the calculations are being run. Can
        #  be path a JSON file with the settings OR one of the predefined tags in
        # `kelpie.scheduler_settings.DEFAULT_SCHEDULER_SETTINGS`. File takes precedence.
        self._host_scheduler_settings = None
        self.host_scheduler_settings = host_scheduler_settings

        #: Nondefault scheduler settings for this particular run. Updates `self.host_scheduler_settings`.
        self._custom_scheduler_settings = None
        self.custom_scheduler_settings = custom_scheduler_settings

        #: Template for the batch script
        self._batch_script_template = None
        self.batch_script_template = batch_script_template

        #: Unsupported keyword arguments
        self.kwargs = kwargs

    @property
    def structure_file(self):
        return self._structure_file

    @structure_file.setter
    def structure_file(self, structure_file):
        if not structure_file:
            error_message = '`structure_file` must be provided'
            raise VaspRunManagerError(error_message)
        self._structure = io.read_poscar(poscar_file=structure_file)
        self._structure_file = structure_file

    @property
    def structure(self):
        return self._structure

    @property
    def calculation_workflow(self):
        return self._calculation_workflow

    @calculation_workflow.setter
    def calculation_workflow(self, calculation_workflow):
        if not calculation_workflow:
            self._calculation_workflow = 'relaxation'
            return
        if calculation_workflow.lower() not in ['relaxation', 'static']:
            raise NotImplementedError('Only relaxation and static workflows currently implemented.')
        self._calculation_workflow = calculation_workflow.lower()

    @property
    def custom_calculation_settings(self):
        return self._custom_calculation_settings

    @custom_calculation_settings.setter
    def custom_calculation_settings(self, custom_calculation_settings):
        if not custom_calculation_settings:
            self._custom_calculation_settings = {}
        else:
            self._custom_calculation_settings = custom_calculation_settings

    @property
    def run_location(self):
        return self._run_location

    @run_location.setter
    def run_location(self, run_location):
        if not run_location:
            self._run_location = os.path.dirname(self.structure_file)
        else:
            self._run_location = run_location

    @property
    def host_scheduler_settings(self):
        return self._host_scheduler_settings

    @host_scheduler_settings.setter
    def host_scheduler_settings(self, host_scheduler_settings):
        if not host_scheduler_settings:
            self._host_scheduler_settings = DEFAULT_SCHEDULER_SETTINGS['cori_knl']
            return
        if os.path.isfile(host_scheduler_settings):
            with open(host_scheduler_settings, 'r') as fr:
                self._host_scheduler_settings = json.load(fr)
        else:
            settings = DEFAULT_SCHEDULER_SETTINGS.get(host_scheduler_settings)
            if not settings:
                error_message = 'Unable to find settings corresponding to the specified `host_scheduler_settings` tag'
                raise VaspRunManagerError(error_message)
            self._host_scheduler_settings = settings

    @property
    def custom_scheduler_settings(self):
        return self._custom_scheduler_settings

    @custom_scheduler_settings.setter
    def custom_scheduler_settings(self, custom_scheduler_settings):
        if not custom_scheduler_settings:
            self._custom_scheduler_settings = {}
        else:
            self._custom_scheduler_settings = custom_scheduler_settings

    @property
    def batch_script_template(self):
        return self._batch_script_template

    @batch_script_template.setter
    def batch_script_template(self, batch_script_template):
        if not batch_script_template:
            self._batch_script_template = SCHEDULER_TEMPLATES['cori']
            return
        if os.path.isfile(batch_script_template):
            self._batch_script_template = batch_script_template
        else:
            template = SCHEDULER_TEMPLATES.get(batch_script_template)
            if not template:
                error_message = 'Unable to find template corresponding to the specified `batch_script_template` tag'
                raise VaspRunManagerError(error_message)
            self._batch_script_template = template

    @property
    def scheduler_script_name(self):
        return 'kelpie_single__{}.q'.format(os.path.splitext(os.path.basename(self.batch_script_template))[0])

    def _get_batch_script(self):
        settings = {**self.host_scheduler_settings}
        settings.update(self.custom_scheduler_settings)
        with open(self.batch_script_template, 'r') as fr:
            template = fr.read()
        template = template.format(**settings)
        load_modules = []
        for load_module in settings.get('modules', []):
            load_modules.append('module load {}'.format(load_module))
        template += '\n'.join(load_modules)
        template += '\n'
        return template

    @property
    def batch_script(self):
        return self._get_batch_script()

    def _write_job_files(self, calc_sett, calc_dir):
        ig = VaspInputGenerator(structure=self.structure,
                                calculation_settings=calc_sett,
                                write_location=calc_dir,
                                **self.kwargs)
        ig.write_vasp_input_files()
        with open(os.path.join(calc_dir, self.scheduler_script_name), 'w') as fw:
            fw.write(self.batch_script)

    @staticmethod
    def _time_stamped_folder(folder):
        d = datetime.datetime.now()
        ts_folder = '{}_{:4d}'.format(folder, d.year)
        ts_folder += ('{:0>2d}'*5).format(d.month, d.day, d.hour, d.minute, d.second)
        return ts_folder

    def _mpi_call(self):
        scheduler_settings = {**self.host_scheduler_settings}
        scheduler_settings.update(self.custom_scheduler_settings)
        mpi_call = scheduler_settings.get('mpi_call')
        n_mpi = scheduler_settings.get('nodes', 1)*scheduler_settings.get('n_mpi_per_node', 64)
        lcores_per_mpi = scheduler_settings.get('lcores_per_mpi', 4)
        exe = scheduler_settings.get('exe', 'vasp_std')
        return mpi_call.format(n_mpi=n_mpi, lcores_per_mpi=lcores_per_mpi, exe=exe)

    def run_vasp(self, calc_dir):
        with _change_dir(calc_dir):
            mpi_call = self._mpi_call()
            return subprocess.run(mpi_call.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
        if not os.path.isdir(self.run_location):
            os.makedirs(self.run_location)

        calc_sett = {**DEFAULT_VASP_INCAR_SETTINGS['static']}
        calc_sett.update(self.custom_calculation_settings)
        calc_dir = os.path.join(self.run_location, self._time_stamped_folder('static'))
        self._write_job_files(calc_sett, calc_dir)
        self.run_vasp(calc_dir)

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

    def generate_VASP_input():
        pass

    def generate_batch_script():
        pass

    def submit_job():
        pass

        def run_vasp():
            pass

    def check_convergence():
        pass

    def write_calculation_data():
        pass

