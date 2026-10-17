"""Single-process Windows WSGI server for the local SQL deployment."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SoftFactur.settings')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    from waitress import serve
    from SoftFactur.wsgi import application
    # One process keeps the existing in-memory session cache shared across requests.
    serve(application, host=args.host, port=args.port, threads=4, expose_tracebacks=False)
