# Configuration spec for Snolla.

# Validate entries of the general section
[general]
allowed_origins = string_list(min=1, default=list('master'))
extract_regex = string(default='(?P<action>\w+)?:?\s*#(?P<bugid>\d+)')
loglevel = option('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', default='INFO')

# Validate entries of the tasks section
[tasks]
[[comment]]
enabled = boolean(default=True)
keywords = string_list(min=1, default=list('comment', 'comments', 'mention', 'mentions', 'see', 'seealso'))
template = string(default='')

# Validate entries of the bugzilla section
[bugzilla]
url = string(min=1)
username = string(min=1)
password = string(min=1)
bugzilla_path = string(default='bugzilla')
bugzilla_additional_args = string_list(default=list())
