#!/usr/bin/python
# This file is part of snolla. See README for more information.

from threading import Thread
import logging

import snolla.utils as utils

class SnollaWorker(Thread):
    """The Snolla main thread."""

    def __init__(self, config, commit_queue, bugzilla_task_queue):
        Thread.__init__(self)
        self.config = config
        self.commit_queue = commit_queue
        self.bugzilla_task_queue = bugzilla_task_queue
        self.log = logging.getLogger(__class__.__name__)

    def run(self):
        """Thread main loop."""
        while True:
            commit = self.commit_queue.get()
            self.log.debug('Start processing commit {id}.'.format(**commit))

            self.process(commit)

            self.log.info('Finished processing commit {id}.'.format(**commit))
            self.commit_queue.task_done()

    def process(self, commit):
        """Process a commit."""
        if not self.check_allowed_origins(commit):
            return

        # Extract action and bugid from commit.
        action_list = utils.extract_actions(commit['message'], self.config['general']['extract_regex'])
        if not action_list:
            self.log.warning('Could not find any action/bugid in commit {id}.'.format(**commit))
            return

        # Handle extracted actions
        for action, bugid in action_list:
            self.handle_extracted_action(action, bugid, commit)

    def check_allowed_origins(self, commit):
        """Check if the origin is allowed.

        Return True on success, False on failure."""
        if not utils.is_origin_allowed(commit['origin'], self.config['general']['allowed_origins']):
            self.log.warning('Commit {id} does not match any allowed origins (origin: {origin}).'.format(**commit))
            return False

        self.log.info('Commit {id} matches allowed origin: {origin}.'.format(**commit))
        return True

    def handle_extracted_action(self, action, bugid, commit):
        """Handle a single extracted action and bugid."""
        self.log.info('Found action "{}" for bug id {}.'.format(action, bugid))

        # Find suitable Bugzilla tasks for the extracted action.
        task = utils.get_bugzilla_task_for_action(action, utils.get_task_dict_from_config(self.config))
        if task:
            self.log.info('The action "{}" matches the Bugzilla task {}.'.format(action, task))
            self.bugzilla_task_queue.put(utils.create_bugzilla_task(task, bugid, commit))
        else:
            self.log.warning('The action "{}" does not match any Bugzilla task.'.format(action))

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
