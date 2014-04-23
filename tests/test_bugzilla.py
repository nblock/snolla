#!/usr/bin/python
# This file is part of snolla. See README for more information.

import logging
import subprocess
import unittest
import unittest.mock as mock

from snolla.bugzilla import BugzillaWorker

class TestBugzillaWorker(unittest.TestCase):

    def setUp(self):
        # Disable logging during unittests
        logging.disable(logging.CRITICAL)

        # A sample config
        self.cfg = {
            'bugzilla': {
                    'bugzilla_path': 'a_path',
                    'bugzilla_additional_args': list(),
                    'url': 'thebugzillaurl',
                    'username': 'username',
                    'password': 'password',
                    },
            'tasks': {
                'comment': {
                    'template': 'x{author_name}y'
                    }
                }
            }

    @mock.patch('subprocess.check_output')
    def test_external_command_ok(self, mock_output):
        obj = BugzillaWorker(self.cfg, None)

        args = ['my', 'args']
        self.assertTrue(obj.external_command(args))
        mock_output.assert_called_once_with(args)

    @mock.patch('subprocess.check_output')
    def test_external_command_raises_subprocess_error(self, mock_output):
        mock_output.side_effect = subprocess.CalledProcessError(1, 'msg', b'output')
        obj = BugzillaWorker(self.cfg, None)

        args = ['my', 'args']
        self.assertFalse(obj.external_command(args))
        mock_output.assert_called_once_with(args)

    @mock.patch('subprocess.check_output')
    def test_external_command_raises_oserror(self, mock_output):
        mock_output.side_effect = OSError()
        obj = BugzillaWorker(self.cfg, None)

        args = ['my', 'args']
        self.assertFalse(obj.external_command(args))
        mock_output.assert_called_once_with(args)

    def test_check_handlers_present(self):
        obj = BugzillaWorker(self.cfg, None)
        self.assertTrue(hasattr(obj, 'on_comment'))

    @mock.patch('snolla.bugzilla.BugzillaWorker.on_comment')
    def test_process_ok(self, mock_comment):
        task = {'task': 'comment'}
        obj = BugzillaWorker(self.cfg, None)
        obj.process(task)
        mock_comment.assert_called_once_with(task)

    @mock.patch('snolla.bugzilla.BugzillaWorker.on_comment')
    def test_process_failed(self, mock_comment):
        obj = BugzillaWorker(self.cfg, None)
        obj.process({'task': 'not_found'})
        self.assertFalse(mock_comment.called)

    @mock.patch('snolla.bugzilla.BugzillaWorker.external_command')
    def test_on_comment(self, mock_ext):
        obj = BugzillaWorker(self.cfg, None)
        args = obj._setup_default_args()
        args.extend(('modify', '1', '--comment=xfoo bary'))

        # Command succeeds
        mock_ext.return_value = True
        obj.on_comment({'bugid': 1, 'commit': {'author_name': 'foo bar'}})
        mock_ext.assert_called_once_with(args)

        # Command fails
        mock_ext.reset_mock()
        mock_ext.return_value = False
        obj.on_comment({'bugid': 1, 'commit': {'author_name': 'foo bar'}})
        mock_ext.assert_called_once_with(args)

    def test_setup_default_command(self):
        obj = BugzillaWorker(self.cfg, None)

        expected = ['a_path', '--bugzilla=thebugzillaurl', '--user=username', '--password=password']
        self.assertListEqual(expected, obj._setup_default_args())

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
