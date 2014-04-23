#!/usr/bin/python
# This file is part of snolla. See README for more information.

import unittest
import json
import re
from configobj import ConfigObj

import snolla.utils as utils

class TestGitlabExtractData(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/gitlab_push_fixture_1.json', 'rt') as f:
            self.json_data = f.read()

    def test_no_commits(self):
        data = json.loads(self.json_data)
        del data['commits'][0]
        del data['commits'][0]

        result = utils.extract_gitlab_commit_data(data)
        self.assertListEqual([], result)

    def test_one_commit(self):
        data = json.loads(self.json_data)
        del data['commits'][1]

        result = utils.extract_gitlab_commit_data(data)
        self.assertEqual(len(result), 1)

        commit = result[0]
        self.assertEqual(commit['id'],
                'b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327')
        self.assertEqual(commit['origin'],
                'master')
        self.assertEqual(commit['message'],
                'Update Catalan translation to e38cb41.')
        self.assertEqual(commit['timestamp'],
                '2011-12-12T14:27:31+02:00')
        self.assertEqual(commit['url'],
                'http://localhost/diaspora/commits/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327')
        self.assertEqual(commit['author_name'],
                'Jordi Mallach')
        self.assertEqual(commit['author_email'],
                'jordi@softcatala.org')

    def test_multiple_commits(self):
        data = json.loads(self.json_data)

        result = utils.extract_gitlab_commit_data(data)

        self.assertEqual(len(result), 2)
        self.assertNotEqual(result[0], result[1])

    def test_raises_on_missing_item(self):
        data = json.loads(self.json_data)
        del data['commits'][0]['id']

        self.assertRaises(KeyError, utils.extract_gitlab_commit_data, data)


class TestSnollaExtractActions(unittest.TestCase):
    def setUp(self):
        self.regex = r'(?P<action>\w+)?:?\s*#(?P<bugid>\d+)'

    def test_empty_message(self):
        self.assertListEqual([], utils.extract_actions('', self.regex))

    def test_single_action(self):
        self.assertListEqual([('fixes', 18)],
                utils.extract_actions('comment (fixes: #18).', self.regex))

    def test_multiple_values(self):
        self.assertListEqual([('fixes', 18), ('closes', 20)],
                utils.extract_actions('fixes #18 and closes:#20', self.regex))

    def test_bugid_empty(self):
        self.assertListEqual([],
                utils.extract_actions('ixes 18).', self.regex))

    def test_action_empty(self):
        self.assertListEqual([('', 2)],
                utils.extract_actions('#2).', self.regex))

    def test_action_as_lower_str(self):
        self.assertListEqual([('fixes', 2)],
                utils.extract_actions('well (FiXES #2).', self.regex))


class TestIsOriginAllowed(unittest.TestCase):

    def setUp(self):
        self.allowed_origins = ('x', 'feature/foo', 'feature/foo/', 'bugfix/',
                'master')

    def test_empty_origin(self):
        self.assertFalse(utils.is_origin_allowed('',
            self.allowed_origins))

    def test_partial_origin(self):
        self.assertFalse(utils.is_origin_allowed('mast',
            self.allowed_origins))

    def test_origin_allowed(self):
        self.assertTrue(utils.is_origin_allowed('master',
            self.allowed_origins))

    def test_origin_in_group(self):
        self.assertTrue(utils.is_origin_allowed('bugfix/id2',
            self.allowed_origins))

    def test_origin_same_as_group(self):
        self.assertFalse(utils.is_origin_allowed('bugfix',
            self.allowed_origins))

    def test_origin_nested(self):
        self.assertTrue(utils.is_origin_allowed('bugfix/1/2/3',
            self.allowed_origins))

    def test_nested_with_single_origin_in_group(self):
        self.assertTrue(utils.is_origin_allowed('feature/foo',
            self.allowed_origins))

    def test_nested_with_match_in_subgroup(self):
        self.assertTrue(utils.is_origin_allowed('feature/foo/bar',
            self.allowed_origins))

    def test_nested_without_match_on_first_level(self):
        self.assertFalse(utils.is_origin_allowed('feature/blub',
            self.allowed_origins))

    def test_very_short_allowed_origin(self):
        self.assertFalse(utils.is_origin_allowed('x/no',
            self.allowed_origins))


class TestGetBugzillaTaskForAction(unittest.TestCase):

    def setUp(self):
        self.tasks = {
            'comment' : ['seealso', 'see', 'comment', 'comments'],
            'something' : ['other', 'anotherkey']
            }

    def test_empty_action(self):
        self.assertIsNone(utils.get_bugzilla_task_for_action('', self.tasks))

    def test_no_match(self):
        self.assertIsNone(utils.get_bugzilla_task_for_action('nonono', self.tasks))

    def test_match(self):
        self.assertEqual('comment', utils.get_bugzilla_task_for_action('see', self.tasks))

    def test_raises_on_invalid_tasks_type(self):
        self.assertRaises(AttributeError, utils.get_bugzilla_task_for_action, '', None)


class TestgetTaskDictFromConfig(unittest.TestCase):

    def test_empty_config(self):
        raw_config = ["[tasks]"]
        config = ConfigObj(raw_config)
        self.assertDictEqual({}, utils.get_task_dict_from_config(config))

    def test_single_task_with_two_keywords(self):
        raw_config = [
                "[tasks]",
                "[[comment]]",
                "enabled = True",
                "keywords = 'see', 'comment'"]
        config = ConfigObj(raw_config)
        self.assertDictEqual({'comment': ['see', 'comment']},
                utils.get_task_dict_from_config(config))

    def test_single_task_with_two_keywords_disabled(self):
        raw_config = [
                "[tasks]",
                "[[comment]]",
                "enabled = False",
                "keywords = 'see', 'comment'"]
        config = ConfigObj(raw_config)
        self.assertDictEqual({}, utils.get_task_dict_from_config(config))

    def test_two_tasks_with_one_keyword_each(self):
        raw_config = [
                "[tasks]",
                "[[comment]]",
                "enabled = True",
                "keywords = 'see',",
                "[[bar]]",
                "enabled = True",
                "keywords = 'foo',"]
        config = ConfigObj(raw_config)
        self.assertDictEqual({'comment': ['see'], 'bar': ['foo']},
                utils.get_task_dict_from_config(config))

    def test_two_tasks_with_just_one_task_enabled(self):
        raw_config = [
                "[tasks]",
                "[[comment]]",
                "enabled = True",
                "keywords = 'see',",
                "[[bar]]",
                "enabled = no",
                "keywords = 'foo',"]
        config = ConfigObj(raw_config)
        self.assertDictEqual({'comment': ['see']},
                utils.get_task_dict_from_config(config))

class TestCreateBugzillaTask(unittest.TestCase):

    def setUp(self):
        self.tpl = """
Author: {author_name} <{author_email}>
Date: {timestamp}
URL: {url}
Log: {message}
"""
        self.commit = {'author_name': 'Foo', 'author_email': 'foo@bar.at',
            'timestamp': '1', 'url': 'http://localhost/gitlab/1',
            'message': 'a message'}
        self.result = {
            'task': 'a task',
            'bugid': 1,
            'commit': self.commit}

    def test_full_bugzilla_task(self):
        self.assertDictEqual(self.result, utils.create_bugzilla_task('a task', 1, self.commit))

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
