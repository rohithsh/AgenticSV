import subprocess

CONTAINER = 'hagent-box'
WORKDIR = '/work'


def run(cmd, timeout=300):
    """Run a command inside the container."""
    full = ['sudo', 'docker', 'exec', '-w', WORKDIR, CONTAINER, 'bash', '-c', cmd]
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, '', f'timeout after {timeout}s'


if __name__ == '__main__':
    rc, out, err = run('cbmc --version')
    print('rc:', rc)
    print('out:', out.strip())
    print('err:', err.strip())