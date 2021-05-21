from unittest import TestCase
from unittest.mock import mock_open, patch

from bx_django_utils.environ import cgroup_memory_usage


class DockerTestCase(TestCase):
    def test_cgroup_memory_usage(self):
        expectations = {
            'B': 524288000,
            'KB': 524288000 / 1024,
            'MB': 524288000 / 1024 ** 2,
            'GB': 524288000 / 1024 ** 3,
            'TB': 524288000 / 1024 ** 4,
        }

        for unit, value in expectations.items():
            with patch('bx_django_utils.environ.open', mock_open(read_data='524288000')) as m:
                usage = cgroup_memory_usage(unit=unit)
            m.assert_called_once_with('/sys/fs/cgroup/memory/memory.usage_in_bytes', 'r')
            assert usage == value
