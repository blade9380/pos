import sys
sys.path.insert(0, '/var/www/pos')

activate_this = '/var/www/pos/venv/bin/activate_this.py'
with open(activate_this) as file:
    exec(file.read(), dict(__file__=activate_this))

from main import app as application

