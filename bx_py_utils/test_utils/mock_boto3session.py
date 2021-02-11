import collections


class MockedBoto3Session:
    """
    Mock boto3.session.Session(), but only this parts:
     * session.client()
     * session.client().get_secret_value()
    """

    def __init__(self):
        self._secrets = collections.defaultdict(dict)

        self.client = self  # fake this call: session.client()

    def __call__(self, *args, **kwargs):
        return self

    ##########################################################################
    # methods to load mock data:

    def add_secret_string(self, **kwargs):
        assert kwargs
        for key, value in kwargs.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            self._secrets[key]['SecretString'] = value

    def add_secret_binary(self, **kwargs):
        assert kwargs
        for key, value in kwargs.items():
            assert isinstance(key, str)
            assert isinstance(value, bytes)
            self._secrets[key]['SecretBinary'] = value

    ##########################################################################
    # replicated API from boto3.session.Session()

    def get_secret_value(self, SecretId):
        try:
            secret_value_response = self._secrets[SecretId]
        except KeyError:
            raise KeyError(f'Mock value for secret {SecretId!r} missing!')

        return secret_value_response
