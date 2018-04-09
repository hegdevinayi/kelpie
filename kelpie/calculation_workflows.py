import os
import subprocess
from kelpie import io
from kelpie.structure import Structure
from kelpie import files_and_folders
from kelpie.vasp_settings.incar import DEFAULT_VASP_INCAR_SETTINGS
from kelpie.vasp_input_generator import VaspInputGenerator
from kelpie.vasp_calculation_data import VaspCalculationData


class KelpieWorkflowError(Exception):
    """Base class to handle calculation workflow related errors."""
    pass


class GenericWorkflow(object):
    """Generic workflow class."""

    def __init__(self,
                 initial_structure=None,
                 run_location=None,
                 custom_calculation_settings=None,
                 mpi_call=None,
                 **kwargs):
        """Constructor.

        :param initial_structure: `kelpie.structure` with the initial structure
        :param run_location: String with the location where calculations should be performed.
        :param custom_calculation_settings: Dictionary of *nondefault* calculation settings
        :param mpi_call: String with the complete MPI call to use for calculations.
        :param kwargs: Other miscellaneous arguments.
        """
        self._initial_structure = None
        self.initial_structure = initial_structure

        self._run_location = None
        self.run_location = run_location

        self._custom_calculation_settings = None
        self.custom_calculation_settings = custom_calculation_settings

        self._mpi_call = None
        self.mpi_call = mpi_call

        self.kwargs = kwargs

    @property
    def initial_structure(self):
        return self._initial_structure

    @initial_structure.setter
    def initial_structure(self, initial_structure):
        if not isinstance(initial_structure, Structure):
            error_message = 'Arugment `initial_structure` must be a `kelpie.structure.Structure object'
            raise KelpieWorkflowError(error_message)
        self._initial_structure = initial_structure

    @property
    def run_location(self):
        return self._run_location

    @run_location.setter
    def run_location(self, run_location):
        if not run_location:
            error_message = 'Run location not specified'
            raise KelpieWorkflowError(error_message)
        if not os.path.isdir(run_location):
            error_message = 'Specified run location {} not found'.format(run_location)
            raise KelpieWorkflowError(error_message)
        self._run_location = run_location

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
    def mpi_call(self):
        return self._mpi_call

    @mpi_call.setter
    def mpi_call(self, mpi_call):
        if not mpi_call:
            error_message = 'MPI call for the calculation not specified'
            raise KelpieWorkflowError(error_message)
        self._mpi_call = mpi_call

    @staticmethod
    def run_vasp(mpi_call):
        with open('stdout.txt', 'w') as fstdout, open('stderr.txt', 'w') as fstderr:
            vasp_process = subprocess.run(mpi_call.split(), stdout=fstdout, stderr=fstderr)
        return vasp_process

    def do_relaxation(self, structure=None, settings=None, mpi_call=None, **kwargs):
        # propagate variable "n_attempts" to keep track of the number of VASP runs
        # if this is the first do_relaxation() call, initialize "n_attempts"
        if not hasattr(kwargs, 'n_attempts'):
            kwargs['n_attempts'] = 0

        # write input files with the given structure and settings
        ig = VaspInputGenerator(structure=structure,
                                calculation_settings=settings,
                                **kwargs)
        ig.write_vasp_input_files()
        # use the MPI call specified to run VASP
        vasp_process = self.run_vasp(mpi_call)
        # did the VASP run OK?
        if vasp_process.returncode != 0:
            error_message = 'Something went wrong with the MPI VASP run'
            raise KelpieWorkflowError(error_message)
        # increase "n_attempts": VASP has already been run once
        kwargs['n_attempts'] += 1
        # parse the calculation output and check if relevent convergence criteria are met
        vcd = VaspCalculationData(vasprun_xml_file='vasprun.xml')
        converged = vcd.is_fully_converged(scf_thresh=settings.get('ediff'),
                                           force_thresh=settings.get('ediffg'))

        # recursively call do_relaxation() until either convergence or maximum attempts have been reached
        if not converged and kwargs['n_attempts'] <= 5:
            # if not converged wrt number of bands, restart with
            # 1.2*N_bands_old or N_bands_old+4 whichever is higher
            # make sure settings are carried over to the static calculation
            if not vcd.is_number_of_bands_converged():
                nbands = max([int(vcd.nbands*1.2), vcd.nbands+4])
                settings.update({'nbands': nbands})
                self._custom_calculation_settings.update({
                    'relaxation': {'nbands': nbands},
                    'static': {'nbands': nbands}
                })
            try:
                output_structure = io.read_poscar('CONTCAR')
            except io.KelpieIOError:
                error_message = 'Could not read the CONTCAR file'
                raise KelpieWorkflowError(error_message)
            else:
                files_and_folders.backup_files()
                return self.do_relaxation(structure=output_structure,
                                          settings=settings,
                                          mpi_call=mpi_call,
                                          **kwargs)
        else:
            return vcd, converged

    def do_static(self, structure=None, settings=None, mpi_call=None, **kwargs):
        # propagate variable "n_attempts" to keep track of the number of VASP runs
        # if this is the first do_relaxation() call, initialize "n_attempts"
        if not hasattr(kwargs, 'n_attempts'):
            kwargs['n_attempts'] = 0

        # write input files with the given structure and settings
        ig = VaspInputGenerator(structure=structure,
                                calculation_settings=settings,
                                **kwargs)
        ig.write_vasp_input_files()
        # use the MPI call specified to run VASP
        vasp_process = self.run_vasp(mpi_call)
        # did the VASP run OK?
        if vasp_process.returncode != 0:
            error_message = 'Something went wrong with the MPI VASP run'
            raise KelpieWorkflowError(error_message)
        # increase "n_attempts": VASP has already been run once
        kwargs['n_attempts'] += 1
        # parse the calculation output and check if relevent convergence criteria are met
        vcd = VaspCalculationData(vasprun_xml_file='vasprun.xml')
        converged = vcd.is_scf_converged(threshold=settings.get('ediff'))

        # recursively call do_static() until either convergence or maximum attempts have been reached
        if not converged and kwargs['n_attempts'] <= 2:
            files_and_folders.backup_files()
            return self.do_static(structure=structure,
                                  settings=settings,
                                  mpi_call=mpi_call,
                                  **kwargs)
        else:
            return vcd, converged


