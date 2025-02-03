import subprocess

backend_cmd = "gunicorn -w 2 -b 0.0.0.0:6969 backend:app"
frontend_cmd = "gunicorn -w 2 -b 0.0.0.0:8080 frontend:app"

bkpro = subprocess.Popen(backend_cmd, shell=True)
frpro = subprocess.Popen(frontend_cmd, shell=True)

bkpro.wait()
frpro.wait()