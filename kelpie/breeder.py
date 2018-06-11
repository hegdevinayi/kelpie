import os
import shutil
import subprocess
import json
import six
from kelpie import files_and_folders
from kelpie.scheduler_settings import DEFAULT_SCHEDULER_SETTINGS
from kelpie.scheduler_templates import SCHEDULER_TEMPLATES


class KelpieBreederError(Exception):
    """Base class to handle errors associated with breeding."""
    pass


class KelpieBreeder(object):
    """Base class to create the run directory and write batch script."""

    def __init__(self,
                 input_structure_file=None,
                 run_location=None,
                 host_scheduler_settings=None,
                 custom_scheduler_settings=None,
                 batch_script_template=None,
                 submit_batch_job=None,
                 **kwargs):
        """Constructor.

        :param input_structure_file: String with the location of the VASP5 POSCAR with the initial structure.
        :param run_location: String with the location where VASP calculations should be performed.
                             (Default: location of the specified `input_structure_file`)
        :param host_scheduler_settings: String with the name of a predefined host or path to a JSON file with the
                                        scheduler settings. Must be one of the hosts defined in
                                        `kelpie.scheduler_settings` (with a corresponding
                                        "[host_scheduler_tag].json" file) OR path to a JSON file with settings.
                                        Note: Path to a JSON file takes precedence.
                                        E.g. "cori_knl", "cori_haswell" (predefined) OR "/path/to/settings.json"
                                        (Default: "cori_knl")
        :param custom_scheduler_settings: Dictionary of tags, and *nondefault* values to go into the batch script.
                                          (The default settings dictionary, loaded for the specified
                                          `host_scheduler_settings` above will be updated)
                                          Some common tags:
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
                                          - n_mpi_per_node (# MPI tasks to invoke per node)
                                          - n_cpu_bind (# logical CPUs to bind to an MPI task)
        :param batch_script_template: String with the path to a batch script template file OR the name of a
                                      predefined template in the "scheduler_settings" directory.
                                      Note: Path to a file takes precedence.
                                      (Default: "cori")
        :param submit_batch_job: Boolean specifying whether the batch job should be submitted to the scheduler.
                                 (Default: True)
        :param kwargs: Dictionary of other miscellaneous parameters, if any.
        """

        #: VASP POSCAR file containing the structure (only VASP 5 format currently supported).
        #: `kelpie.structure.Structure` object containing VASP POSCAR data.
        self._input_structure_file = None
        self.input_structure_file = input_structure_file

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

        #: Should the batch job be submitted to the scheduler?
        self._submit_batch_job = None
        self.submit_batch_job = submit_batch_job

        #: Unsupported keyword arguments
        self.kwargs = kwargs

    @property
    def input_structure_file(self):
        return self._input_structure_file

    @input_structure_file.setter
    def input_structure_file(self, input_structure_file):
        if not input_structure_file:
            error_message = 'Input structure file not specified'
            raise KelpieBreederError(error_message)
        if not os.path.isfile(input_structure_file):
            error_message = 'Specified `input_structure_file` {} not found'.format(input_structure_file)
            raise KelpieBreederError(error_message)
        self._input_structure_file = os.path.abspath(input_structure_file)

    @property
    def run_location(self):
        return self._run_location

    @run_location.setter
    def run_location(self, run_location):
        if not run_location:
            self._run_location = os.path.dirname(os.path.abspath(self.input_structure_file))
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
                error_message = 'Unable to find the specified `host_scheduler_settings`'
                raise KelpieBreederError(error_message)
            self._host_scheduler_settings = settings

    @property
    def custom_scheduler_settings(self):
        return self._custom_scheduler_settings

    @custom_scheduler_settings.setter
    def custom_scheduler_settings(self, custom_scheduler_settings):
        if not custom_scheduler_settings:
            self._custom_scheduler_settings = {}
            return
        if os.path.isfile(custom_scheduler_settings):
            with open(custom_scheduler_settings, 'r') as fr:
                self._custom_scheduler_settings = json.load(fr)
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
                error_message = 'Unable to find the specified `batch_script_template`'
                raise KelpieBreederError(error_message)
            self._batch_script_template = template

    @property
    def submit_batch_job(self):
        return self._submit_batch_job

    @submit_batch_job.setter
    def submit_batch_job(self, submit_batch_job):
        if not submit_batch_job:
            self._submit_batch_job = True
            return
        if isinstance(submit_batch_job, six.string_types):
            self._submit_batch_job = submit_batch_job.lower()[0] == 't'
        else:
            self._submit_batch_job = submit_batch_job

    @property
    def scheduler_script_name(self):
        return '{}.q'.format(os.path.splitext(os.path.basename(self.batch_script_template))[0])

    def _get_batch_script(self):
        # general batch scheduler settings
        settings = {**self.host_scheduler_settings}
        settings.update(self.custom_scheduler_settings)

        # generate the "module load" section
        modules = []
        for module in settings.get('modules', []):
            modules.append('module load {}'.format(module))
        modules = '\n'.join(modules)
        settings.update({'modules': modules})

        # if calculation workflow and custom calculation settings were specified,
        # write them as is into the batch script
        calculation_params = []
        calculation_workflow = self.kwargs.get('calculation_workflow')
        if calculation_workflow:
            calculation_params.append('-w {}'.format(calculation_workflow))
        custom_calculation_settings = self.kwargs.get('custom_calculation_settings')
        if custom_calculation_settings:
            calculation_params.append('-ccs {}'.format(custom_calculation_settings))
        calculation_params = ' '.join(calculation_params)

        # arguments for kelpie grazer
        settings.update({'run_location': self.run_location,
                         'calculation_params': calculation_params})

        # format the template with all the arguments
        with open(self.batch_script_template, 'r') as fr:
            template = fr.read()
        template = template.format(**settings, **self.kwargs)
        return template

    @property
    def batch_script(self):
        return self._get_batch_script()

    def submit_job_to_scheduler(self):
        settings = {**self.host_scheduler_settings}
        settings.update(self.custom_scheduler_settings)
        submit_cmd = settings.get('submit_cmd')
        if not submit_cmd:
            error_message = 'Submit command for the batch scheduler not specified'
            raise KelpieBreederError(error_message)
        with files_and_folders.change_working_dir(self.run_location):
            subprocess.run([submit_cmd, self.scheduler_script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _get_mpi_call(self):
        settings = {**self.host_scheduler_settings}
        settings.update(self.custom_scheduler_settings)
        mpi_call = settings.get('mpi_call')
        if not mpi_call:
            error_message = 'MPI call not specified for the host (in scheduler settings)'
            raise KelpieBreederError(error_message)
        # special settings for the "shared" queue on Cori
        if not settings.get('nodes'):
            settings.update({'n_mpi': int(settings.get('cores'))})
        else:
            settings.update({'n_mpi': int(settings.get('nodes'))*int(settings.get('n_mpi_per_node'))})
        mpi_call = mpi_call.format(**settings)
        return mpi_call

    @property
    def mpi_call(self):
        return self._get_mpi_call()

    def breed(self):
        """Create the directory for running calculations if not already present, copy the specified input structure,
        write the batch script and the mpi_call command into the run location, submit the batch job.
        """
        # create the directory structure if not already present
        if not os.path.isdir(self.run_location):
            os.makedirs(self.run_location)

        # copy the specified input structure file into "[self.run_location]/initial_structure"
        init_structure_file = os.path.join(self.run_location, 'initial_structure.vasp')
        shutil.copy(self.input_structure_file, init_structure_file)

        # write the mpi call into "[self.run_location]/mpi_call.txt". Will be read while grazing
        mpi_call_file = os.path.join(self.run_location, 'mpi_call.txt')
        with open(mpi_call_file, 'w') as fw:
            fw.write(self.mpi_call)

        # write the batch script
        batch_script_file = os.path.join(self.run_location, self.scheduler_script_name)
        with open(batch_script_file, 'w') as fw:
            fw.write(self.batch_script)

        if self.submit_batch_job:
            self.submit_job_to_scheduler()


