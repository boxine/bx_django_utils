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

* [`BaseApproveModelAdmin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/approve_workflow/admin.py#L15-L107) - Base admin class for a draft/approve Model

#### bx_django_utils.approve_workflow.forms

* [`PublishAdminForm()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/approve_workflow/forms.py#L7-L46) - Activate models REQUIRED_FIELDS_PUBLIC on approve

#### bx_django_utils.approve_workflow.models

* [`BaseApproveModel()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/approve_workflow/models.py#L14-L202) - Base model class for approve models *and* this relation models.
* [`BaseApproveWorkflowModel()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/approve_workflow/models.py#L205-L255) - Base model for approve workflow models.

#### bx_django_utils.data_types.gtin

ModelField, FormField and validators for GTIN/UPC/EAN numbers


##### bx_django_utils.data_types.gtin.form_fields

* [`GtinFormField()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/data_types/gtin/form_fields.py#L8-L28) - Form field with GTIN validator.

##### bx_django_utils.data_types.gtin.model_fields

* [`GtinModelField()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/data_types/gtin/model_fields.py#L10-L33) - GTIN model field

##### bx_django_utils.data_types.gtin.validators

* [`GtinValidator()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/data_types/gtin/validators.py#L33-L52) - Validate GTIN number
* [`validate_gtin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/data_types/gtin/validators.py#L12-L30) - It's the same as stdnum.ean.validate() but also accept ISBN-10

#### bx_django_utils.dbperf.cursor

* [`RecordingCursorWrapper()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/dbperf/cursor.py#L17-L115) - An implementation of django.db.backends.utils.CursorWrapper.

#### bx_django_utils.dbperf.query_recorder

* [`SQLQueryRecorder()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/dbperf/query_recorder.py#L95-L167) - A context manager that allows recording SQL queries executed during its lifetime.

### bx_django_utils.filename

* [`clean_filename()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/filename.py#L34-L64) - Convert filename to ASCII only via slugify.
* [`filename2human_name()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/filename.py#L7-L31) - Convert filename to a capitalized name.

#### bx_django_utils.humanize.pformat

* [`pformat()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/humanize/pformat.py#L6-L20) - Better `pretty-print-format` using `DjangoJSONEncoder` with fallback to `pprint.pformat()`

#### bx_django_utils.humanize.time

* [`human_timedelta()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/humanize/time.py#L18-L63) - Converts a time duration into a friendly text representation. (`X ms`, `sec`, `minutes` etc.)

### bx_django_utils.json_utils

* [`make_json_serializable()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/json_utils.py#L20-L37) - Convert value to a JSON serializable value, with convert callback for special objects.
* [`to_json()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/json_utils.py#L40-L56) - Convert value to JSON via make_json_serializable() and DjangoJSONEncoder()

#### bx_django_utils.models.color_field

* [`ColorModelField()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/color_field.py#L14-L29) - Hex color model field, e.g.: "#0055ff" (It's not a html color picker widget)
* [`HexColorValidator()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/color_field.py#L6-L11) - Hex color validator (seven-character hexadecimal notation, e.g.: "#0055ff")

#### bx_django_utils.models.manipulate

Utilities to manipulate objects in database via models:

* [`CreateOrUpdateResult()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L39-L63) - Result object returned by create_or_update2() with all information about create/save a model.
* [`InvalidStoreBehavior()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L19-L23) - Exception used in create_or_update() if "store_behavior" contains not existing field names.
* [`create()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L26-L36) - Create a new model instance with optional validate before create.
* [`create_or_update()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L197-L217) - Create a new model instance or update a existing one. Deprecated! Use: create_or_update2()
* [`create_or_update2()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L66-L194) - Create a new model instance or update a existing one and returns CreateOrUpdateResult instance

#### bx_django_utils.models.queryset_utils

* [`remove_filter()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/queryset_utils.py#L7-L32) - Remove a applied .filter() from a QuerySet
* [`remove_model_filter()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/queryset_utils.py#L35-L57) - Remove a applied .filter() from a QuerySet if it contains references to the specified model

#### bx_django_utils.models.timetracking

* [`TimetrackingBaseModel()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/timetracking.py#L8-L62) - Abstract base model that will automaticly set create/update Datetimes.

### bx_django_utils.stacktrace

* [`StackTrace()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/stacktrace.py#L21-L22) - Built-in mutable sequence.
* [`StacktraceAfter()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/stacktrace.py#L83-L111) - Generate a stack trace after a package was visited.
* [`get_stacktrace()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/stacktrace.py#L63-L80) - Returns a StackTrace object, which is a list of FrameInfo objects.

#### bx_django_utils.templatetags.humanize_time

* [`human_duration()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/templatetags/humanize_time.py#L15-L45) - Verbose time since template tag, e.g.: `<span title="Jan. 1, 2000, noon">2.0 seconds</span>`

### bx_django_utils.test_utils

Utilities / helper for writing tests.


#### bx_django_utils.test_utils.assert_queries

* [`AssertQueries()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/assert_queries.py#L30-L209) - Assert executed database queries: Check table names, duplicate/similar Queries.

#### bx_django_utils.test_utils.content_types

* [`ContentTypeCacheFixMixin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/content_types.py#L7-L35) - TestCase mixin to fill the ContentType cache to avoid flaky database queries.

#### bx_django_utils.test_utils.datetime

* [`MockDatetimeGenerator()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/datetime.py#L4-L50) - Mock django `timezone.now()` with generic time stamps in tests.

#### bx_django_utils.test_utils.html_assertion

* [`HtmlAssertionMixin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/html_assertion.py#L30-L132) - Unittest mixin class with useful assertments around Django test client tests
* [`assert_html_response_snapshot()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/html_assertion.py#L9-L27) - Assert a HttpResponse via snapshot file using assert_html_snapshot() from bx_py_utils.

#### bx_django_utils.test_utils.model_clean_assert

* [`AssertModelCleanCalled()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/model_clean_assert.py#L35-L86) - Context manager for assert that full_clean() was called for every model instance.
* [`CleanMock()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/model_clean_assert.py#L6-L32) - Track if full_clean() was called.

#### bx_django_utils.test_utils.users

* [`assert_permissions()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L29-L44) - Check user permissions.
* [`filter_permission_names()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L8-L26) - Generate a Permission model query filtered by names, e.g.: ['<app_label>.<codename>', ...]
* [`make_max_test_user()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L106-L140) - Create a test user with all permissions *except* the {exclude_permissions} ones.
* [`make_minimal_test_user()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L79-L103) - Create a test user and set given permissions.
* [`make_test_user()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L47-L76) - Create a test user and set given permissions.

#### bx_django_utils.view_utils.dynamic_menu_urls

* [`DynamicViewMenu()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/view_utils/dynamic_menu_urls.py#L4-L45) - Simple storage for store information about views/urls to build a menu.

[comment]: <> (✂✂✂ auto generated end ✂✂✂)

## developing

To start developing e.g.:

```bash
~$ git clone https://github.com/boxine/bx_django_utils.git
~$ cd bx_django_utils
~/bx_django_utils$ make
help                 List all commands
install-poetry       install or update poetry via pip
install              install via poetry
update               Update the dependencies as according to the pyproject.toml file
lint                 Run code formatters and linter
fix-code-style       Fix code formatting
tox-listenvs         List all tox test environments
tox                  Run pytest via tox with all environments
pytest               Run pytest
pytest-ci            Run pytest with CI settings
publish              Release new version to PyPi
docker-test          Run tests in docker
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


### update this README

This README will be updated via tests ;) But currently this is only done with Python 3.9 !
If your system Python version is not 3.9: Install this Python version and switch to it, e.g.:

```bash
~/bx_django_utils$ poetry env use python3.9
~/bx_django_utils$ make install
~/bx_django_utils$ make pytest
```

## License

[MIT](LICENSE). Patches welcome!


## About us

We’ve been rethinking the listening experience for kids and have created an ecosystem where haptic and listening experience are combined via smart technology - the Toniebox.

We are constantly looking for engineers to join our team in different areas. If you’d be interested in contributing to our platform, have a look at: https://tonies.com/jobs/


## Links

* https://pypi.org/project/bx-django-utils/
