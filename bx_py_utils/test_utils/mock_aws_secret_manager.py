class SecretsManagerMock:
    """
    Mock for bx_py_utils.aws.secret_manager.SecretsManager
    """

    def __init__(self, **data):
        self.data = data

    def __call__(self, *args, **kwargs):
        return self

    def get_secret(self, secret_name, force_bytes=False):
        secret_data = self.data[secret_name]
        if force_bytes:
            secret_data = bytes(secret_data, encoding='UTF-8')
        return secret_data
