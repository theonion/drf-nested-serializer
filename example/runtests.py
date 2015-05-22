import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = "example.settings"

import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings

TestRunner = get_runner(settings, None)

test_runner = TestRunner(verbosity=1, noinput=True)
failures = test_runner.run_tests(None)
if failures:
    sys.exit(bool(failures))
