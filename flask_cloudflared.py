import atexit
import requests
import subprocess
import tarfile
import tempfile
import shutil
import os
import platform
import time
import re
from random import randint
from threading import Timer
from pathlib import Path

CLOUDFLARED_CONFIG = {
    ('Windows', 'AMD64'): {
        'command': 'cloudflared-windows-amd64.exe',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
    },
    ('Windows', 'x86'): {
        'command': 'cloudflared-windows-386.exe',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-386.exe'
    },
    ('Linux', 'x86_64'): {
        'command': 'cloudflared-linux-amd64',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64'
    },
    ('Linux', 'i386'): {
        'command': 'cloudflared-linux-386',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-386'
    },
    ('Linux', 'arm'): {
        'command': 'cloudflared-linux-arm',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm'
    },
    ('Linux', 'arm64'): {
        'command': 'cloudflared-linux-arm64',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64'
    },
    ('Linux', 'aarch64'): {
        'command': 'cloudflared-linux-arm64',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64'
    },
    ('Darwin', 'x86_64'): {
        'command': 'cloudflared',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz'
    },
    ('Darwin', 'arm64'): {
        'command': 'cloudflared',
        'url': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz'
    }
}

def _get_command(system, machine):
    try:
        return CLOUDFLARED_CONFIG[(system, machine)]['command']
    except KeyError:
        raise Exception(f"{machine} is not supported on {system}")

def _get_url(system, machine):
    try:
        return CLOUDFLARED_CONFIG[(system, machine)]['url']
    except KeyError:
        raise Exception(f"{machine} is not supported on {system}")

# Needed for the darwin package
def _extract_tarball(tar_path, filename):
    tar = tarfile.open(tar_path+'/'+filename, 'r')
    for item in tar:
        tar.extract(item, tar_path)
        if item.name.find(".tgz") != -1 or item.name.find(".tar") != -1:
            extract(item.name, "./" + item.name[:item.name.rfind('/')])

def _download_cloudflared(cloudflared_path, command):
    system, machine = platform.system(), platform.machine()
    if Path(cloudflared_path, command).exists():
        executable = (cloudflared_path+'/'+'cloudflared') if (system == "Darwin" and machine in ["x86_64", "arm64"]) else (cloudflared_path+'/'+command)
        update_cloudflared = subprocess.Popen([executable, 'update'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return
    print(f" * Downloading cloudflared for {system} {machine}...")
    url = _get_url(system, machine)
    _download_file(url)

def _download_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    download_path = str(Path(tempfile.gettempdir(), local_filename))
    with open(download_path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return download_path

def _run_cloudflared(port, metrics_port):
    system, machine = platform.system(), platform.machine()
    command = _get_command(system, machine)
    cloudflared_path = str(Path(tempfile.gettempdir()))
    if system == "Darwin":
        _download_cloudflared(cloudflared_path, "cloudflared-darwin-amd64.tgz")
        _extract_tarball(cloudflared_path, "cloudflared-darwin-amd64.tgz")
    else:
        _download_cloudflared(cloudflared_path, command)

    executable = str(Path(cloudflared_path, command))
    os.chmod(executable, 0o777)

    if system == "Darwin" and machine == "arm64":
        cloudflared = subprocess.Popen(['arch', '-x86_64', executable, 'tunnel', '--url', f'http://127.0.0.1:{port}', '--metrics', f'127.0.0.1:{metrics_port}'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        cloudflared = subprocess.Popen([executable, 'tunnel', '--url', f'http://127.0.0.1:{port}', '--metrics', f'127.0.0.1:{metrics_port}'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    atexit.register(cloudflared.terminate)
    localhost_url = f"http://127.0.0.1:{metrics_port}/metrics"

    for _ in range(10):
        try:
            tunnel_url = requests.get(localhost_url).text
            tunnel_url = (re.search("(?P<url>https?:\/\/[^\s]+.trycloudflare.com)", tunnel_url).group("url"))
            break
        except:
            time.sleep(3)
    else:
        raise Exception(f"! Can't connect to Cloudflare Edge")

    return tunnel_url

def start_cloudflared(port, metrics_port):
    cloudflared_address = _run_cloudflared(port, metrics_port)
    print(f" * Running on {cloudflared_address}")
    print(f" * Traffic stats available on http://127.0.0.1:{metrics_port}/metrics")

def run_with_cloudflared(app):
    old_run = app.run

    def new_run(*args, **kwargs):
        # Webserver port is 5000 by default.
        port = kwargs.get('port', 5000)
        # If metrics_port is not specified, we will use a random port between 8100 and 9000.
        metrics_port = kwargs.get('metrics_port', randint(8100, 9000))
        # Removing the port and metrics_port from kwargs to avoid passing them to the Flask app.
        kwargs.pop('metrics_port', None)
        # Starting the Cloudflared tunnel in a separate thread.
        thread = Timer(2, start_cloudflared, args=(port, metrics_port,))
        thread.setDaemon(True)
        thread.start()
        # Running the Flask app.
        old_run(*args, **kwargs)
    app.run = new_run