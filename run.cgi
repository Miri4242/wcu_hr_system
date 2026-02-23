#!/home/wcuteing/public_html/hr.wcu.edu.az/.venv/bin/python
import sys
import os

# Add application directory to system path
sys.path.insert(0, "/home/wcuteing/public_html/hr.wcu.edu.az")

# Set environment variable for .env file
os.environ['FLASK_ENV'] = 'production'

# Import Flask application
from app import app as application
from wsgiref.handlers import CGIHandler

# Enable error logging
import logging
logging.basicConfig(
    filename='/home/wcuteing/public_html/hr.wcu.edu.az/cgi_errors.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    try:
        CGIHandler().run(application)
    except Exception as e:
        logging.error(f"CGI Handler Error: {e}", exc_info=True)
        print("Content-Type: text/html\n")
        print(f"<h1>Error</h1><pre>{e}</pre>")
