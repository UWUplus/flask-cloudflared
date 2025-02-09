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
from tqdm.auto import tqdm

CLOUDFLARED_CONFIG = {
    ("Windows", "AMD64"): {
        "command": "cloudflared-windows-amd64.exe",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
    },
    ("Windows", "x86"): {
        "command": "cloudflared-windows-386.exe",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-386.exe",
    },
    ("Linux", "x86_64"): {
        "command": "cloudflared-linux-amd64",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
    },
    ("Linux", "i386"): {
        "command": "cloudflared-linux-386",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-386",
    },
    ("Linux", "arm"): {
        "command": "cloudflared-linux-arm",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm",
    },
    ("Linux", "arm64"): {
        "command": "cloudflared-linux-arm64",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64",
    },
    ("Linux", "aarch64"): {
        "command": "cloudflared-linux-arm64",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64",
    },
    ("Darwin", "x86_64"): {
        "command": "cloudflared",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz",
    },
    ("Darwin", "arm64"): {
        "command": "cloudflared",
        "url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz",
    },
}


def _get_command(system, machine):
    try:
        return CLOUDFLARED_CONFIG[(system, machine)]["command"]
    except KeyError:
        raise Exception(f"{machine} is not supported on {system}")


def _get_url(system, machine):
    try:
        return CLOUDFLARED_CONFIG[(system, machine)]["url"]
    except KeyError:
        raise Exception(f"{machine} is not supported on {system}")


# Needed for the darwin package
def _extract_tarball(tar_path, filename):
    tar = tarfile.open(tar_path + "/" + filename, "r")
    for item in tar:
        tar.extract(item, tar_path)
        if item.name.find(".tgz") != -1 or item.name.find(".tar") != -1:
            extract(item.name, "./" + item.name[: item.name.rfind("/")])


def extract(filename, path):
    tar = tarfile.open(filename, "r")
    for item in tar:
        tar.extract(item, path)
        if item.name.find(".tgz") != -1 or item.name.find(".tar") != -1:
            extract(item.name, "./" + item.name[: item.name.rfind("/")])


def _download_cloudflared(cloudflared_path, command):
    system, machine = platform.system(), platform.machine()
    if Path(cloudflared_path, command).exists():
        executable = (
            (cloudflared_path + "/" + "cloudflared")
            if (system == "Darwin" and machine in ["x86_64", "arm64"])
            else (cloudflared_path + "/" + command)
        )
        update_cloudflared = subprocess.Popen(
            [executable, "update"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
        return
    print(f" * Downloading cloudflared for {system} {machine}...")
    url = _get_url(system, machine)
    _download_file(url)


def _download_file(url):
    local_filename = url.split("/")[-1]
    r = requests.get(url, stream=True)
    r.raise_for_status()
    download_path = str(Path(tempfile.gettempdir(), local_filename))
    with open(download_path, "wb") as f:
        file_size = int(r.headers.get("content-length", 50000000))  # type: ignore
        chunk_size = 1024
        with tqdm(
            desc=" * Downloading",
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                pbar.update(chunk_size)
    return download_path


def _run_cloudflared(port, metrics_port, tunnel_id=None, config_path=None):
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

    cloudflared_command = [
        executable,
        "tunnel",
        "--metrics",
        f"127.0.0.1:{metrics_port}",
    ]
    if config_path:
        cloudflared_command += ["--config", config_path, "run"]
    elif tunnel_id:
        cloudflared_command += ["--url", f"http://127.0.0.1:{port}", "run", tunnel_id]
    else:
        cloudflared_command += ["--url", f"http://127.0.0.1:{port}"]

    if system == "Darwin" and machine == "arm64":
        cloudflared = subprocess.Popen(
            ["arch", "-x86_64"] + cloudflared_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    else:
        cloudflared = subprocess.Popen(
            cloudflared_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )

    atexit.register(cloudflared.terminate)
    localhost_url = f"http://127.0.0.1:{metrics_port}/metrics"

    for _ in range(10):
        try:
            metrics = requests.get(localhost_url).text
            if tunnel_id or config_path:
                # If tunnel_id or config_path is provided, we check for cloudflared_tunnel_ha_connections, as no tunnel URL is available in the metrics
                if re.search(r"cloudflared_tunnel_ha_connections\s\d", metrics):
                    # No tunnel URL is available in the metrics, so we return a generic text
                    tunnel_url = "preconfigured tunnel URL"
                    break
            else:
                # If neither tunnel_id nor config_path is provided, we check for the tunnel URL in the metrics
                tunnel_url = re.search(
                    r"(?P<url>https?:\/\/[^\s]+.trycloudflare.com)", metrics
                )
                if tunnel_url:
                    tunnel_url = tunnel_url.group("url")
                break
        except:
            time.sleep(3)
    else:
        raise Exception(f"! Can't connect to Cloudflare Edge")

    return tunnel_url


def start_cloudflared(port, metrics_port, tunnel_id=None, config_path=None):
    cloudflared_address = _run_cloudflared(port, metrics_port, tunnel_id, config_path)
    print(f" * Running on {cloudflared_address}")
    print(f" * Traffic stats available on http://127.0.0.1:{metrics_port}/metrics")


def run_with_cloudflared(app):
    old_run = app.run

    def new_run(*args, **kwargs):
        print(" * Starting Cloudflared tunnel...")
        port = kwargs.get("port", 5000)

        metrics_port = kwargs.pop("metrics_port", randint(8100, 9000))
        tunnel_id = kwargs.pop("tunnel_id", None)
        config_path = kwargs.pop("config_path", None)

        # Starting the Cloudflared tunnel in a separate thread.
        tunnel_args = (port, metrics_port, tunnel_id, config_path)
        thread = Timer(2, start_cloudflared, args=tunnel_args)
        thread.daemon = True
        thread.start()

        # Running the Flask app.
        old_run(*args, **kwargs)

    app.run = new_run
