## deterministic_primary_key()

With this context manager can be used to enforce a deterministic primary key for a model
in deeper code paths.
It used the `post_init` signal to set a deterministic primary key,
before the model will be stored into the database.
e.g.:
    with deterministic_primary_key(MyModel1, MyModel2):
        MyModel.objects.create()
        baker.make(MyModel2)

Models with integer primary key will get 10000 + counter + 1
Looks like:
* `10001`
* `10002`

Models with UUID primary key will get a UUID with a
prefix based on the model name and a counter. Looks like:
* `UUID('bf264d42-0000-0000-0000-000000000001')`
* `UUID('bf264d42-0000-0000-0000-000000000002')`

There is the optional keyword argument `force_overwrite_pk`,
which forces overwrite a existing primary key.

`force_overwrite_pk` is enabled by default.