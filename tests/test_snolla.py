#!/usr/bin/python
# This file is part of snolla. See README for more information.

import logging
import unittest
import unittest.mock as mock

from snolla.snolla import SnollaWorker

class TestSnollaWorker(unittest.TestCase):

    def setUp(self):
        # Disable logging during unittests
        logging.disable(logging.CRITICAL)

        # A sample config
        self.cfg = {
            'general': {
                'allowed_origins': 'anything',
                'extract_regex': 'something'
                }
            }

        # A sample commit
        self.commit = {'origin': 'anything', 'id': 1, 'message': 'msg'}


    @mock.patch('snolla.utils.create_bugzilla_task')
    @mock.patch('snolla.utils.get_task_dict_from_config')
    @mock.patch('snolla.utils.get_bugzilla_task_for_action')
    def test_check_allowed_origins_no_match(self, mock_task, mock_config, mock_create):
        mock_task.return_value = None
        mock_config.return_value = 'foo'

        mock_queue = mock.MagicMock()
        obj = SnollaWorker(self.cfg, None, mock_queue)
        obj.handle_extracted_action('action', 1, 'the commit')

        mock_task.assert_called_once_with('action', mock_config.return_value)
        mock_config.assert_called_once_with(self.cfg)
        self.assertFalse(mock_queue.called)
        self.assertFalse(mock_create.called)

    @mock.patch('snolla.utils.create_bugzilla_task')
    @mock.patch('snolla.utils.get_task_dict_from_config')
    @mock.patch('snolla.utils.get_bugzilla_task_for_action')
    def test_check_allowed_origins_match(self, mock_task, mock_config, mock_create):
        mock_task.return_value = 'afinetask'
        mock_config.return_value = 'foo'
        mock_create.return_value = 'the bugzilla task'

        mock_queue = mock.MagicMock()
        obj = SnollaWorker(self.cfg, None, mock_queue)
        obj.handle_extracted_action('action', 1, 'the commit')

        mock_task.assert_called_once_with('action', mock_config.return_value)
        mock_config.assert_called_once_with(self.cfg)
        mock_create.assert_called_once_with('afinetask', 1, 'the commit')
        mock_queue.put.assert_called_once_with('the bugzilla task')

    @mock.patch('snolla.utils.is_origin_allowed')
    def test_handle_extracted_action(self, mock_origin):
        mock_origin.return_value = False
        obj = SnollaWorker(self.cfg, None, None)

        # Check False
        self.assertFalse(obj.check_allowed_origins(self.commit))
        mock_origin.assert_called_once_with(self.commit['origin'], self.cfg['general']['allowed_origins'])

        # Check True
        mock_origin.reset_mock()
        mock_origin.return_value = True
        self.assertTrue(obj.check_allowed_origins(self.commit))
        mock_origin.assert_called_once_with(self.commit['origin'], self.cfg['general']['allowed_origins'])

    @mock.patch('snolla.utils.extract_actions')
    @mock.patch('snolla.snolla.SnollaWorker.check_allowed_origins')
    def test_process_allowed_origins_no_match(self, mock_origin, mock_extract):
        mock_origin.return_value = False

        obj = SnollaWorker(self.cfg, None, None)
        obj.process(self.commit)

        mock_origin.assert_called_once_with(self.commit)
        self.assertFalse(mock_extract.called)

    @mock.patch('snolla.snolla.SnollaWorker.handle_extracted_action')
    @mock.patch('snolla.utils.extract_actions')
    @mock.patch('snolla.snolla.SnollaWorker.check_allowed_origins')
    def test_process_empty_extracted_actions(self, mock_origin, mock_extract, mock_handle):
        mock_origin.return_value = True
        mock_extract.return_value = []

        obj = SnollaWorker(self.cfg, None, None)
        obj.process(self.commit)

        mock_origin.assert_called_once_with(self.commit)
        mock_extract.assert_called_once_with(self.commit['message'], self.cfg['general']['extract_regex'])
        self.assertFalse(mock_handle.called)

    @mock.patch('snolla.snolla.SnollaWorker.handle_extracted_action')
    @mock.patch('snolla.utils.extract_actions')
    @mock.patch('snolla.snolla.SnollaWorker.check_allowed_origins')
    def test_process_has_action_and_bugid(self, mock_origin, mock_extract, mock_handle):
        mock_origin.return_value = True
        mock_extract.return_value = [('action1', 1), ('action2', 2)]

        obj = SnollaWorker(self.cfg, None, None)
        obj.process(self.commit)

        mock_origin.assert_called_once_with(self.commit)
        mock_extract.assert_called_once_with(self.commit['message'], self.cfg['general']['extract_regex'])

        expected = [mock.call(action, bugid, self.commit) for action, bugid in mock_extract.return_value]
        self.assertEqual(expected, mock_handle.call_args_list)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
