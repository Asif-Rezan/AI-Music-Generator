"""Initialize the instance-local database under a cross-process lock."""
import fcntl
import threading
from pathlib import Path
from django.conf import settings
from django.core.management import call_command

class TemporaryDatabaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.ready = False
        self.lock = threading.Lock()

    def __call__(self, request):
        if not self.ready:
            with self.lock:
                if not self.ready:
                    database = Path(settings.DATABASES['default']['NAME'])
                    database.parent.mkdir(parents=True, exist_ok=True)
                    with database.with_suffix('.lock').open('a') as lockfile:
                        fcntl.flock(lockfile, fcntl.LOCK_EX)
                        call_command('migrate', interactive=False, verbosity=0)
                    self.ready = True
        return self.get_response(request)
