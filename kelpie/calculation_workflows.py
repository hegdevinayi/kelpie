import os
import shutil
import subprocess
import json

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
            msg = 'Arugment `initial_structure` must be a `kelpie.structure.Structure object'
            raise KelpieWorkflowError(msg)
        self._initial_structure = initial_structure

    @property
    def run_location(self):
        return self._run_location

    @run_location.setter
    def run_location(self, run_location):
        if not run_location:
            msg = 'Run location not specified'
            raise KelpieWorkflowError(msg)
        if not os.path.isdir(run_location):
            msg = 'Specified run location {} not found'.format(run_location)
            raise KelpieWorkflowError(msg)
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
            msg = 'MPI call for the calculation not specified'
            raise KelpieWorkflowError(msg)
        self._mpi_call = mpi_call

    @staticmethod
    def run_vasp(mpi_call):
        with open('stdout.txt', 'w') as fstdout, open('stderr.txt', 'w') as fstderr:
            vasp_process = subprocess.run(mpi_call.split(), stdout=fstdout, stderr=fstderr)
        return vasp_process

    @staticmethod
    def get_vasp_errors(vasp_stdout=None):
        if not vasp_stdout:
            return {'empty_stdout'}
        errors = set()
        if 'Error reading item' in vasp_stdout:
            errors.add('input_error')
        if 'ZPOTRF' in vasp_stdout:
            errors.add('zpotrf')
        if 'SGRCON' in vasp_stdout:
            errors.add('sgrcon')
        if 'INVGRP' in vasp_stdout:
            errors.add('invgrp')
        if 'PRICEL' in vasp_stdout:
            errors.add('pricel')
        if 'RHOSYG' in vasp_stdout:
            errors.add('rhosyg')
        if 'POSMAP' in vasp_stdout:
            errors.add('posmap')
        if 'BRIONS problems: POTIM should be increased' in vasp_stdout:
            errors.add('brions_potim')
        if 'TOO FEW BANDS' in vasp_stdout:
            errors.add('bands')
        if 'FEXCF' in vasp_stdout:
            errors.add('fexcf')
        if 'FEXCP' in vasp_stdout:
            errors.add('fexcp')
        if 'EDDDAV' in vasp_stdout:
            errors.add('edddav')
        if 'not hermitian in DAV' in vasp_stdout:
            errors.add('hermitian_dav')
        if 'BRMIX: very serious problems' in vasp_stdout:
            errors.add('brmix')
        if 'IBZKPT' in vasp_stdout:
            errors.add('ibzkpt')
        if 'ZBRENT' in vasp_stdout:
            errors.add('zbrent')
        return errors

    @staticmethod
    def address_vasp_errors(errors=None,
                            current_sett=None,
                            calc_data=None):
        new_sett = {}
        if current_sett is None:
            current_sett = {}
        if not errors:
            return new_sett
        for error in errors:
            if error == 'input_error':
                msg = 'Error while VASP read the INCAR file'
                raise KelpieWorkflowError(msg)
            elif error in ['zpotrf', 'fexcf', 'fexcp']:
                new_sett.update({
                    'potim': current_sett.get(
                            'potim',
                            DEFAULT_VASP_INCAR_SETTINGS['relaxation']['potim']
                    )*0.5
                })
            elif error in ['sgrcon', 'invgrp', 'pricel', 'rhosyg', 'posmap']:
                new_sett.update({'symprec': 1e-4})
            elif error in ['brions']:
                new_sett.update({
                    'potim': current_sett.get(
                            'potim',
                            DEFAULT_VASP_INCAR_SETTINGS['relaxation']['potim']
                    )*2.0
                })
            elif error in ['bands']:
                n_bands = getattr(calc_data, 'n_bands')
                n_bands = max([int(n_bands*1.2), n_bands + 4])
                new_sett.update({'nbands': n_bands})
            elif error in ['edddav', 'hermitian']:
                if current_sett.get('algo', 'normal').lower()[0] == 'n':
                    new_sett.update({'algo': 'fast'})
            elif error in ['brmix']:
                new_sett.update({'symprec': 1e-6})
            elif error in ['ibzkpt', 'zbrent']:
                pass
        return new_sett

    def do_relaxation(self, structure=None, settings=None, mpi_call=None,
                      **kwargs):
        # propagate "n_attempts" to keep track of the number of VASP runs
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
            msg = 'Something went wrong with the MPI VASP run'
            raise KelpieWorkflowError(msg)
        # increase "n_attempts": the number of VASP runs
        kwargs['n_attempts'] += 1
        # parse VASP output files to check for convergence
        vcd = VaspCalculationData(vasprunxml_file='vasprun.xml',
                                  vasp_outcar_file='OUTCAR')
        converged = vcd.is_fully_converged(scf_thresh=settings.get('ediff'),
                                           force_thresh=settings.get('ediffg'))
        # if the calculation has converged or the maximum number of attempts
        # has been reached, return the most recent calculation data
        max_nattempts = kwargs.get('max_nattempts', 5)
        if converged or kwargs['n_attempts'] >= max_nattempts:
            return vcd, converged
        # if not try to fix any errors and/or convergence issues
        # get all runtime errors reported by VASP
        with open('stdout.txt', 'r') as fr:
            vasp_stdout = fr.read()
        vasp_errors = self.get_vasp_errors(vasp_stdout=vasp_stdout)
        if not vcd.is_number_of_bands_converged():
            vasp_errors.add('bands')
        # try to address any errors encountered above
        # except when VASP didn't run at all: request user intervention
        if any([e in vasp_errors for e in ['empty_stdout', 'input_error']]):
            msg = 'Error running VASP. Problem with the INCAR?'
            raise KelpieWorkflowError(msg)
        new_sett = self.address_vasp_errors(errors=vasp_errors,
                                            current_sett=settings,
                                            calc_data=vcd)
        settings.update(new_sett)
        # make sure settings related to the VASP NBANDS tag are carried over
        # to the all other calculation settings
        if 'nbands' in new_sett:
            for calc_type in DEFAULT_VASP_INCAR_SETTINGS:
                if calc_type not in self._custom_calculation_settings:
                    self._custom_calculation_settings[calc_type] = {
                        'nbands': new_sett.get('nbands')
                    }
                else:
                    self._custom_calculation_settings[calc_type].update({
                        'nbands': new_sett.get('nbands')
                    })
        # restart the relaxation with the final structure from the previous
        # attempt
        try:
            prev_structure = io.read_poscar('CONTCAR')
        except io.KelpieIOError:
            try:
                prev_structure = io.read_poscar('POSCAR')
            except io.KelpieIOError:
                msg = 'Error while reading the previous CONTCAR/POSCAR'
                raise KelpieWorkflowError(msg)
        files_and_folders.backup_files()
        return self.do_relaxation(structure=prev_structure,
                                  settings=settings,
                                  mpi_call=mpi_call,
                                  **kwargs)

    def do_static(self, structure=None, settings=None, mpi_call=None, **kwargs):
        # propagate "n_attempts" to keep track of the number of VASP runs
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
            msg = 'Something went wrong with the MPI VASP run'
            raise KelpieWorkflowError(msg)
        # increase "n_attempts": the number of VASP runs
        kwargs['n_attempts'] += 1
        # parse VASP output files to check for convergence
        vcd = VaspCalculationData(vasprunxml_file='vasprun.xml',
                                  vasp_outcar_file='OUTCAR')
        converged = vcd.is_fully_converged(scf_thresh=settings.get('ediff'))
        # if the calculation has converged or the maximum number of attempts
        # has been reached, return the most recent calculation data
        max_nattempts = kwargs.get('max_nattempts', 2)
        if converged or kwargs['n_attempts'] >= max_nattempts:
            return vcd, converged
        # if not try to fix any errors and/or convergence issues
        # get all runtime errors reported by VASP
        with open('stdout.txt', 'r') as fr:
            vasp_stdout = fr.read()
        vasp_errors = self.get_vasp_errors(vasp_stdout=vasp_stdout)
        if not vcd.is_number_of_bands_converged():
            vasp_errors.add('bands')
        # try to address any errors encountered above
        # except when VASP didn't run at all: request user intervention
        if any([e in vasp_errors for e in ['empty_stdout', 'input_error']]):
            msg = 'Error running VASP. Problem with the INCAR?'
            raise KelpieWorkflowError(msg)
        new_sett = self.address_vasp_errors(errors=vasp_errors,
                                            current_sett=settings,
                                            calc_data=vcd)
        settings.update(new_sett)
        # restart the static calculation
        files_and_folders.backup_files()
        return self.do_static(structure=structure,
                              settings=settings,
                              mpi_call=mpi_call,
                              **kwargs)


