"""Run DataPulse locally (backend + frontend)

Usage:
  python scripts/run_local.py

Features:
- Loads environment variables from .env (if present)
- Selects default ports (8000 backend, 8501 frontend) and auto-adjusts if in use
- Starts backend (uvicorn) and frontend (streamlit) subprocesses using the current Python
- Waits for backend health endpoint before opening the frontend in a browser
- Gracefully terminates child processes on Ctrl+C
"""

import os
import sys
import time
import socket
import subprocess
import signal
from pathlib import Path

# Try to import dotenv if available
try:
    from dotenv import dotenv_values
except Exception:
    def dotenv_values(path):
        vals = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    vals[k.strip()] = v.strip().strip('"\'"')
        except FileNotFoundError:
            pass
        return vals

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / '.env'

DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 8501

CHECK_HEALTH_PATH = '/api/health'


def is_port_free(port: int, host: str = '127.0.0.1') -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.5)
        s.bind((host, port))
        s.close()
        return True
    except Exception:
        return False


def find_free_port(start: int) -> int:
    port = start
    while port < start + 100:
        if is_port_free(port):
            return port
        port += 1
    raise RuntimeError(f"No free port found starting at {start}")


def load_env(env_file: Path):
    vals = {}
    if env_file.exists():
        vals = dotenv_values(str(env_file))
    # Merge into os.environ copy
    env = os.environ.copy()
    for k, v in vals.items():
        if v is not None:
            env[k] = v
    return env


def wait_for_health(url: str, timeout: int = 30) -> bool:
    # Use requests if available, otherwise use urllib
    try:
        import requests
    except Exception:
        requests = None

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests:
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    return True
            else:
                from urllib.request import urlopen
                with urlopen(url, timeout=2) as r:
                    if r.status == 200:
                        return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def start_process(cmd: list, env: dict, cwd: Path, name: str):
    print(f"Starting {name}: {' '.join(cmd)} (cwd={cwd})")
    return subprocess.Popen(cmd, env=env, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def stream_output(proc, name: str):
    # Non-blocking streaming of process output
    try:
        if proc.stdout:
            for line in proc.stdout:
                print(f"[{name}] {line.rstrip()}")
    except Exception:
        pass


def main():
    os.chdir(str(PROJECT_ROOT))
    env = load_env(ENV_FILE)

    backend_port = DEFAULT_BACKEND_PORT if is_port_free(DEFAULT_BACKEND_PORT) else find_free_port(DEFAULT_BACKEND_PORT)
    frontend_port = DEFAULT_FRONTEND_PORT if is_port_free(DEFAULT_FRONTEND_PORT) else find_free_port(DEFAULT_FRONTEND_PORT)

    # Ensure Streamlit points to the chosen backend
    env.setdefault('BACKEND_URL', f'http://127.0.0.1:{backend_port}')
    env.setdefault('ENVIRONMENT', env.get('ENVIRONMENT', 'development'))
    env.setdefault('DEBUG', env.get('DEBUG', 'true'))

    python_exe = sys.executable or 'python'

    backend_cmd = [python_exe, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', str(backend_port)]
    frontend_cmd = [python_exe, '-m', 'streamlit', 'run', 'frontend/app.py', '--server.port', str(frontend_port), '--server.address', '127.0.0.1']

    backend_proc = start_process(backend_cmd, env=env, cwd=PROJECT_ROOT, name='backend')
    time.sleep(1)

    # Wait for backend to be healthy before starting frontend
    health_url = f"http://127.0.0.1:{backend_port}{CHECK_HEALTH_PATH}"
    print(f"Waiting for backend health at {health_url}...")
    if not wait_for_health(health_url, timeout=30):
        print('Backend did not become healthy in time. Streaming backend logs for diagnostics:')
        stream_output(backend_proc, 'backend')
        backend_proc.terminate()
        sys.exit(1)

    frontend_proc = start_process(frontend_cmd, env=env, cwd=PROJECT_ROOT, name='frontend')

    print('\nDataPulse is running')
    print(f'  Frontend: http://127.0.0.1:{frontend_port}')
    print(f'  Backend:  http://127.0.0.1:{backend_port} (docs: /docs)')

    # Open browser to frontend
    try:
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{frontend_port}')
    except Exception:
        pass

    try:
        # Stream outputs in background
        while True:
            if backend_proc.poll() is not None:
                print('Backend process exited. Streaming output:')
                stream_output(backend_proc, 'backend')
                break
            if frontend_proc.poll() is not None:
                print('Frontend process exited. Streaming output:')
                stream_output(frontend_proc, 'frontend')
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('Stopping DataPulse...')
    finally:
        for p in (frontend_proc, backend_proc):
            try:
                if p and p.poll() is None:
                    p.terminate()
            except Exception:
                pass


if __name__ == '__main__':
    main()
