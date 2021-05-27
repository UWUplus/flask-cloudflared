import atexit
import requests
import subprocess
import tempfile
import shutil
import os
import zipfile
import platform
import time
import re
from threading import Timer
from pathlib import Path

def _get_command():
    system = platform.system()
    if system == "Windows":
        print("cloudflared.exe")
        command = "cloudflared.exe"
    elif system == "Linux" or system == "Darwin":
        command = "cloudflared"
    else:
        raise Exception("{system} is not supported".format(system=system))
    return command

def _run_cloudflared(port):
    command = _get_command()
    cloudflared_path = str(Path(tempfile.gettempdir(), "cloudflared"))
    _download_cloudflared(cloudflared_path)
    executable = str(Path(cloudflared_path, command))
    os.chmod(executable, 0o777)
    cloudflared = subprocess.Popen([executable, 'tunnel', '--url', 'http://127.0.0.1:' + str(port), '--metrics', '127.0.0.1:8099'])
    atexit.register(cloudflared.terminate)
    localhost_url = "http://127.0.0.1:8099/metrics"
    attempts = 0
    while attempts < 10:
        try:
            tunnel_url = requests.get(localhost_url).text
            tunnel_url = (re.search("(?P<url>https?:\/\/[^\s]+.trycloudflare.com)", tunnel_url).group("url"))
            break
        except:
            attempts += 1
            time.sleep(3)
            continue
    return tunnel_url
    
def _download_cloudflared(cloudflared_path):
    if Path(cloudflared_path).exists():
        return
    system = platform.system()
    if system == "Darwin":
        url = "https://bin.equinox.io/c/VdrWdbjqyF/cloudflared-stable-darwin-amd64.zip"
    elif system == "Windows":
        url = "https://bin.equinox.io/c/VdrWdbjqyF/cloudflared-stable-windows-amd64.zip"
    elif system == "Linux":
        url = "https://bin.equinox.io/c/VdrWdbjqyF/cloudflared-stable-linux-amd64.zip"
    else:
        raise Exception(f"{system} is not supported")
    download_path = _download_file(url)
    with zipfile.ZipFile(download_path, "r") as zip_ref:
        zip_ref.extractall(cloudflared_path)

def _download_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    download_path = str(Path(tempfile.gettempdir(), local_filename))
    with open(download_path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return download_path

def start_cloudflared(port):
    cloudflared_address = _run_cloudflared(port)
    print(f" * Running on {cloudflared_address}")
    print(f" * Traffic stats available on http://127.0.0.1:8099/metrics")

def run_with_cloudflared(app):
    old_run = app.run

    def new_run(*args, **kwargs):
        port = kwargs.get('port', 5000)
        thread = Timer(2, start_cloudflared, args=(port,))
        thread.setDaemon(True)
        thread.start()
        old_run(*args, **kwargs)
    app.run = new_run
