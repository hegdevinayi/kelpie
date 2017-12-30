batch_schedulers = ['slurm']

# module variable DEFAULT_BATCH_SCHEDULER_SETTINGS
DEFAULT_BATCH_SCHEDULER_SETTINGS = {}
for batch_scheduler in batch_schedulers:
    batch_scheduler_module = __import__(batch_scheduler)
    DEFAULT_BATCH_SCHEDULER_SETTINGS[batch_scheduler] = batch_scheduler_module.DEFAULT_SETTINGS
