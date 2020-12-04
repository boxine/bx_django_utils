from django import forms
from django.http import QueryDict

from bx_py_utils.approve_workflow.constants import POST_KEY_APPROVE


class PublishAdminForm(forms.ModelForm):
    """
    Activate models REQUIRED_FIELDS_PUBLIC on approve
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # This class used as normal admin ModelForm and for admin inline ModelForm
        # Both will be initialized in sightly other way. So we must do this:
        if 'data' in kwargs:
            # Inline Formset instance made with: form(**defaults)
            post_data = kwargs['data']
        elif args:
            # normal admin ModelForm instance made:
            #   ModelForm(request.POST, request.FILES, instance=obj)
            # or
            #   ModelForm(instance=obj)
            post_data = args[0]
        else:
            return

        assert isinstance(post_data, QueryDict)
        if post_data:
            self.set_required_fields(post_data)

    def get_required_fields(self, post_data):
        """
        Maybe overwrite this method and set other fields depend on post_data
        """
        return self.instance.REQUIRED_FIELDS_PUBLIC

    def set_required_fields(self, post_data):
        if POST_KEY_APPROVE in post_data:
            # "Approve" submit button was used
            # set more field as "required" as in model defined.
            required_fields = self.get_required_fields(post_data)
            for field_name, field in self.fields.items():
                if field_name in required_fields:
                    field.required = True
