import sys
import os

# Proje dizinini yola ekle
sys.path.insert(0, os.path.dirname(__file__))

# Senin projenin ana nesnesi app.py içindeki 'app'
from app import app as application