#!/usr/bin/python
# This file is part of snolla. See README for more information.

from configobj import ConfigObj, flatten_errors
from queue import Queue
from validate import Validator
import logging
import sys

from snolla.frontend import Frontend
from snolla.snolla import SnollaWorker
from snolla.bugzilla import BugzillaWorker


def load_config(configfile, configspec):
    """Load a configfile and validate it againsgt a configspec.

    The configfile is validated against the configspec. Each entry in configfile
    is validated against a matching configspec. Any errors will be printed.

    Returns:
        A tuple containing a bool flag indicating the validity of the parsed
        and the parsed config object."""
    config = ConfigObj(configfile, configspec=configspec,
            file_error=True, encoding='utf8')
    validation_result = config.validate(Validator(), preserve_errors=True)
    for entry in flatten_errors(config, validation_result):
        section_list, key, error = entry
        if key is not None:
           section_list.append(key)
        else:
            section_list.append('[missing section]')
        section_string = ', '.join(section_list)
        if error == False:
            error = 'Missing value or section.'
        print(section_string, ' = ', error)

    return (validation_result == True, config)


def create_app():
    """Create callable wsgi app."""
    # Load and validate the configuration
    valid, config = load_config('/etc/snolla.conf', configspec='config/snolla.conf.spec')
    if not valid:
        print('The supplied configuration is invalid.')
        sys.exit(1)

    # Setup logging
    logging.basicConfig(level=getattr(logging, config['general']['loglevel']))

    # Create the queues
    commit_queue = Queue()
    bugzilla_task_queue = Queue()

    # Start a Snolla worker thread
    tw = SnollaWorker(config, commit_queue, bugzilla_task_queue)
    tw.setDaemon(True)
    tw.start()

    # Start a Bugzilla task handler thread
    tw = BugzillaWorker(config, bugzilla_task_queue)
    tw.setDaemon(True)
    tw.start()

    # Setup the WSGI frontend
    return Frontend(commit_queue)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
