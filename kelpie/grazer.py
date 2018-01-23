import os
import shutil
import subprocess
import json
from kelpie import io
from kelpie.vasp_settings.incar import DEFAULT_VASP_INCAR_SETTINGS
from kelpie.vasp_input_generator import VaspInputGenerator
from kelpie.vasp_output_parser import VasprunXMLParser


class KelpieGrazerError(Exception):
    """Base class to handle errors associated with grazing."""
    pass


class KelpieGrazer(object):
    """Base class to perform specified calculation workflow(s)."""

    def __init__(self,
                 run_location=None,
                 calculation_workflow=None,
                 custom_calculation_settings=None,
                 **kwargs):
        """Constructor.

        :param run_location: String with the directory where calculations will be performed.
        :param calculation_workflow: String with type of DFT calculation workflow.
                                     Currently, only "relaxation", "static", "relaxation+static" workflows implemented.
                                     (Default: "relaxation")
        :param custom_calculation_settings: Dictionary of *nondefault* INCAR, POTCAR settings for each
                                            calculation type. (The default settings dictionary will be updated.)
                                            E.g. {"relaxation": {"ediff": 1E-8, "nsw": 80}, "static": {"sigma": 0.1}}
                                            (Default: {})
        :param kwargs: Dictionary of other miscellaneous parameters, if any.
        """

        #: Relative/absolute path to run VASP calculations.
        self._run_location = None
        self.run_location = run_location

        #: Type of DFT calculation workflow: relaxation/static/hse/...
        self._calculation_workflow = None
        self.calculation_workflow = calculation_workflow

        #: Nondefault INCAR settings and POTCAR choices for different calculation types
        #: default INCAR, POTCAR settings defined by `kelpie.vasp_settings.incar.DEFAULT_VASP_INCAR_SETTINGS` for the
        # calculation workflow specified.
        #: VASP recommended POTCARs used by default are in `kelpie.vasp_settings.potcar.VASP_RECO_POTCARS`.
        self._custom_calculation_settings = None
        self.custom_calculation_settings = custom_calculation_settings

        #: Unsupported keyword arguments
        self.kwargs = kwargs

        #: Initial structure
        self.init_structure = io.read_poscar(self.init_structure_file)

        #: MPI call command
        self.mpi_call = self.read_mpi_call()

    @property
    def run_location(self):
        return self._run_location

    @run_location.setter
    def run_location(self, run_location):
        self._run_location = run_location

    @property
    def calculation_workflow(self):
        return self._calculation_workflow

    @calculation_workflow.setter
    def calculation_workflow(self, calculation_workflow):
        if not calculation_workflow:
            self._calculation_workflow = 'relaxation'
            return
        if calculation_workflow.lower() not in ['relaxation', 'static', 'relaxation+static']:
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
    def init_structure_file(self):
        return os.path.join(self.run_location, 'init_structure.vasp')

    @property
    def mpi_call_file(self):
        return os.path.join(self.run_location, 'mpi_call.txt')

    def read_mpi_call(self):
        if not os.path.isfile(self.mpi_call_file):
            error_message = 'MPI call file "mpi_call.txt" not found in the run location'
            raise KelpieGrazerError(error_message)
        with open(self.mpi_call_file, 'r') as fr:
            return fr.read()


