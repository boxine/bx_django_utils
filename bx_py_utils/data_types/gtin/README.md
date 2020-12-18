# GTIN - Global Trade Item Number

* `bx_py_utils.data_types.gtin.model_fields.GtinModelField`
* `bx_py_utils.data_types.gtin.form_fields.GtinFormField`

default validation will accept only:

| Code   | Length    | Full Name               |
|--------|-----------|-------------------------|
| UPC    | 12        | Universal Product Code  |
| EAN    | 13 and 14 | European Article Number |

See: `bx_py_utils.data_types.gtin.constants.DEFAULT_ACCEPT_LENGTH`

You can see that these kinds of IDs will not accepted as default, e.g.:

* EAN-8
* ISBN-10

But model, form field and validators has a optional keyword argument `accepted_length`,
so you can accept more types.

Used parts from: [python-stdnum](https://arthurdejong.org/python-stdnum/)
