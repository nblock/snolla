#!/usr/bin/python
# This file is part of snolla. See README for more information.

import re

# Format for messages in commit_queue:
# commit_format = {
    # "id": "<commit id>",
    # "origin": "<the short git refspec, eg. master>",
    # "message": "<commit message>",
    # "timestamp": "<iso 8601 timestamp with utc offset>",
    # "url": "<url to online diff of this commit>",
    # "author_name": "<author name>",
    # "author_email": "<author email>",
    # }

def is_origin_allowed(origin, allowed_origins):
    """
    Check if the given origin is allowed or not.

    Args:
        origin - The origin to check.
        allowed_origins - An iterable of allowed origins
    Returns:
        True if the origin is allowed, False otherwise.
    """
    for allowed in allowed_origins:
        if origin == allowed or \
                allowed.endswith('/') and origin.startswith(allowed):
            return True
    return False


def extract_actions(message, regex):
    """
    Extract actions and bugids for the given message and return all found
    tuples in a list. For example, the message 'A commit (Fixes #1).' will yield
    the list [('fixes' 1)].

    Args:
        message - The message to search on.
        regex - The regex to use. It must provide the match groups 'action'
                and 'bugid' in order to retrieve information. The value in the
                match group 'action' will be converted to a lowercase string
                and the value in the match group 'bugid' will be converted to
                an int.
    Returns:
        A list with tuples: [('action', 23), ('anotheraction', 42)] or an empty
        list no results were found.
    """
    results = []
    for mo in re.finditer(regex, message):
        action = mo.group('action') or ''
        results.append((action.lower(), int(mo.group('bugid'))))
    return results


def get_bugzilla_task_for_action(action, tasks):
    """
    Get the Bugzilla task for a given action.

    Args:
        action - The action to search for.
        tasks - The task dictionary to search in, eg:
                { 'task_1': ['action 1', 'action 2', ...] ... }.
    Returns:
        The matching task as str or None if no match was found.
    Raises:
        AttributeError if tasks is no dict.
    """
    for task, actions in tasks.items():
        if action in actions:
            return task
    return None


def get_task_dict_from_config(config):
    """
    Get the task dictionary from the configuration.

    Args:
        config - The parsed configuration.
    Returns:
        The tasks dictionary, eg:
            { 'task_1': ['action 1', 'action 2', ...] ... }.
    """
    return {task: config['tasks'][task]['keywords'] for task in
            config['tasks'].sections if config['tasks'][task].as_bool('enabled')}


def extract_gitlab_commit_data(data_dict):
    """Extract commit data from a parsed gitlab push json message.

    Returns:
        A list of commits in snolla format.
    Raises:
        KeyError in case one of the expected keys is not present.
    """
    result = []
    origin = re.sub(r'^refs/heads/', '', data_dict['ref'])
    for commit in data_dict['commits']:
        result.append({
                'id': commit['id'],
                'origin': origin,
                'message': commit['message'],
                'timestamp': commit['timestamp'],
                'url': commit['url'],
                'author_name': commit['author']['name'],
                'author_email': commit['author']['email'],
            })
    return result


def create_bugzilla_task(task, bugid, commit):
    """Create a task for the Bugzilla worker.

    Args:
        task - The bugzilla task.
        bugid - The bugid.
        commit - The commit dict, that contains the keys as specified in tpl.
    Returns:
        A dictionary: {'task': ..., 'bugid': ..., 'commit': ...}
    """
    return {
        'bugid': bugid,
        'commit': commit,
        'task': task,
        }

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
