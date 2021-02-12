import boto3


class SecretsManager:
    """
    Access AWS Secrets Manager values
    """

    def __init__(self, *, region_name):
        session = boto3.session.Session()
        self.client = session.client(
            service_name='secretsmanager',
            region_name=region_name,
        )

    def get_secret(self, secret_name, force_bytes=False, force_str=False, encoding='UTF-8'):
        response = self.client.get_secret_value(SecretId=secret_name)

        if 'SecretString' in response:
            secret_data = response['SecretString']

            if force_bytes and isinstance(secret_data, str):
                secret_data = bytes(secret_data, encoding=encoding)

        elif 'SecretBinary' in response:
            secret_data = response['SecretBinary']

            if force_str and isinstance(secret_data, bytes):
                secret_data = str(secret_data, encoding=encoding)

        else:
            raise NotImplementedError

        return secret_data
