#!/home/wcuteing/public_html/hr.wcu.edu.az/venv/bin/python
import sys
import os

# Uygulama klasörünü sisteme tanıtıyoruz
sys.path.insert(0, "/home/wcuteing/public_html/hr.wcu.edu.az")

# Flask uygulamanı çağırıyoruz
from app import app as application
from wsgiref.handlers import CGIHandler

if __name__ == '__main__':
    CGIHandler().run(application)
