import os
import subprocess
from kelpie.change_dir import change_working_dir
from kelpie.vasp_settings.incar import DEFAULT_VASP_INCAR_SETTINGS
from kelpie.vasp_input_generator import VaspInputGenerator
from kelpie.vasp_output_parser import VasprunXMLParser


class WorkflowError(Exception):
    """Base class to handle calculation workflow related errors."""
    pass


def check_convergence(calc_type, vasprunxml, calc_sett):



def run_vasp(mpi_call):
    with open('stdout.txt', 'w') as fstdout, open('stderr.txt', 'w') as fstderr:
        vasp_process = subprocess.run(mpi_call.split(), stdout=fstdout, stderr=fstderr)
    return vasp_process


def do_relaxation(structure,
                  calc_dir,
                  calc_sett,
                  mpi_call,
                  **kwargs):
    ig = VaspInputGenerator(structure=structure,
                            calculation_settings=calc_sett,
                            write_location=calc_dir,
                            **kwargs)
    ig.write_vasp_input_files()
    with change_working_dir(calc_dir):
        vasp_process = run_vasp(mpi_call)
    if vasp_process.returncode != 0:
        error_message = 'Something went wrong with the MPI VASP run'
        raise WorkflowError(error_message)



def relaxation_workflow(init_structure,
                        run_location,
                        custom_calculation_settings,
                        mpi_call,
                        **kwargs):
    calc_dir = os.path.join(run_location, 'relaxation')
    os.makedirs(calc_dir, exist_ok=True)
    calc_sett = DEFAULT_VASP_INCAR_SETTINGS['relaxation']
    calc_sett.update(custom_calculation_settings.get('relaxation'), {})
    do_relaxation(structure=init_structure,
                  calc_dir=calc_dir,
                  calc_sett=calc_sett,
                  mpi_call=mpi_call,
                  **kwargs)






class StaticWorkflow(object):


