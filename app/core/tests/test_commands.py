"""
Test custom Django management commands.
"""

# Mocking the database behavior with patch
from unittest.mock import patch

# OperationalError: one of the possible errors we may get from db
# when we try to connect to the db before it is ready.
from psycopg2 import OperationalError as Psycopg2Error

# call_command: helper function provided by Django
# to call a command by the name.
from django.core.management import call_command

# OperationalError: one of the possible errors we may get from
# depending on the stage of the startup process.
from django.db.utils import OperationalError

# SimpleTestCase: the base test class to create the unittest
# that does not need a db. As we are test a none available db,
# we don't need to perform migration. With patch, we simulate a db
from django.test import SimpleTestCase


# We moke (simulate) the database behavior with:
#  - @patch(path.to.the.command.to.execute)

# REM: 'check' is a method supplied by BaseCommand that allows
# to check the status of the database from wait_for_db.py
# It returns an exception.

# As we do it for each test method, we add the @patch() decorator
# on top of the test class
@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    """Test commands."""

    ##### - TEST 1 -
    # REM: because of @patch() that moke check, we need to add
    # an argument to each call that we make to our test methods.
    # Here the added argument is: patched_check
    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database if database ready."""

        # patched_check is the remplacement of the 'check' method
        # replaced by @patch(). We use it to customize the behavior.
        # Each time we call the 'check' command, we simulate
        # a response as True this signifies that the db is ready.
        patched_check.return_value = True

        # We call our custom command with call_command()
        # This executes the code insde: wait_for_db.py
        # This permits to check two things:
        # 1- the command is set and called correctly
        # 2- the database is ready. No exception has been called
        call_command('wait_for_db')

        # Verify if the 'check' method that is mocked has been
        # called w/ the DATABASES parameter in settings.py: default
        patched_check.assert_called_once_with(databases=['default'])

    ##### - TEST 2 -
    # The wait_for_db() command has to sleep between calls.
    # The command does: check db -> wait (sleep) -> check again ...

    # We don't want to slow out test by waiting. Then, we PATCH
    # using 'time.sleep' which is a MAGIC MOKE OBJECT.
    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for db when getting Operational Error."""

        # We moke the exceptions and the times they should be raised
        # side_effect permit to pass various items
        # that will be handled differently deppending on that type.
        # The moking library knows that will should raise exceptions
        # and, it knows the order and how many times.
        # - Postgres first raise twice: Psycopg2Error
        # - Django raise (after), three times: OperationalError
        # - finally, check() should return the sixth time: True
        patched_check.side_effect = (
                [Psycopg2Error] * 2 +
                [OperationalError] * 3 +
                [True]
        )

        # After the moking set up, we call the Django's command
        call_command('wait_for_db')

        # We expect the check() method being called six times.
        # - If called more than 6 times then it is unecessary
        # - If called less than 6 times then we are not testing
        # the exceptions properly
        self.assertEqual(patched_check.call_count, 6)

        # REM: differently to previous test. We do multiple calls.
        # WE DO NOT USE: assert_called_once_with()
        patched_check.assert_called_with(databases=['default'])
