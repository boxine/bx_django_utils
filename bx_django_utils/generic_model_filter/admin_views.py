"""
    Generic "AdminExtraView" view to filter accessible model by any field value.
    This is not a perfect solution, because some model field types are not supported.
"""

import dataclasses

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.admin.utils import label_for_field
from django.core.paginator import Paginator
from django.db import models
from django.db.models.options import Options
from django.forms import modelform_factory
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.views.generic import FormView

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta
from bx_django_utils.http import build_url_parameters
from bx_django_utils.json_utils import make_json_serializable
from bx_django_utils.models.get_models4user import SelectModelForm

SESSION_KEY = 'generic_model_filter'
IS_NULL_CHECK_PREFIX = 'is_null_check_'


def iter_model_fields(ModelClass: type[models.Model]):
    opts = ModelClass._meta
    model_fields = opts.get_fields()
    yield from model_fields


class NullChoices(models.TextChoices):
    """[no-doc] Choices for "isnull" fields."""

    __empty__ = '-----'
    IS_NULL = '0', 'is null'
    NOT_NULL = '1', 'is not null'


def make_search_form(ModelClass: type[models.Model], field_names: list[str]) -> type[forms.BaseForm]:
    """[no-doc] Generate a search form that also include "non-editable" fields."""
    editable_field_names = []
    non_editable_fields = []
    for model_field in iter_model_fields(ModelClass):
        if model_field.name not in field_names:
            continue

        if model_field.editable:
            editable_field_names.append(model_field.name)
        else:
            non_editable_fields.append(model_field)

    # Start with a model form that contains all editable fields:
    ModelValuesForm = modelform_factory(ModelClass, fields=editable_field_names)

    # Make all fields optional:
    for model_field in ModelValuesForm.base_fields.values():
        model_field.required = False

    # Add all non-editable fields:
    for model_field in non_editable_fields:
        form_field = model_field.formfield(required=False)
        ModelValuesForm.base_fields[model_field.name] = form_field

    # Add "isnull" choice fields to ModelValuesForm:
    for field_name in field_names:
        label = f'{IS_NULL_CHECK_PREFIX}{field_name}'
        is_null_field = forms.ChoiceField(
            label=label,
            required=False,
            choices=NullChoices.choices,
        )
        ModelValuesForm.base_fields[label] = is_null_field

    return ModelValuesForm


def get_model_field_choices(ModelClass, exclude_fields=()):
    opts = ModelClass._meta

    choices = []
    for field in iter_model_fields(ModelClass):
        if field.name in exclude_fields:
            continue

        if field.related_model:
            # TODO: Support relations
            continue

        if isinstance(field, models.FileField):
            # TODO: Support file fields by replace the input to a normal Charfield
            continue

        label = label_for_field(field.name, ModelClass, opts)
        choices.append((field.name, label))
    return choices


class SelectModelFieldsForm(forms.Form):
    """[no-doc] Select model fields for the search."""

    field_names = forms.MultipleChoiceField(label='Fields:')

    def __init__(self, *args, ModelClass, **kwargs):
        super().__init__(*args, **kwargs)

        field = self.fields['field_names']
        field.choices = get_model_field_choices(ModelClass)


@dataclasses.dataclass
class ModelFilterData:
    """[no-doc] Holds all data required to search in a model."""

    perform_search: bool = False

    # Step 1: selected model to be searched:
    model_name: str = None
    ModelClass: type[models.Model] = None

    # Step 2: selected fields to be searched on the selected model:
    field_names: list[str] = None
    ModelValuesForm: type[forms.BaseForm] = None

    def _set_model_name(self, model_name) -> None:
        self.model_name = model_name
        app_label, model_name = self.model_name.split('.')
        self.ModelClass = apps.get_model(app_label=app_label, model_name=model_name)

    def _set_field_names(self, field_names) -> None:
        self.field_names = field_names
        self.ModelValuesForm = make_search_form(ModelClass=self.ModelClass, field_names=self.field_names)

    @classmethod
    def from_query(cls, get_query: MultiValueDict) -> "ModelFilterData":
        data = cls()
        if model_name := get_query.get('model_name'):
            data._set_model_name(model_name)

        if field_names := get_query.getlist('field_names'):
            data._set_field_names(field_names)

        return data

    def update_by_cleaned_data(self, cleaned_data: dict) -> None:
        if model_name := cleaned_data.get('model_name'):
            # Step 1: selected model to be searched:
            self._set_model_name(model_name)
        elif field_names := cleaned_data.get('field_names'):
            # Step 2: selected fields to be searched on the selected model:
            self._set_field_names(field_names)

    def get_search_model_query_str(self) -> str:
        return build_url_parameters(model_name=self.model_name)

    def get_query_str(self) -> str:
        """
        :return: all current information as URL encoded string
        """
        parms = dict(model_name=self.model_name)
        if self.field_names:
            parms['field_names'] = self.field_names
        return build_url_parameters(**parms)