class RelaxationWorkflow(GenericWorkflow):
    """Class with workflow for a relaxation run followed by a static run."""

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
        with open('relaxation_data.json', 'w') as fw:
            json.dump(vcd.as_dict(), fw, indent=2)

        if not converged:
            msg = 'Error while performing the relaxation run(s)'
            raise KelpieWorkflowError(msg)

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
        with open('static_data.json', 'w') as fw:
            json.dump(vcd.as_dict(), fw, indent=2)

        if not converged:
            msg = 'Error while performing the final static run'
            raise KelpieWorkflowError(msg)


class AccStdRelaxWorkflow(GenericWorkflow):
    """Class with workflow for an accurate (e.g. for phonons) relaxation of the
    Spglib-standardized primitive unit cell."""

    def __init__(self,
                 initial_structure=None,
                 run_location=None,
                 custom_calculation_settings=None,
                 mpi_call=None,
                 **kwargs):
        super(AccStdRelaxWorkflow, self).__init__(initial_structure=initial_structure,
                                                  run_location=run_location,
                                                  custom_calculation_settings=custom_calculation_settings,
                                                  mpi_call=mpi_call,
                                                  **kwargs)

    def perform_workflow(self, from_scratch=False):
        #TODO: Make the directory structure more organic (avoid duplicate
        # "initial_structure.vasp" files e.g.)
        ##relaxation_dir = os.path.join(self.run_location, 'acc_std_relax')
        relaxation_dir = os.path.join(self.run_location)
        ### if from_scratch, delete the relaxation folder, if it exists
        ##if from_scratch and os.path.isdir(relaxation_dir):
        ##    shutil.rmtree(relaxation_dir)
        ### create a "relaxation" folder, if one doesn't already exist
        ##os.makedirs(relaxation_dir, exist_ok=True)
        relaxation_settings = DEFAULT_VASP_INCAR_SETTINGS['acc_std_relax']
        relaxation_settings.update(self.custom_calculation_settings.get('acc_std_relax', {}))
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
        with open('acc_std_relax_data.json', 'w') as fw:
            json.dump(vcd.as_dict(), fw, indent=2)

        if not converged:
            msg = 'Error while performing the relaxation run(s)'
            raise KelpieWorkflowError(msg)


