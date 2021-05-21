import traceback

from django.db.models.signals import post_init


class CleanMock:
    """
    Track if full_clean() was called.
    """

    def __init__(self, instance):
        self.instance = instance  # the model instance that should be tracked

        # Replace the full_clean() function to track the call of it:
        self.origin_clean = instance.full_clean
        instance.full_clean = self.full_clean

        self.clean_called = False  # Was full_clean() called?

        # Helpful to find the code part that missed the full_clean() call:
        self.stack = traceback.extract_stack(f=None, limit=None)

    def full_clean(self, *args, **kwargs):
        self.clean_called = True
        return self.origin_clean(*args, **kwargs)

    def model_pkg_name(self):
        opts = self.instance._meta
        return f'{opts.app_label}.{opts.object_name}'

    def __repr__(self):
        return f'<CleanMock {self.model_pkg_name()}>'


class AssertModelCleanCalled:
    """
    Context manager for assert that full_clean() was called for every model instance.
    """

    def __init__(self):
        self.clean_mocks = []
        self.called_cleans = []
        self.missing_cleans = []

    def post_init_handler(self, signal, sender, instance, **kwargs):
        self.clean_mocks.append(CleanMock(instance))

    def __enter__(self):
        post_init.connect(self.post_init_handler)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        post_init.disconnect(self.post_init_handler)
        for clean_mock in self.clean_mocks:
            if clean_mock.clean_called:
                self.called_cleans.append(clean_mock)
            else:
                self.missing_cleans.append(clean_mock)

    def assert_no_missing_cleans(self):
        """
        Assert that there are no missing full_clean() calls.
        Give a very verbose error message with a stack trace
        so it should be easy to find the related code part.
        """
        if not self.missing_cleans:
            # There are no missing full_clean() calls -> everything is okay
            return

        msg = [
            f'There are {len(self.missing_cleans)} missing clean calls:'
        ]
        seen_stacks = []
        for missing_clean in self.missing_cleans:

            stack_info = ''.join(traceback.format_list(missing_clean.stack))
            if stack_info in seen_stacks:
                # Skip same stack traces
                continue
            seen_stacks.append(stack_info)

            msg.append(
                f'{missing_clean.model_pkg_name()}: {stack_info}'
            )

        raise AssertionError('\n'.join(msg))
