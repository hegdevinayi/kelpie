import argparse


class KelpieArgumentParser(argparse.ArgumentParser):
    """Argument parser wrapper for command line kelpie."""
    def __init__(self, *args, **kwargs):
        if not kwargs.get('formatter_class'):
            kwargs['formatter_class'] = argparse.RawTextHelpFormatter
        super(KelpieArgumentParser, self).__init__(*args, **kwargs, add_help=False)

        general_args = self.add_argument_group(title='General arguments')
        scheduler_args = self.add_argument_group(title='Batch scheduler-related arguments')
        calculation_args = self.add_argument_group(title='DFT calculation-related arguments')

        ######################################################################
        # General arguments (optional)
        ######################################################################
        input_structure_help = """Location of the file with the structure to calculate.
REQUIRED if mode is "breed" (see below).

"""
        general_args.add_argument('-i', '--input-structure-file',
                                  default=None,
                                  help=input_structure_help)

        mode_help = """Mode to run kelpie in:
breed: Generate the necessary directory structure, job file, and submit job.
graze: Perform the specified calculation workflow using the specified DFT code.
herd:  Gather data for all the calculations performed during grazing.

"""
        general_args.add_argument('-m', '--mode',
                                  default='breed',
                                  choices=['breed', 'graze', 'herd'],
                                  help=mode_help)

        submit_help = """Should the batch job be submitted to the scheduler?
Only relevant for "breed" mode, ignored otherwise. Defaults to "true".

"""
        general_args.add_argument('-s', '--submit-batch-job',
                                  default='true',
                                  choices=['true', 'false'],
                                  help=submit_help)

        run_location_help = """Path/location where the calculations need to be run.
Directories along the path specified will be created if not already present.
Defaults to the current working directory.

"""
        general_args.add_argument('-l', '--run-location',
                                  default=None,
                                  help=run_location_help)

        help_help = """Show this help message and exit

"""
        general_args.add_argument('-h', '--help',
                                  action='help',
                                  help=help_help)

        ######################################################################
        # Batch scheduler related arguments (optional)
        ######################################################################
        host_scheduler_help = """Name of a predefined host or path to a JSON file
with the scheduler settings. If a name is specified, must be one of the hosts
defined in `kelpie.scheduler_settings` (i.e., with a corresponding
"[host_scheduler].json" file. their values. Path to JSON file takes precedence.
Defaults to "cori_knl".

"""
        scheduler_args.add_argument('-hss', '--host-scheduler-settings',
                                    default=None,
                                    help=host_scheduler_help)

        custom_scheduler_help = """Path to a JSON file with a dictionary of tags
and *nondefault* values to go into the batch script. (The default settings
dictionary, if loaded based on the host-scheduler specified with the "-hs" tag
will be updated.

"""
        scheduler_args.add_argument('-css', '--custom-scheduler-settings',
                                    default=None,
                                    help=custom_scheduler_help)

        batch_script_help = """Name of a predefined template file or path to a file
with a template of the batch script to use to submit jobs. Name of the
predefined template must be one of those in the "scheduler_settings" directory.
Path to a template file takes precedence.
Defaults to "cori".

"""
        scheduler_args.add_argument('-bst', '--batch-script-template',
                                    default=None,
                                    help=batch_script_help)

        ######################################################################
        # DFT calculation/settings related arguments (optional)
        ######################################################################
        calculation_workflow_help = """Tag specifying the calculation workflow to
perform. Currently only "relaxation" and "static" implemented. Default settings
for each calculation in the workflow are predefined.
Defaults to "relaxation".

"""
        calculation_args.add_argument('-w', '--calculation-workflow',
                                      default='relaxation',
                                      choices=['relaxation', 'static',
                                               'acc_std_relax', 'sc_forces'],
                                      help=calculation_workflow_help)

        custom_calculation_settings_help = """Absolute path to a JSON file with a
dictionary of *nondefault* INCAR and POTCAR settings for each calculation type. The
default calculation settings dictionary loaded according to the workflow will be
updated. E.g., {"relaxation": {"ediff": 1E-8}, "static": {"sigma": 0.05}}

"""
        calculation_args.add_argument('-ccs', '--custom-calculation-settings',
                                      default=None,
                                      help=custom_calculation_settings_help)

