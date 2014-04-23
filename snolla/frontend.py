#!/usr/bin/python
# This file is part of snolla. See README for more information.

from json import loads
from werkzeug.exceptions import HTTPException, BadRequest, NotFound, MethodNotAllowed
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response
import logging

import snolla.utils as utils

class Frontend():
    """The Snolla wsgi frontend."""

    def __init__(self, queue):
        """Setup the Snolla frontend."""
        self.queue = queue
        self.log = logging.getLogger(__class__.__name__)

        # URL map
        self.url_map = Map([
            Rule('/', endpoint='index'),
            Rule('/gitlab/push', endpoint='gitlab_push'),
        ])

    def on_index(self, request):
        """The index page."""
        self.log.debug('Received request: "{}".'.format(request))
        return Response('Welcome to Snolla.')

    def on_gitlab_push(self, request):
        """The endpoint for gitlab post commit hooks."""
        self.log.debug('Received request: "{}".'.format(request))
        if request.method == 'POST':
            if request.headers.get('content-type') == 'application/json':
                raw_data = request.stream.read().decode('utf-8')
                self.log.debug('Got POST data: "{}".'.format(raw_data))

                extracted_commits = utils.extract_gitlab_commit_data(loads(raw_data))
                for commit in extracted_commits:
                    self.queue.put(commit)

                msg = 'Successfully extracted {} commits.'.format(len(extracted_commits))
                self.log.info(msg)
                return Response(msg)
            else:
                msg = 'No POST data as application/json supplied.'
                self.log.warning(msg)
                return BadRequest(msg)
        else:
            return MethodNotAllowed()

    def dispatch_request(self, request):
        """Dispatch a request to one of the on_* members."""
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except NotFound as e:
            return NotFound()
        except HTTPException as e:
            return e

    def __call__(self, environ, start_response):
        """Callable wsgi app."""
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
