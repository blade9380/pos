import sys
sys.path.insert(0, '/pos')

activate_this = '/home/blade/.local/share/virtualenvs/pos-YwRHZ6Qo/bin/activate_this.py'
with open(activate_this) as file:
    exec(file.read(), dict(__file__=activate_this)

from main import app as application