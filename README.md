# Boxine - bx_py_utils

Various Python / Django utility functions


## Quickstart

```bash
pip install bx_py_utils
```


## Existing stuff

Here only a simple list about existing utilities.
Please take a look into the sources and tests for deeper informations.


### models utilities

* `approve_workflow` - Base model/admin/form classes to implement a model with draft/approve versions workflow
* `manipulate.create_or_update()` - Similar to django's `create_or_update()` with benefits
* `timetracking.TimetrackingBaseModel()` - Base model with "create" and "last update" date time

### data types

* `data_types.gtin` - ModelField, FormField and validators for GTIN/UPC/EAN numbers, more info: [data_types/gtin/README.md](https://github.com/boxine/bx_py_utils/blob/master/bx_py_utils/data_types/gtin/README.md)

### test utilities

* `datetime.MockDatetimeGenerator()` - Mock django `timezone.now()` with generic time stamps
* `datetime.parse_dt()` - Handy `datetime.strptime()` convert
* `html_assertion.HtmlAssertionMixin` - Unittest mixin class with usefull assertments around Django test client tests
* `model_clean_assert.CleanMock()` - Context manager to track if model `full_clean()` was called
* `users` - Utilities around user/permission setup for tests
* `time.MockTimeMonotonicGenerator()` - Mock `time.monotonic()` with generic time stamps
* `AssertQueries()` - Context manager with different checks of made database queries
* `assert_json_requests_mock()` - Check the requests history of `requests_mock.mock()`
* `assert_equal()` - Compare objects with a nice ndiff using pformat
* `assert_text_equal()` - Compare text strings with a nice ndiff
* `assert_snapshot` - Helper for quick snapshot test functionality (comparing value with one stored in a file using json)
* `assert_text_snapshot` - Same as `assert_snapshot` comparing text strings

### performance analysis

* `dbperf.query_recorder.SQLQueryRecorder` - Context Manager that records SQL queries executed via the Django ORM

### humanize

* `humanize.time.human_timedelta()` - Converts a time duration into a friendly text representation. (`X ms`, `sec`, `minutes` etc.)
* `templatetags.humanize_time.human_duration()` - Verbose time since template tag, e.g.: `<span title="Jan. 1, 2000, noon">2.0 seconds</span>`
* `filename.filename2human_name()` - Convert filename to a capitalized name
* `filename.clean_filename()` - Convert filename to ASCII only via slugify
* `pformat()` - Better `pretty-print-format` using JSON with fallback to `pprint.pformat()`

### view utilities

* `view_utils.dynamic_menu_urls.DynamicViewMenu()` - Register views to build a simple menu with sections


### AWS stuff

* `bx_py_utils.aws.secret_manager.SecretsManager` - Get values from AWS Secrets Manager
* `bx_py_utils.test_utils.mock_aws_secret_manager.SecretsManagerMock` - Mock our `SecretsManager()` helper in tests
* `bx_py_utils.test_utils.mock_boto3session.MockedBoto3Session` - Mock `boto3.session.Session()` (Currently only `get_secret_value()`)
* `bx_py_utils.aws.client_side_cert_manager.ClientSideCertManager` - Helper to manage client-side TLS certificate via AWS Secrets Manager

### GraphQL

* `graphql_introspection.introspection_query` Generate an introspection query to get an introspection doc.
* `graphql_introspection.complete_query` Generate a full query for all fields from an introspection doc.

### misc

* `dict_utils.dict_get()` - nested dict `get()`
* `dict_utils.pluck()` - Extract values from a dict, if they are present
* `environ.cgroup_memory_usage()` - Get the memory usage of the current cgroup
* `error_handling.print_exc_plus()` - Print traceback information with a listing of all the local variables in each frame
* `iteration.chunk_iterable()` - Create chunks off of any iterable
* `processify.processify()` - Will execute the decorated function in a separate process
* `stacktrace.get_stacktrace()` - Returns a filterable and easy-to-process stacktrace
* `anonymize.anonymize()` - Anonymize a string (With special handling of email addresses)
* `hash_utils.url_safe_hash()` - Generate URL safe hashes


## developing

To start developing e.g.:

```bash
~$ git clone https://github.com/boxine/bx_py_utils.git
~$ cd bx_py_utils
~/bx_py_utils$ make
help                 List all commands
install-poetry       install or update poetry
install              install via poetry
update               Update the dependencies as according to the pyproject.toml file
lint                 Run code formatters and linter
fix-code-style       Fix code formatting
tox-listenvs         List all tox test environments
tox                  Run pytest via tox with all environments
tox-py36             Run pytest via tox with *python v3.6*
tox-py37             Run pytest via tox with *python v3.7*
tox-py38             Run pytest via tox with *python v3.8*
tox-py39             Run pytest via tox with *python v3.9*
pytest               Run pytest
pytest-ci            Run pytest with CI settings
publish              Release new version to PyPi
makemessages         Make and compile locales message files
start-dev-server     Start Django dev. server with the test project
clean                Remove created files from the test project (e.g.: SQlite, static files)
```

You can start the test project with the Django developing server, e.g.:
```bash
~/bx_py_utils$ make start-dev-server
```
This is a own manage command, that will create migrations files from our test app, migrate, collectstatic and create a super user if no user exists ;)

If you like to start from stretch, just delete related test project files with:
```bash
~/bx_py_utils$ make clean
```
...and start the test server again ;)


## License

[MIT](LICENSE). Patches welcome!

## Links

* https://pypi.org/project/bx-py-utils/
