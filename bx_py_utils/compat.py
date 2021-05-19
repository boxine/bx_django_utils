def removeprefix(self: str, prefix: str) -> str:
    """ Backport of removeprefix from PEP-616 (Python 3.9+) """

    if self.startswith(prefix):
        return self[len(prefix):]
    else:
        return self


def removesuffix(self: str, suffix: str) -> str:
    """ Backport of removesuffix from PEP-616 (Python 3.9+) """

    if self.endswith(suffix):
        return self[:-len(suffix)]
    else:
        return self
