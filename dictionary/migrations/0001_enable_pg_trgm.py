from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Enable the pg_trgm extension that powers typo-tolerant search.

    Must run before any GIN index using gin_trgm_ops is created.
    """

    initial = True

    dependencies = []

    operations = [
        TrigramExtension(),
    ]
