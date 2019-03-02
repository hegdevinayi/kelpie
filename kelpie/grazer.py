import os
import json
from kelpie import io
from kelpie import calculation_workflows


class KelpieGrazerError(Exception):
    """Base class to handle errors associated with grazing."""
    pass


class KelpieGrazer(object):
    """Base class to perform specified calculation workflow(s)."""

    def __init__(self,
                 run_location=None,
                 initial_structure_file=None,
                 calculation_workflow=None,
                 custom_calculation_settings=None,
                 mpi_call_file=None,
                 **kwargs):
        """Constructor.

        :param run_location: String with the directory where calculations will be performed.
                             (Default: Current working directory)
        :param initial_structure_file: String with the location of the VASP5 POSCAR with the initial structure.
                                       (Default: "[self.run_location]/initial_structure.vasp")
        :param calculation_workflow: String with type of DFT calculation workflow.
                                     Currently, only "relaxation", "static" workflows implemented.
                                     (Default: "relaxation")
        :param custom_calculation_settings: Path to a JSON file with a dictionary of *nondefault* INCAR and POTCAR
                                            settings for each calculation type. The default calculation settings
                                            dictionary loaded according to the workflow will be updated.
                                            E.g., {"relaxation": {"ediff": 1E-8}, "static": {"sigma": 0.05}}
                                            (Default: {})
        :param mpi_call_file: Path to the text file with the mpi call command.
                              E.g. file contents: "srun -np 64 -c 4 -cpu_bind=cores vasp_std"
                              (Default: "[self.run_location]/mpi_call.txt"
        :param kwargs: Dictionary of other miscellaneous parameters, if any.
        """

        #: Relative/absolute path to run VASP calculations.
        self._run_location = None
        self.run_location = run_location

        #: File with the initial structure, and the initial structure
        self._initial_structure_file = None
        self.initial_structure_file = initial_structure_file
        self.initial_structure = io.read_poscar(self.initial_structure_file)

        #: Type of DFT calculation workflow: relaxation/static/hse/...
        self._calculation_workflow = None
        self.calculation_workflow = calculation_workflow
        #: Nondefault INCAR settings and POTCAR choices for different calculation types
        #: default INCAR, POTCAR settings defined by `kelpie.vasp_settings.incar.DEFAULT_VASP_INCAR_SETTINGS` for the
        # calculation types in the workflow specified.
        #: VASP recommended POTCARs used by default are in `kelpie.vasp_settings.potcar.VASP_RECO_POTCARS`.
        self._custom_calculation_settings = None
        self.custom_calculation_settings = custom_calculation_settings

        #: Path to the text file with the mpi call command
        self._mpi_call_file = None
        self.mpi_call_file = mpi_call_file

        #: Unsupported keyword arguments
        self.kwargs = kwargs

    @property
    def run_location(self):
        return self._run_location

    @run_location.setter
    def run_location(self, run_location):
        if not run_location:
            self._run_location = os.path.abspath(os.getcwd())
        else:
            self._run_location = os.path.abspath(run_location)

    @property
    def initial_structure_file(self):
        return self._initial_structure_file

    @initial_structure_file.setter
    def initial_structure_file(self, initial_structure_file):
        if not initial_structure_file:
            initial_structure_file = os.path.join(self.run_location, 'initial_structure.vasp')
        if not os.path.exists(initial_structure_file):
            error_message = 'Initial structure file {} not found'.format(initial_structure_file)
            raise KelpieGrazerError(error_message)
        else:
            self._initial_structure_file = os.path.abspath(initial_structure_file)

    @property
    def calculation_workflow(self):
        return self._calculation_workflow

    @calculation_workflow.setter
    def calculation_workflow(self, calculation_workflow):
        if not calculation_workflow:
            self._calculation_workflow = 'relaxation'
        elif calculation_workflow.lower() not in ['relaxation', 'static',
                                                  'acc_std_relax', 'sc_forces']:
            raise NotImplementedError('Specified workflow currently not implemented.')
        else:
            self._calculation_workflow = ''.join(calculation_workflow.title().split('_'))

    @property
    def custom_calculation_settings(self):
        return self._custom_calculation_settings

    @custom_calculation_settings.setter
    def custom_calculation_settings(self, custom_calculation_settings):
        if not custom_calculation_settings:
            self._custom_calculation_settings = {}
        elif not os.path.isfile(custom_calculation_settings):
            error_message = 'Specified custom settings file {} not found'.format(custom_calculation_settings)
            raise KelpieGrazerError(error_message)
        else:
            with open(custom_calculation_settings, 'r') as fr:
                self._custom_calculation_settings = json.load(fr)

    @property
    def mpi_call_file(self):
        return self._mpi_call_file

    @mpi_call_file.setter
    def mpi_call_file(self, mpi_call_file):
        if not mpi_call_file:
            mpi_call_file = os.path.join(self.run_location, 'mpi_call.txt')
        if not os.path.exists(mpi_call_file):
            error_message = 'MPI call file {} not found'.format(mpi_call_file)
            raise KelpieGrazerError(error_message)
        else:
            self._mpi_call_file = os.path.abspath(mpi_call_file)

    @property
    def mpi_call(self):
        with open(self.mpi_call_file, 'r') as fr:
            return fr.read()

    def graze(self):
        if not os.path.isdir(self.run_location):
            os.makedirs(self.run_location)

        workflow = getattr(calculation_workflows, '{}Workflow'.format(self.calculation_workflow))(
            initial_structure=self.initial_structure,
            run_location=self.run_location,
            custom_calculation_settings=self.custom_calculation_settings,
            mpi_call=self.mpi_call,
            **self.kwargs)
        workflow.perform_workflow()
