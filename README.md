# Boxine - bx_django_utils

Various Django utility functions

[![unittests](https://github.com/boxine/bx_django_utils/actions/workflows/pythonapp.yml/badge.svg?branch=master)](https://github.com/boxine/bx_django_utils/actions/workflows/pythonapp.yml) [![Coverage Status on codecov.io](https://codecov.io/gh/boxine/bx_django_utils/branch/master/graph/badge.svg)](https://codecov.io/gh/boxine/bx_django_utils)

[![bx_django_utils @ PyPi](https://img.shields.io/pypi/v/bx_django_utils?label=bx_django_utils%20%40%20PyPi)](https://pypi.org/project/bx_django_utils/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bx_django_utils)](https://gitlab.com/boxine/bx_django_utils/-/blob/main/pyproject.toml)
[![License MIT](https://img.shields.io/pypi/l/bx_django_utils)](https://gitlab.com/boxine/bx_django_utils/-/blob/main/LICENSE)


## Quickstart

```bash
pip install bx_django_utils
```

## Supported Django versions
`bx_django_utils` generally follows the support schedule of Django. The project is tested against [officially supported Django versions](https://endoflife.date/django) and [their respective supported CPython versions](https://docs.djangoproject.com/en/stable/faq/install/#what-python-version-can-i-use-with-django).

However, under special circumstances we may decide to pull support for a specific version early, e.g. if development of the library would be severely limited.
Check our tox test matrix for a definitive answer.

## Existing stuff

Here only a simple list about existing utilities.
Please take a look into the sources and tests for deeper informations.

[comment]: <> (✂✂✂ auto generated start ✂✂✂)

### bx_django_utils.admin_extra_views

Django Admin extra views: https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/README.md


#### bx_django_utils.admin_extra_views.admin_config

Activate "ExtraViewAdminSite" by set this as default admin site

* [`CustomAdminConfig()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/admin_config.py#L7-L12) - Change Django Admin Site to ExtraViewAdminSite for the extra views.

#### bx_django_utils.admin_extra_views.apps

* [`AdminExtraViewsAppConfig()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/apps.py#L6-L18) - App config to auto discover all extra views.

#### bx_django_utils.admin_extra_views.conditions

* [`only_staff_user()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/conditions.py#L4-L15) - Pass only active staff users. The default condition for all admin extra views.

#### bx_django_utils.admin_extra_views.datatypes

* [`AdminExtraMeta()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/datatypes.py#L15-L58) - Stores information for pseudo app and pseudo models.
* [`PseudoApp()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/datatypes.py#L61-L91) - Represents information about a Django App. Instance must be pass to @register_admin_view()

###### bx_django_utils.admin_extra_views.management.commands.admin_extra_views

* [`Command()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/management/commands/admin_extra_views.py#L7-L26) - Manage command "admin_extra_views": Info about registered admin extra views

#### bx_django_utils.admin_extra_views.registry

* [`AdminExtraViewRegistry()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/registry.py#L12-L101) - Hold all information about all admin extra views to expand urls and admin app list.
* [`register_admin_view()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/registry.py#L107-L120) - Decorator to add a normal view as pseudo App/Model to the admin.

#### bx_django_utils.admin_extra_views.site

* [`ExtraViewAdminSite()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/site.py#L6-L13) - An AdminSite object encapsulates an instance of the Django admin application, ready

##### bx_django_utils.admin_extra_views.tests.test_admin_extra_views

* [`AdminExtraViewsTestCase()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/tests/test_admin_extra_views.py#L10-L43) - Integrations tests for Admin Extra Views.

#### bx_django_utils.admin_extra_views.utils

* [`iter_admin_extra_views_urls()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/utils.py#L20-L26) - Iterate over all registered admin extra view urls.
* [`reverse_admin_extra_view()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/utils.py#L10-L17) - Get the URL of a Admin Extra View, e.g.: url=reverse_admin_extra_view(YouAdminExtraView)

#### bx_django_utils.admin_extra_views.views

* [`Redirect2AdminExtraView()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/views.py#L7-L23) - Redirect to a Admin Extra Views.

#### bx_django_utils.admin_utils.admin_urls

Helpers to build Admin URLs

* [`admin_change_url()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_utils/admin_urls.py#L62-L78) - Shortcut to generate Django admin "change" url for a model instance.
* [`admin_changelist_url()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_utils/admin_urls.py#L119-L134) - Shortcut to generate Django admin "changelist" url for a model or instance.
* [`admin_delete_url()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_utils/admin_urls.py#L100-L116) - Shortcut to generate Django admin "delete" url for a model instance.
* [`admin_history_url()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_utils/admin_urls.py#L81-L97) - Shortcut to generate Django admin "history" url for a model instance.
* [`admin_model_url()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_utils/admin_urls.py#L15-L59) - Build Admin change, add, changelist, etc. links with optional filter parameters.

#### bx_django_utils.admin_utils.filters

* [`ExistingCountedListFilter()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_utils/filters.py#L26-L62) - Advanced SimpleListFilter that list only existing filter values with counts.
* [`NotAllSimpleListFilter()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_utils/filters.py#L8-L23) - Similar to SimpleListFilter, but don't add "All" choice.

### bx_django_utils.approve_workflow

Base model/admin/form classes to implement a model with draft/approve versions workflow


#### bx_django_utils.approve_workflow.admin

* [`BaseApproveModelAdmin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/approve_workflow/admin.py#L15-L107) - Base admin class for a draft/approve Model

#### bx_django_utils.approve_workflow.forms

* [`PublishAdminForm()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/approve_workflow/forms.py#L7-L46) - Activate models REQUIRED_FIELDS_PUBLIC on approve

#### bx_django_utils.approve_workflow.models

* [`BaseApproveModel()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/approve_workflow/models.py#L14-L202) - Base model class for approve models *and* this relation models.
* [`BaseApproveWorkflowModel()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/approve_workflow/models.py#L205-L255) - Base model for approve workflow models.

### bx_django_utils.cached_dataclasses

* [`CachedDataclassBase()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/cached_dataclasses.py#L7-L59) - A Base dataclass that can be easy store/restore to Django cache.

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

* [`RecordingCursorWrapper()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/dbperf/cursor.py#L17-L136) - An implementation of django.db.backends.utils.CursorWrapper.

#### bx_django_utils.dbperf.query_recorder

* [`SQLQueryRecorder()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/dbperf/query_recorder.py#L95-L176) - A context manager that allows recording SQL queries executed during its lifetime.

### bx_django_utils.feature_flags

Feature flags: https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/feature_flags/README.md


#### bx_django_utils.feature_flags.admin_views

* [`ManageFeatureFlagsBaseView()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/feature_flags/admin_views.py#L30-L91) - Base admin extra view to manage all existing feature flags in admin.

#### bx_django_utils.feature_flags.data_classes

* [`FeatureFlag()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/feature_flags/data_classes.py#L17-L128) - A feature flag that persistent the state into django cache/database.

#### bx_django_utils.feature_flags.test_utils

* [`FeatureFlagTestCaseMixin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/feature_flags/test_utils.py#L35-L72) - Mixin for `TestCase` that will change `FeatureFlag` entries. To make the tests atomic.
* [`get_feature_flag_states()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/feature_flags/test_utils.py#L12-L17) - Collects information about all registered feature flags and their current state.

### bx_django_utils.filename

* [`clean_filename()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/filename.py#L34-L64) - Convert filename to ASCII only via slugify.
* [`filename2human_name()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/filename.py#L7-L31) - Convert filename to a capitalized name.

### bx_django_utils.http

* [`build_url_parameters()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/http.py#L4-L30) - Return an encoded string of all given parameters.

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

* [`CreateOrUpdateResult()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L50-L77) - Result object returned by create_or_update2() with all information about create/save a model.
* [`FieldUpdate()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L39-L47) - Information about updated model field values. Used for CreateOrUpdateResult.update_info
* [`InvalidStoreBehavior()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L19-L23) - Exception used in create_or_update() if "store_behavior" contains not existing field names.
* [`create()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L26-L36) - Create a new model instance with optional validate before create.
* [`create_or_update()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L235-L249) - Create a new model instance or update a existing one. Deprecated! Use: create_or_update2()
* [`create_or_update2()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L98-L232) - Create a new model instance or update a existing one and returns CreateOrUpdateResult instance
* [`update_model_field()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/manipulate.py#L80-L95) - Default callback for create_or_update2() to set a changed model field value and expand CreateOrUpdateResult

#### bx_django_utils.models.queryset_utils

* [`remove_filter()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/queryset_utils.py#L8-L38) - Remove an applied .filter() from a QuerySet
* [`remove_model_filter()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/queryset_utils.py#L41-L68) - Remove an applied .filter() from a QuerySet if it contains references to the specified model

#### bx_django_utils.models.timetracking

* [`TimetrackingBaseModel()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/models/timetracking.py#L8-L62) - Abstract base model that will automaticly set create/update Datetimes.

### bx_django_utils.stacktrace

* [`StackTrace()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/stacktrace.py#L21-L22) - Built-in mutable sequence.
* [`StacktraceAfter()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/stacktrace.py#L84-L112) - Generate a stack trace after a package was visited.
* [`get_stacktrace()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/stacktrace.py#L64-L81) - Returns a StackTrace object, which is a list of FrameInfo objects.

#### bx_django_utils.templatetags.accessors

* [`dict_get()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/templatetags/accessors.py#L7-L26) - Returns the wanted member of a dict-like container, or an empty string

#### bx_django_utils.templatetags.humanize_time

* [`human_duration()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/templatetags/humanize_time.py#L16-L58) - Verbose time since template tag, e.g.: `<span title="Jan. 1, 2000, noon">2.0 seconds</span>`

### bx_django_utils.test_utils

Utilities / helper for writing tests.


#### bx_django_utils.test_utils.assert_queries

* [`AssertQueries()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/assert_queries.py#L35-L288) - Assert executed database queries: Check table names, duplicate/similar Queries.

#### bx_django_utils.test_utils.cache

* [`ClearCacheMixin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/cache.py#L100-L111) - TestCase mixin to clear the Django cache in setUp/tearDown
* [`MockCache()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/cache.py#L55-L97) - Mock Django cache backend, so it's easy to check/manipulate the cache content

#### bx_django_utils.test_utils.content_types

* [`ContentTypeCacheFixMixin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/content_types.py#L7-L35) - TestCase mixin to fill the ContentType cache to avoid flaky database queries.

#### bx_django_utils.test_utils.datetime

* [`MockDatetimeGenerator()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/datetime.py#L4-L50) - Mock django `timezone.now()` with generic time stamps in tests.

#### bx_django_utils.test_utils.fixtures

Utilities to manage text fixtures in JSON files.

* [`BaseFixtures()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/fixtures.py#L28-L65) - Base class for JSON dump fixtures.
* [`FixturesRegistry()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/fixtures.py#L102-L140) - Registry to collect a list of all existing fixture classes.
* [`RenewAllFixturesBaseCommand()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/fixtures.py#L172-L248) - A base Django manage command to renew all existing fixture JSON dump files
* [`SerializerFixtures()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/fixtures.py#L68-L99) - Helper to store/restore model instances serialized into a JSON file.
* [`autodiscover()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/fixtures.py#L146-L169) - Register all fixtures by import all **/fixtures/**/*.py files

#### bx_django_utils.test_utils.forms

* [`AssertFormFields()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/forms.py#L13-L86) - Helper to check the existing form fields.

#### bx_django_utils.test_utils.html_assertion

* [`HtmlAssertionMixin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/html_assertion.py#L48-L184) - Unittest mixin class with useful assertments around Django test client tests
* [`assert_html_response_snapshot()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/html_assertion.py#L19-L45) - Assert a HttpResponse via snapshot file using assert_html_snapshot() from bx_py_utils.
* [`get_django_name_suffix()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/html_assertion.py#L12-L16) - Returns a short Django version string, useable for snapshot "name_suffix" e.g.: "django42"

#### bx_django_utils.test_utils.model_clean_assert

* [`AssertModelCleanCalled()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/model_clean_assert.py#L35-L86) - Context manager for assert that full_clean() was called for every model instance.
* [`CleanMock()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/model_clean_assert.py#L6-L32) - Track if full_clean() was called.

#### bx_django_utils.test_utils.playwright

Use Playwright in Unittest + Fast Django user login

* [`PlaywrightConfig()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/playwright.py#L13-L31) - PlaywrightTestCase config from environment (PWBROWSER, PWHEADLESS, PWSKIP, PWSLOWMO)
* [`PlaywrightTestCase()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/playwright.py#L34-L91) - StaticLiveServerTestCase with helpers for writing frontend tests using Playwright.

#### bx_django_utils.test_utils.users

* [`assert_permissions()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L31-L46) - Check user permissions.
* [`assert_user_properties()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L149-L171) - Check a user instance with all properties and password (optional)
* [`filter_permission_names()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L10-L28) - Generate a Permission model query filtered by names, e.g.: ['<app_label>.<codename>', ...]
* [`make_max_test_user()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L112-L146) - Create a test user with all permissions *except* the {exclude_permissions} ones.
* [`make_minimal_test_user()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L85-L109) - Create a test user and set given permissions.
* [`make_test_user()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/test_utils/users.py#L49-L82) - Create a test user and set given permissions.

### bx_django_utils.translation

* [`FieldTranslation()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L110-L128) - Dict-like container that maps language codes to a translated string.
* [`TranslationField()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L131-L259) - A field designed to hold translations for a given set of language codes.
* [`TranslationFieldAdmin()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L408-L469) - Provides drop-in support for ModelAdmin classes that want to display TranslationFields
* [`TranslationFormField()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L63-L107) - Default form field for TranslationField.
* [`TranslationSlugField()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L316-L405) - A unique translation slug field, useful in combination with TranslationField()
* [`create_or_update_translation_callback()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L472-L505) - Callback for create_or_update2() for TranslationField, that will never remove existing translation.
* [`expand_languages_codes()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L578-L598) - Build a complete list if language code with and without dialects.
* [`get_user_priorities()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L601-L614) - Collect usable language codes the current user
* [`make_unique()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L566-L575) - Flat args and remove duplicate entries while keeping the order intact.
* [`merge_translations()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L519-L530) - Merge two FieldTranslation and ignore all empty/None values, e.g.:
* [`remove_empty_translations()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L508-L516) - Remove all empty/None from a FieldTranslation, e.g.:
* [`user_language_priorities()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L617-L625) - Returns the order in which to attempt resolving translations of a FieldTranslation model field.
* [`validate_unique_translations()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/translation.py#L533-L563) - Deny creating non-unique translation: Creates ValidationError with change list search for doubled entries.

### bx_django_utils.user_timezone

Automatic local user timezone: https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/user_timezone/README.md


#### bx_django_utils.user_timezone.apps

* [`UserTimezoneAppConfig()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/user_timezone/apps.py#L4-L14) - Django app to set the user local time zone.

#### bx_django_utils.user_timezone.humanize

* [`human_timezone_datetime()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/user_timezone/humanize.py#L7-L21) - Render a datetime with timezone information.

#### bx_django_utils.user_timezone.middleware

* [`InvalidUserTimeZone()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/user_timezone/middleware.py#L11-L12) - Inappropriate argument value (of correct type).
* [`UserTimezoneMiddleware()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/user_timezone/middleware.py#L34-L68) - Activate Timezone by "UserTimeZone" cookie
* [`validate()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/user_timezone/middleware.py#L15-L31) - Validate the UserTimeZone cookie value.

##### bx_django_utils.user_timezone.templatetags.user_timezone

* [`humane_timezone_dt()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/user_timezone/templatetags/user_timezone.py#L9-L14) - Template filter to render a datetime with timezone information.

### bx_django_utils.version

* [`DetermineVersionCommand()`](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/version.py#L50-L78) - Write application version determined from git as a command

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
install-poetry       install poetry
install              install via poetry
update               Update the dependencies as according to the pyproject.toml file
lint                 Run code formatters and linter
fix-code-style       Fix code formatting
tox-listenvs         List all tox test environments
tox                  Run unittests via tox with all environments
test                 Run unittests
publish              Release new version to PyPi
docker-test          Run tests in docker
makemessages         Make and compile locales message files
start-dev-server     Start Django dev. server with the test project
clean                Remove created files from the test project (e.g.: SQlite, static files)
playwright-install   Install test browser for Playwright tests
playwright-inspector Run Playwright inspector
playwright-tests     Run only the Playwright tests
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


## About us

We’ve been rethinking the listening experience for kids and have created an ecosystem where haptic and listening experience are combined via smart technology - the Toniebox.

We are constantly looking for engineers to join our team in different areas. If you’d be interested in contributing to our platform, have a look at: https://tonies.com/jobs/


## Links

* https://pypi.org/project/bx-django-utils/
