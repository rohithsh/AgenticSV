import json, os, sys
from container import run

# host path -> container path
HOST_ROOT = 'forge-example'
CONT_ROOT = '/work'


def run_test(test_host, spec, timeout=60):
    """Compile and run the unit test against the real program."""
    test = to_container(test_host)
    binary = '/tmp/cex_test'
    compile_cmd = (f'clang -std=c99 -g {spec["build_flags"]} '
                   f'{test} {spec["test_sources"]} -o {binary}')
    rc, out, err = run(compile_cmd, timeout=timeout)
    if rc != 0:
        return {'outcome': 'COMPILE_ERROR', 'rc': rc, 'stderr': err}

    rc, out, err = run(binary, timeout=timeout)
    if rc == 124:
        return {'outcome': 'TIMEOUT', 'rc': rc}
    if rc != 0:
        return {'outcome': 'REPRODUCED', 'rc': rc, 'stdout': out, 'stderr': err}
    if 'VERDICT: GUARDED' in out:
        return {'outcome': 'GUARDED', 'rc': rc, 'stdout': out}
    return {'outcome': 'NOT_REPRODUCED', 'rc': rc, 'stdout': out}

def to_container(host_path):
    """forge-example/verification/x.c  ->  verification/x.c (relative to /work)"""
    return os.path.relpath(host_path, HOST_ROOT)


def verify(harness_host, cex_host, build_flags, unwind=5, timeout=300):
    harness = to_container(harness_host)
    cex = to_container(cex_host)
    cmd = (f'cbmc {harness} {build_flags} '
           f'--unwind {unwind} --unwinding-assertions '
           f'--trace --json-ui > {cex}')
    rc, out, err = run(cmd, timeout=timeout)
    return {'rc': rc, 'cex_path': cex_host, 'stderr': err}


if __name__ == '__main__':
    spec = json.load(open(sys.argv[1]))
    r = verify(spec['out'],
               spec['out'].replace('harness.c', 'cex.json'),
               spec['build_flags'])
    print(json.dumps(r, indent=2))