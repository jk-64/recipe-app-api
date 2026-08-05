"""
Django command to wait for the database to be available.
"""

# To make the execution sleep
import time

from django.core.management.base import BaseCommand

# Error thrown by django when the database is not ready.
from django.db.utils import OperationalError

# Error thrown by psycopg2 when the database is not ready
from psycopg2 import OperationalError as Psycopg2Error


class Command(BaseCommand):
    """Django command to wait for database."""

    # handle() is part of the standard syntax for any command.
    # This method is called when we run a Django command.
    def handle(self, *args, **options):
        """Entrypoint for command."""
        # 'stdout' is the standard output that we can use
        # to log things to the screen as our command is executed.
        self.stdout.write('Waiting for database...')

        # A boolean value to track to see if the db is available.
        db_up = False

        while not db_up:
            try:
                # If the database is not ready,
                # check() will throw an exception
                self.check(databases=['default'])
                db_up = True

            # Catch the exceptions if the db is not ready.
            # Depending on the stage of the db, it can be either
            # Psycopg2Error or OperationalError.
            except (Psycopg2Error, OperationalError):
                self.stdout.write(
                    'Database unavailable, waiting 1 second...'
                )
                # Sleep 1s before next connection attempt
                time.sleep(1)

        # The db is ready, db_up=True
        # The program is out of the while loop.
        self.stdout.write(self.style.SUCCESS('Database available !'))
