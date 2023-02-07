from django import template


register = template.Library()


@register.filter
def dict_get(value, member_name):
    """
    Returns the wanted member of a dict-like container, or an empty string
    if the member cannot be found.
    When you know the key in advance, you can access the associated value with
    DTL's regular dot-notation. `dict_get` allows you to access the value from
    a variable containing the key.
    You can also use it as a shortcut for `{{ mydict.member|default_if_none:'' }}`.

    e.g.:
        context = {'data': {'foo': '123', 'bar': '456'}}

        {% with member='bar' %}
            <span>{{ data|dict_get:member }}</span>
        {% endwith %}

        renders: <span>456</span>
    """
    return value.get(member_name, '')
