import argparse


class KelpieArgumentParser(argparse.ArgumentParser):
    """Argument parser wrapper for command line kelpie."""
    def __init__(self, *args, **kwargs):
        if not kwargs.get('formatter_class'):
            kwargs['formatter_class'] = argparse.RawTextHelpFormatter
        super(KelpieArgumentParser, self).__init__(*args, **kwargs)

        general_args = self.add_argument_group(title='general', description='General options')
        scheduler_args = self.add_argument_group(title='scheduler', description='Batch scheduler-related options')
        calculation_args = self.add_argument_group(title='calculation', description='DFT calculation-related options')

        ######################################################################
        # General arguments
        ######################################################################
        mode_help = """Mode to run kelpie in:
breed: Generate the necessary directory structure, input files, job files.
graze: Perform the specified calculation workflow using the specified DFT code.
herd:  Gather data for all the calculations performed during grazing.
all:   Breed, graze and herd.
"""
        general_args.add_argument('-m', '--mode',
                                  default='all',
                                  choices=['breed', 'graze', 'herd', 'all'],
                                  help=mode_help)

        input_structure_help = """Location of the file with the structure to
calculate. If there are more than one structure to be calculated (e.g.
"multiple" mode), the location should be of a JSON file with the list of input
structure files to calculate.
"""
        general_args.add_argument('-i', '--input-structure-file',
                                  default=None,
                                  required=True,
                                  help=input_structure_help)

        run_location_help = """Path/location where the calculations need to be run.
Directories along the path specified will be created if not already present.
"""
        general_args.add_argument('-r', '--run-location',
                                  default=None,
                                  help=run_location_help)

        ######################################################################
        # Batch scheduler related arguments
        ######################################################################
        host_scheduler_help = """Name of a predefined host or path to a JSON file
with the scheduler settings. If a name is specified, must be one of the hosts
defined in `kelpie.scheduler_settings` (i.e., with a corresponding
"[host_scheduler].json" file. their values. Path to JSON file takes precedence.
"""
        scheduler_args.add_argument('-hs', '--host-scheduler-settings',
                                    default=None,
                                    help=host_scheduler_help)

        custom_scheduler_help = """Path to a JSON file with a dictionary of tags
and *nondefault* values to go into the batch script. (The default settings
dictionary, if loaded based on the host-scheduler specified with the "-hs" tag
will be updated.
"""
        scheduler_args.add_argument('-cs', '--custom-scheduler-settings',
                                    default=None,
                                    help=custom_scheduler_help)

        batch_script_help = """Name of a predefined template file or path to a file
with a template of the batch script to use to submit jobs. Name of the
predefined template must be one of those in the "scheduler_settings" directory.
Path to a template file takes precedence.
"""
        scheduler_args.add_argument('-bs', '--batch-script-template',
                                    default=None,
                                    help=batch_script_help)

        ######################################################################
        # DFT calculation/settings related arguments
        ######################################################################
        calculation_workflow_help = """Tag specifying the calculation workflow to
perform. Currently only "relaxation" and "static" implemented. Default settings
for each calculation in the workflow are predefined.
"""
        calculation_args.add_argument('-w', '--workflow',
                                      default='static',
                                      choices=['relaxation', 'static'],
                                      help=calculation_workflow_help)

        custom_calculation_settings_help = """Path to a JSON file with a dictionary
of *nondefault* INCAR and POTCAR settings for each calculation type. The default
calculation settings dictionary loaded according to the workflow will be
updated. E.g., {"relaxation": {"ediff": 1E-8}, "static": {"sigma": 0.05}}
"""
        calculation_args.add_argument('-ccs', '--custom-calculation-settings',
                                      default=None,
                                      help=custom_calculation_settings_help)


