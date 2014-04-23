#!/usr/bin/python
# This file is part of snolla. See README for more information.

from threading import Thread
import subprocess
import logging

class BugzillaWorker(Thread):
    """The Bugzilla worker."""

    def __init__(self, config, bugzilla_task_queue):
        """init."""
        Thread.__init__(self)
        self.config = config
        self.queue = bugzilla_task_queue
        self.bugzilla_default_args = self._setup_default_args()
        self.log = logging.getLogger(__class__.__name__)

    def _setup_default_args(self):
        """Setup the default args for python-bugzilla's bugzilla."""
        args_list = list()
        args_list.append(self.config['bugzilla']['bugzilla_path'])
        args_list.extend(self.config['bugzilla']['bugzilla_additional_args'])
        args_list.extend((
            "--bugzilla={}".format(self.config['bugzilla']['url']),
            "--user={}".format(self.config['bugzilla']['username']),
            "--password={}".format(self.config['bugzilla']['password'])))
        return args_list

    def external_command(self, args):
        """Execute an external command.

        Return True on success, False on failure."""
        try:
            subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            self.log.error('Exit code: "{}".'.format(e.returncode))
            self.log.error('Error message: "{}".'.format(e.output.decode('utf-8').strip()))
            self.log.error('Arguments: "{}".'.format(' '.join((e.cmd))))
            return False
        except OSError as e:
            self.log.exception(e)
            return False
        return True

    def run(self):
        """Thread main loop."""
        while True:
            task = self.queue.get()
            self.log.debug('Start processing task "{task}".'.format(**task))

            self.process(task)

            self.log.info('Finished processing task "{task}".'.format(**task))
            self.queue.task_done()

    def process(self, task):
        """Process a bugzilla task."""
        try:
            getattr(self, 'on_{task}'.format(**task))(task)
        except AttributeError as e:
            self.log.error(e)
            self.log.error('Unknown bugzilla task found: "{task}".'.format(**task))

    def on_comment(self, task):
        """Handle comment tasks."""
        args = self.bugzilla_default_args[:]
        args.extend((
            "modify",
            "{bugid}".format(**task),
            "--comment={}".format(self.config['tasks']['comment']['template']).format(**task['commit']))
            )
        if self.external_command(args) == True:
            self.log.info('Added a new comment to bug {bugid}.'.format(**task))
        else:
            self.log.error('Could not add a new comment to bug {bugid}.'.format(**task))

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
