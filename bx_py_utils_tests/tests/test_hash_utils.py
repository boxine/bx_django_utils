from django.test import SimpleTestCase

from bx_py_utils.hash_utils import url_safe_encode, url_safe_hash


class HastUtilsTestCase(SimpleTestCase):
    def test_url_safe_encode(self):
        assert url_safe_encode(b'\x00\x01\x02\xfd\xfe\xff') == '-._GHJ'

    def test_url_safe_hash(self):
        assert url_safe_hash('foobar') == (
            'J45l_w.05QsjdV32~D-2hj-w2Jn8qL2FSkd2.vLhHZkGr-BmVrRpH-1LVgDJmMw_'
        )
        assert url_safe_hash('foobar', max_size=16) == (
            'J45l_w.05QsjdV32'
        )

        with self.assertRaisesMessage(
            AssertionError, 'Hash digest too short for requested max size!'
        ):
            assert url_safe_hash('foobar', max_size=9999)
