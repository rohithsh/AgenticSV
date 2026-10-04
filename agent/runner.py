import json, os, sys

from contract_check import check
from refine import refine_contract
from emitter import emit_harness
from verifier import verify, run_test
from test_gen import emit_test
from cex_parser import parse, extract_inputs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def iter_dir(spec, n):
    """verification/counter/iter-003/, created if absent."""
    base = os.path.join(ROOT, os.path.dirname(spec['out']))
    d = os.path.join(base, f'iter-{n:03d}')
    os.makedirs(d, exist_ok=True)
    return d


def run_iteration(spec, n):
    """One pass: emit, verify, validate. Returns a verdict dict."""
    d = iter_dir(spec, n)
    rel = os.path.relpath(d, ROOT)

    harness_rel = os.path.join(rel, 'harness.c')
    cex_rel = os.path.join(rel, 'cex.json')
    test_rel = os.path.join(rel, 'test.c')

    open(os.path.join(ROOT, harness_rel), 'w').write(emit_harness(spec))

    v = verify(harness_rel, cex_rel, spec['build_flags'])
    if v['rc'] not in (0, 10):
        return {'iteration': n, 'outcome': 'VERIFIER_ERROR',
                'rc': v['rc'], 'stderr': v.get('stderr', '')[:2000]}

    report = parse(os.path.join(ROOT, cex_rel))
    if not report['failures']:
        return {'iteration': n, 'outcome': 'VERIFIED_CLEAN'}

    mocks = [m['name'] for m in spec['mocks']]
    cex = extract_inputs(report['failures'][0], mocks)

    open(os.path.join(ROOT, test_rel), 'w').write(emit_test(spec, cex))
    t = run_test(test_rel, spec)

    return {'iteration': n,
            'outcome': t['outcome'],
            'property': report['failures'][0]['property'],
            'description': report['failures'][0]['description'],
            'cex': cex,
            'contracts': {m['name']: m.get('post') for m in spec['mocks']},
            'test_stdout': t.get('stdout', '')}

def _loop(spec_path, max_iters=10, max_proposals=5):
    spec = json.load(open(spec_path))
    trace = []
    history = []          # accumulated spurious counterexamples
    last = None

    for n in range(max_iters):
        v = run_iteration(spec, n)
        d = iter_dir(spec, n)
        entry = {'iteration': n, 'outcome': v['outcome'],
                 'installed': spec['mocks'][0].get('post'), 'proposals': []}
        trace.append(entry)
        v['contract_history'] = trace
        open(os.path.join(d, 'verdict.json'), 'w').write(json.dumps(v, indent=2))
        print(f"iter {n}: {v['outcome']}")
        last = v

        if v['outcome'] in ('VERIFIED_CLEAN', 'REPRODUCED'):
            return v
        if v['outcome'] in ('VERIFIER_ERROR', 'TIMEOUT', 'COMPILE_ERROR'):
            print('  terminal outcome; not repairing')
            return v
        if v['outcome'] == 'GUARDED':
            print('  guarded: precondition strengthening not implemented')
            return v
        if v['outcome'] != 'NOT_REPRODUCED':
            print(f"  no rule for {v['outcome']}")
            return v

        history.append(v['cex'])
        m = spec['mocks'][0]          # TODO: multiple mocks
        accepted = None
        refuted_post = refuted_ev = None

        for _ in range(max_proposals):
            r = refine_contract(m['name'], m['src'], m.get('post'), history,
                                refuted_post, refuted_ev,
                                ret_type=m['ret_type'], params=m['params'])
            proposed = r['post']
            print(f"  propose: {proposed}  ({r.get('reasoning','')})")
            if proposed is None:
                break
            status, evidence = check(dict(m, post=proposed), spec, d)
            entry['proposals'].append({'post': proposed,
                                       'reasoning': r.get('reasoning', ''),
                                       'check': status,
                                       'evidence': evidence})
            print(f"  check:   {status}")
            if status == 'NOT_REFUTED':
                accepted = proposed
                break
            if status == 'ERROR':
                print(f'  {evidence}')
                break
            refuted_post, refuted_ev = proposed, evidence

        open(os.path.join(d, 'verdict.json'), 'w').write(json.dumps(v, indent=2))
        if accepted is None:
            print('  no acceptable contract; stopping')
            return last
        if accepted == m.get('post'):
            print('  contract unchanged; stopping')
            return last
        m['post'] = accepted
        m['status'] = 'not_refuted'

    print('iteration cap reached')
    return last

def loop(spec_path, **kw):
    spec = json.load(open(spec_path))
    v = _loop(spec_path, **kw)
    base = os.path.join(ROOT, os.path.dirname(spec['out']))
    open(os.path.join(base, 'history.json'), 'w').write(
        json.dumps(v.get('contract_history', []), indent=2))
    return v

def main(spec_path, n=0):
    spec = json.load(open(spec_path))
    verdict = run_iteration(spec, n)
    d = iter_dir(spec, n)
    open(os.path.join(d, 'verdict.json'), 'w').write(json.dumps(verdict, indent=2))
    print(json.dumps(verdict, indent=2))


if __name__ == '__main__':
    loop(sys.argv[1])