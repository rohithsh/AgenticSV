import os
import subprocess

CONTAINER = 'hagent-box'
WORKDIR = '/work'
INSIDE = os.path.exists('/.dockerenv')

def ensure_running():
    """Start the container if it exists but is stopped."""
    p = subprocess.run(['sudo', 'docker', 'inspect', '-f', '{{.State.Running}}', CONTAINER],
                       capture_output=True, text=True)
    if p.stdout.strip() != 'true':
        subprocess.run(['sudo', 'docker', 'start', CONTAINER],
                       capture_output=True, text=True)

def run(cmd, timeout=300):
    if INSIDE:
        full = ['bash', '-c', cmd]
        cwd = WORKDIR
    else:
        ensure_running()
        full = ['sudo', 'docker', 'exec', '-w', WORKDIR, CONTAINER, 'bash', '-c', cmd]
        cwd = None
    try:
        p = subprocess.run(full, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, '', f'timeout after {timeout}s'


if __name__ == '__main__':
    rc, out, err = run('cbmc --version')
    print('rc:', rc)
    print('out:', out.strip())
    print('err:', err.strip())