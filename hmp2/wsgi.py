from __future__ import unicode_literals

import os

## Seems like we were having problems with local_settings importing before we added
## the following lines.
##
## Credit - http://stackoverflow.com/a/7367787
root_path = os.path.abspath(os.path.split(__file__)[0])
sys.path.insert(0, os.path.join(root_path, 'hmp2'))
sys.path.insert(0, root_path)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
settings_module = "%s.settings" % PROJECT_ROOT.split(os.sep)[-1]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
