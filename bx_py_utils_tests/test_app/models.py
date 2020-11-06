from django.db import models

from bx_py_utils.models.timetracking import TimetrackingBaseModel


class TimetrackingTestModel(TimetrackingBaseModel):
    pass


class CreateOrUpdateTestModel(TimetrackingBaseModel):
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