class ScForcesWorkflow(GenericWorkflow):
    """Class with the workflow for the calculation of forces in supercells with
    (a) displaced atom(s)."""

    def __init__(self,
                 initial_structure=None,
                 run_location=None,
                 custom_calculation_settings=None,
                 mpi_call=None,
                 **kwargs):
        super(ScForcesWorkflow, self).__init__(initial_structure=initial_structure,
                                               run_location=run_location,
                                               custom_calculation_settings=custom_calculation_settings,
                                               mpi_call=mpi_call,
                                               **kwargs)

    def perform_workflow(self, from_scratch=False):
        calc_dir = os.path.join(self.run_location)
        calc_settings = DEFAULT_VASP_INCAR_SETTINGS['sc_forces']
        calc_settings.update(self.custom_calculation_settings.get('sc_forces', {}))
        initial_structure = self.initial_structure
        with files_and_folders.change_working_dir(calc_dir):
            if not from_scratch:
                previous_outcar = os.path.join(calc_dir, 'OUTCAR')
                if os.path.isfile(previous_outcar) and os.path.getsize(previous_outcar):
                    files_and_folders.backup_files()
            vcd, converged = self.do_static(structure=initial_structure,
                                            settings=calc_settings,
                                            mpi_call=self.mpi_call,
                                            **self.kwargs)
        with open('sc_forces_data.json', 'w') as fw:
            json.dump(vcd.as_dict(), fw, indent=2)

        if not converged:
            msg = 'Error during (scf) calculation of forces'
            raise KelpieWorkflowError(msg)

