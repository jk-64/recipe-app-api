"""
Sample tests
"""

# We use SimpleTestCase because
# we don't need database intégration for this test demo
from django.test import SimpleTestCase

from app import calc


class CalcTests(SimpleTestCase):
    """Test the calc module."""

    def test_add_numbers(self):
        """Test adding numbers together."""
        res = calc.add(5, 6)

        self.assertEqual(res, 11)

        # For sanity, create failing test
        # self.assertEqual(res, 12)

    def test_subtract_numbers(self):
        """Test subtracting numbers"""
        res = calc.subtract(10, 15)

        self.assertEqual(res, 5)

