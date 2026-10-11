"""Keep authentication tests isolated from application data and deployment secrets."""

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

TEST_DATA = tempfile.mkdtemp(prefix='answerai-email-tests-')
atexit.register(shutil.rmtree, TEST_DATA, ignore_errors=True)
os.environ['DATA_DIR'] = TEST_DATA
os.environ['STATIC_DIR'] = str(Path(TEST_DATA) / 'static')
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DATA}/test.db'
os.environ['ENABLE_DB_MIGRATIONS'] = 'false'
os.environ['WEBUI_SECRET_KEY'] = 'test-only-application-secret-not-for-production'
os.environ['USE_SLIM_DOCKER'] = 'true'
os.environ['OFFLINE_MODE'] = 'true'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
