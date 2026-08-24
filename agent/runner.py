import json, os, sys
from emitter import emit_harness
from verifier import verify, run_test
from test_gen import emit_test
from cex_parser import parse, extract_inputs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(spec_path):
    spec = json.load(open(spec_path))
    hdir = os.path.join(ROOT, os.path.dirname(spec['out']))
    os.makedirs(hdir, exist_ok=True)

    harness = os.path.join(ROOT, spec['out'])
    open(harness, 'w').write(emit_harness(spec))

    cex_path = os.path.join(hdir, 'cex.json')
    v = verify(spec['out'], os.path.join(os.path.dirname(spec['out']), 'cex.json'),
               spec['build_flags'])
    print('verifier rc:', v['rc'])

    report = parse(cex_path)
    if not report['failures']:
        print('VERDICT: harness verified clean')
        return

    mocks = [m['name'] for m in spec['mocks']]
    cex = extract_inputs(report['failures'][0], mocks)
    print('CEX:', json.dumps(cex))

    test_rel = os.path.join(os.path.dirname(spec['out']), 'test.c')
    open(os.path.join(ROOT, test_rel), 'w').write(emit_test(spec, cex))

    t = run_test(test_rel, spec)
    print('TEST:', json.dumps(t, indent=2))


if __name__ == '__main__':
    main(sys.argv[1])