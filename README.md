# Boxine - bx_django_utils

Various Django utility functions


## Quickstart

```bash
pip install bx_django_utils
```


## Existing stuff

Here only a simple list about existing utilities.
Please take a look into the sources and tests for deeper informations.

[comment]: <> (✂✂✂ auto generated start ✂✂✂)

### bx_django_utils.approve_workflow

Base model/admin/form classes to implement a model with draft/approve versions workflow


#### bx_django_utils.approve_workflow.admin

* `BaseApproveModelAdmin()` - Base admin class for a draft/approve Model

#### bx_django_utils.approve_workflow.forms

* `PublishAdminForm()` - Activate models REQUIRED_FIELDS_PUBLIC on approve

#### bx_django_utils.approve_workflow.models

* `BaseApproveModel()` - Base model class for approve models *and* this relation models.
* `BaseApproveWorkflowModel()` - Base model for approve workflow models.

#### bx_django_utils.data_types.gtin

ModelField, FormField and validators for GTIN/UPC/EAN numbers


##### bx_django_utils.data_types.gtin.form_fields

* `GtinFormField()` - Form field with GTIN validator.

##### bx_django_utils.data_types.gtin.model_fields

* `GtinModelField()` - GTIN model field

##### bx_django_utils.data_types.gtin.validators

* `GtinValidator()` - Validate GTIN number
* `validate_gtin()` - It's the same as stdnum.ean.validate() but also accept ISBN-10

#### bx_django_utils.dbperf.cursor

* `RecordingCursorWrapper()` - An implementation of django.db.backends.utils.CursorWrapper.

#### bx_django_utils.dbperf.query_recorder

* `SQLQueryRecorder()` - A context manager that allows recording SQL queries executed during its lifetime.

### bx_django_utils.filename

* `clean_filename()` - Convert filename to ASCII only via slugify.
* `filename2human_name()` - Convert filename to a capitalized name.

#### bx_django_utils.humanize.pformat

* `pformat()` - Better `pretty-print-format` using `DjangoJSONEncoder` with fallback to `pprint.pformat()`

#### bx_django_utils.humanize.time

* `human_timedelta()` - Converts a time duration into a friendly text representation. (`X ms`, `sec`, `minutes` etc.)

#### bx_django_utils.models.manipulate

Utilities to manipulate objects in database via models:

* `create()` - Create a new model instance with optional validate before create.
* `create_or_update()` - Create a new model instance or update a existing one.

#### bx_django_utils.models.timetracking

* `TimetrackingBaseModel()` - Abstract base model that will automaticly set create/update Datetimes.

### bx_django_utils.stacktrace

* `StackTrace()` - Built-in mutable sequence.
* `StacktraceAfter()` - Generate a stack trace after a package was visited.
* `get_stacktrace()` - Returns a StackTrace object, which is a list of FrameInfo objects.

#### bx_django_utils.templatetags.humanize_time

* `human_duration()` - Verbose time since template tag, e.g.: `<span title="Jan. 1, 2000, noon">2.0 seconds</span>`

### bx_django_utils.test_utils

Utilities / helper for writing tests.


#### bx_django_utils.test_utils.assert_queries

* `AssertQueries()` - Assert executed database queries: Check table names, duplicate/similar Queries.

#### bx_django_utils.test_utils.datetime

* `MockDatetimeGenerator()` - Mock django `timezone.now()` with generic time stamps in tests.

#### bx_django_utils.test_utils.html_assertion

* `HtmlAssertionMixin()` - Unittest mixin class with useful assertments around Django test client tests

#### bx_django_utils.test_utils.model_clean_assert

* `AssertModelCleanCalled()` - Context manager for assert that full_clean() was called for every model instance.
* `CleanMock()` - Track if full_clean() was called.

#### bx_django_utils.test_utils.users

* `assert_permissions()` - Check user permissions.
* `filter_permission_names()` - Generate a Permission model query filtered by names, e.g.: ['<app_label>.<codename>', ...]
* `make_max_test_user()` - Create a test user with all permissions *except* the {exclude_permissions} ones.
* `make_minimal_test_user()` - Create a test user and set given permissions.
* `make_test_user()` - Create a test user and set given permissions.

#### bx_django_utils.view_utils.dynamic_menu_urls

* `DynamicViewMenu()` - Simple storage for store information about views/urls to build a menu.

[comment]: <> (✂✂✂ auto generated end ✂✂✂)

## developing

To start developing e.g.:

```bash
~$ git clone https://github.com/boxine/bx_django_utils.git
~$ cd bx_django_utils
~/bx_django_utils$ make
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
~/bx_django_utils$ make start-dev-server
```
This is a own manage command, that will create migrations files from our test app, migrate, collectstatic and create a super user if no user exists ;)

If you like to start from stretch, just delete related test project files with:
```bash
~/bx_django_utils$ make clean
```
...and start the test server again ;)


## License

[MIT](LICENSE). Patches welcome!

## Links

* https://pypi.org/project/bx-django-utils/
