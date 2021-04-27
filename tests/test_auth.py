from pathlib import Path
from unittest import TestCase

from src.utility.auth.auth import Auth

path = Path(__file__).parent.parent


class TestAuth(TestCase):
    def test_get_key(self):
        auth = Auth(path)

        self.assertIsInstance(auth, Auth)

        self.assertTrue(
            expr=type(auth.get_key("ChatNoir")) is str,
            msg="auth does not provide a key for ChatNoir",
        )