class RelaxationWorkflow(GenericWorkflow):
    """Class with workflow for a relaxation run followed by a final static run."""

    def __init__(self,
                 initial_structure=None,
                 run_location=None,
                 custom_calculation_settings=None,
                 mpi_call=None,
                 **kwargs):
        super(RelaxationWorkflow, self).__init__(initial_structure=initial_structure,
                                                 run_location=run_location,
                                                 custom_calculation_settings=custom_calculation_settings,
                                                 mpi_call=mpi_call,
                                                 **kwargs)

    def perform_workflow(self, from_scratch=False):
        relaxation_dir = os.path.join(self.run_location, 'relaxation')
        # if from_scratch, delete the "relaxation" folder, if it exists
        if from_scratch and os.path.isdir(relaxation_dir):
            shutil.rmtree(relaxation_dir)
        # create a "relaxation" folder, if one doesn't already exist
        os.makedirs(relaxation_dir, exist_ok=True)
        relaxation_settings = DEFAULT_VASP_INCAR_SETTINGS['relaxation']
        relaxation_settings.update(self.custom_calculation_settings.get('relaxation', {}))
        initial_structure = self.initial_structure
        with files_and_folders.change_working_dir(relaxation_dir):
            if not from_scratch:
                previous_outcar = os.path.join(relaxation_dir, 'OUTCAR')
                previous_contcar = os.path.join(relaxation_dir, 'CONTCAR')
                previous_poscar = os.path.join(relaxation_dir, 'POSCAR')
                if os.path.isfile(previous_outcar) and os.path.getsize(previous_outcar):
                    files_and_folders.backup_files()
                if os.path.isfile(previous_contcar) and os.path.getsize(previous_contcar):
                    initial_structure = io.read_poscar(previous_contcar)
                elif os.path.isfile(previous_poscar) and os.path.getsize(previous_poscar):
                    initial_structure = io.read_poscar(previous_poscar)
            vcd, converged = self.do_relaxation(structure=initial_structure,
                                                settings=relaxation_settings,
                                                mpi_call=self.mpi_call,
                                                **self.kwargs)
        vcd.write_calculation_data(filename='relaxation_data.json')

        if not converged:
            error_message = 'Error while performing the relaxation run(s)'
            raise KelpieWorkflowError(error_message)

        relaxation_output_structure = os.path.join(relaxation_dir, 'CONTCAR')
        initial_structure = io.read_poscar(relaxation_output_structure)
        static_dir = os.path.join(self.run_location, 'static')
        os.makedirs(static_dir, exist_ok=True)
        static_settings = DEFAULT_VASP_INCAR_SETTINGS['static']
        static_settings.update(self.custom_calculation_settings.get('static', {}))
        files_and_folders.copy_files(src_folder='relaxation',
                                     dest_folder='static',
                                     list_of_filenames=['CHGCAR'])
        with files_and_folders.change_working_dir(static_dir):
            vcd, converged = self.do_static(structure=initial_structure,
                                            settings=static_settings,
                                            mpi_call=self.mpi_call,
                                            **self.kwargs)
        vcd.write_calculation_data(filename='static_data.json')

        if not converged:
            error_message = 'Error while performing the final static run'
            raise KelpieWorkflowError(error_message)



