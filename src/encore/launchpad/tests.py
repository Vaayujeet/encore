"""Setup Test Case"""

from django.test import TestCase


# Create your tests here.
class SetupTestCase(TestCase):
    """Setup Test Case Class"""

    def test_setup(self):
        """Setup Test Case"""
        t = True
        self.assertTrue(t)