class GenericModelFilterBaseView(AdminExtraViewMixin, FormView):
    """
    Base "AdminExtraView" to add this view to the admin interface via @register_admin_view().
    """

    meta = AdminExtraMeta(name='Generic model item filter', app_label='generic-filter')
    template_name = 'generic_model_filter.html'

    def get(self, request, *args, **kwargs):
        self.data = ModelFilterData.from_query(get_query=request.GET)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.data = ModelFilterData.from_query(get_query=request.GET)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        if self.data.field_names:
            # Input the search values
            self.request.session[SESSION_KEY] = make_json_serializable(cleaned_data)
        else:
            self.data.update_by_cleaned_data(cleaned_data)

        query_str = self.data.get_query_str()
        url = reverse(self.meta.url_name)
        url = f'{url}?{query_str}'
        return HttpResponseRedirect(url)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.data.model_name and self.data.field_names:
            # Step 3 + 4: Input the search values / search with last input
            if self.request.method == 'POST':
                kwargs['data'] = self.request.POST
            elif SESSION_KEY in self.request.session:
                kwargs['data'] = self.request.session[SESSION_KEY]
        elif not self.data.model_name:
            # Step 1: SelectModelForm:
            kwargs['user'] = self.request.user
        elif not self.data.field_names:
            # Step 2: SelectModelFieldsForm:
            kwargs['ModelClass'] = self.data.ModelClass
            if SESSION_KEY in self.request.session:
                del self.request.session[SESSION_KEY]
        else:
            raise NotImplementedError

        return kwargs

    def get_form_class(self):
        if form_class := self.data.ModelValuesForm:
            # Step 3 + 4: Input the search values / search with last input
            return form_class
        elif not self.data.model_name:
            # Step 1: selected model to be searched:
            return SelectModelForm
        elif not self.data.field_names:
            # Step 2: selected fields to be searched on the selected model:
            return SelectModelFieldsForm
        else:
            raise NotImplementedError

    def get_context_data(self, **context):
        context = super().get_context_data(**context)

        context['title'] = self.meta.name

        start_url = reverse(self.meta.url_name)
        context['start_url'] = start_url

        if self.data.model_name and self.data.field_names:
            context['subtitle'] = 'Step 3: The field values used to filter the model'
            context['search_values_input'] = True
        elif not self.data.model_name:
            context['subtitle'] = 'Step 1: selected model to be searched'
        elif not self.data.field_names:
            context['subtitle'] = 'Step 2: selected fields to be searched on the selected model'

        if ModelClass := self.data.ModelClass:
            options: Options = ModelClass._meta
            context['opts'] = options

            search_model_query_str = self.data.get_search_model_query_str()
            context['search_model_url'] = f'{start_url}?{search_model_query_str}'

            if SESSION_KEY in self.request.session:
                raw_search_values = self.request.session[SESSION_KEY]

                qs_filter_kwargs = {}
                is_null_check_fields = []
                for key, value in raw_search_values.items():
                    if key.startswith(IS_NULL_CHECK_PREFIX):
                        if value == NullChoices.IS_NULL:
                            isnull = True
                        elif value == NullChoices.NOT_NULL:
                            isnull = False
                        else:
                            continue

                        model_field_name = key[len(IS_NULL_CHECK_PREFIX) :]
                        qs_filter_kwargs[f'{model_field_name}__isnull'] = isnull
                        is_null_check_fields.append(model_field_name)

                for key, value in raw_search_values.items():
                    if not key.startswith(IS_NULL_CHECK_PREFIX) and key not in is_null_check_fields:
                        qs_filter_kwargs[key] = value

                messages.info(self.request, f'Search with: {qs_filter_kwargs}')

                queryset = ModelClass.objects.all()
                context['total_count'] = queryset.count()

                queryset = queryset.filter(**qs_filter_kwargs)

                # Pagination may yield inconsistent results with an unordered object list
                order_by = queryset.query.order_by
                if not order_by:
                    if options.ordering:
                        # Order by Meta.ordering:
                        queryset = queryset.order_by(*options.ordering)
                    else:
                        queryset = queryset.order_by('pk')

                context['filtered_count'] = queryset.count()

                paginator = Paginator(queryset, 50)
                page_number = self.request.GET.get('__page')
                context['page_obj'] = paginator.get_page(page_number)
                context['query_str'] = self.data.get_query_str()

            # Collect "isnull" fields:
            form = context['form']
            regular_field_names = []
            null_fields = {}
            for form_field in form:
                field_name = form_field.name
                if field_name.startswith(IS_NULL_CHECK_PREFIX):
                    field_name = field_name[len(IS_NULL_CHECK_PREFIX) :]
                    null_fields[field_name] = form_field
                else:
                    regular_field_names.append(field_name)
            context['regular_field_names'] = regular_field_names

            # Add the "isnull" field to the regular field, for forms rendering:
            for form_field in form:
                if null_field := null_fields.get(form_field.name):
                    form_field.null_field = null_field

        return context
