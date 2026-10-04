#!/usr/bin/env python3
"""Deterministic tools the agent calls inside the container."""
import argparse, json, os, sys
import re

from container import run
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emitter import emit_harness
from verifier import verify, run_test
from cex_parser import parse, extract_inputs
from test_gen import emit_test
from contract_check import check

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HELP = """Tools (python3 agent/hv.py ...):
  schema                        show the spec format
  run   SPEC DIR                build harness, run CBMC, replay any violation
  check SPEC MOCK "RULE" DIR    test a mock rule against the real callee
   test  SPEC DIR name=value ... run the REAL program with chosen inputs (globals and parameters)

NEXT: explore the project, then run `schema` and write a spec
to <project>/verification/<target>/spec.json with every "post" set to null."""

SCHEMA = """{
  "target": "<function>",
  "target_file": "<.c file defining it>",
  "target_ret_type": "<type or void>",
  "target_params": [{"name": "...", "type": "<scalar type>"}],
  "guard_value": "<constant returned by an early-exit guard, or null>",
  "build_flags": "<-I and -D flags from the Makefile; paths relative to the project>",
  "test_header": "<header declaring the target>",
  "test_sources": "<real .c files for the target and its callees>",
  "mocks": [{"name": "...", "ret_type": "...", "params": "<C params WITH names>",
             "src": "<.c file defining the real callee>", "post": null}],
  "havoc": [{"name": "<global or global.field>", "type": "<scalar type>"}]
}
Mock only callees defined in other project files, not the C library.

NEXT: write the spec, then run: run SPEC <project>/verification/<target>/iter-000"""

NEXT = {
    'VERIFIER_ERROR': 'NEXT: read the error above, fix the spec, and run again in the same DIR.',
    'VERIFIED_CLEAN': 'NEXT: finish with: echo TASK_DONE VERIFIED_CLEAN <summary>',
    'REPRODUCED':     'NEXT: real bug. Finish with: echo TASK_DONE REPRODUCED <summary>',
    'GUARDED':        'NEXT: finish with: echo TASK_DONE GUARDED <summary>',
    'NOT_REPRODUCED': ('NEXT: false alarm. The mock returned a value the real callee never '
                       'returns. Propose a SIMPLE general rule as a C expression'
                       ' without numbers from the counterexample, avoid literal numbers, use'
                       'named limits like SHRT_MIN '
                       'and macros like RANGE. Test it with `check`.'),
    'VACUOUS': ('NEXT: the mock rules rule out EVERY execution, so this result proves '
                'nothing. The rule is too strong or not valid C; weaken or fix it and check it.'),
}

def cmd_help(a):   print(HELP)
def cmd_schema(a): print(SCHEMA)
def cmd_test(a):
    """Run the REAL program with inputs chosen by the agent, e.g. some_value=-32768."""
    spec, d = load(a.spec, a.iterdir)
    params = {p['name'] for p in spec.get('target_params', [])}
    inputs = {}
    for kv in a.inputs:
        name, val = kv.split('=', 1)
        key = f'__cex_arg_{name}' if name in params else '__cex_' + name.replace('.', '_')
        inputs[key] = val
    test = os.path.join(d, 'test_manual.c')
    open(test, 'w').write(emit_test(spec, {'inputs': inputs, 'mock_returns': {}}))
    t = run_test(os.path.relpath(test, ROOT), spec)
    save(d, 'test_manual.json', {'inputs': a.inputs, 'outcome': t['outcome'],
                                 'stdout': t.get('stdout', '')[-1000:],
                                 'stderr': t.get('stderr', '')[-1000:]})
    print('NEXT: real bug confirmed. Finish with: echo TASK_DONE REPRODUCED <summary>'
          if t['outcome'] == 'REPRODUCED' else
          'NEXT: no failure with these inputs on the real program.')

def ledger_path(spec_path):
    return os.path.join(ROOT, os.path.dirname(spec_path), 'checked_rules.json')

def load_ledger(spec_path):
    p = ledger_path(spec_path)
    return json.load(open(p)) if os.path.exists(p) else {}

def cmd_run(a):
    spec_raw = json.load(open(os.path.join(ROOT, a.spec)))
    ledger = load_ledger(a.spec)
    for m in spec_raw['mocks']:
        if m.get('post') and m['post'] not in ledger.get(m['name'], []):
            print(f'REFUSED: the rule for {m["name"]} has not passed `check`.\n'
                  f'NEXT: run check on "{m["post"]}" first, or set "post" to null.')
            return

    # repeated rule sets
    rules = {m['name']: m.get('post') for m in spec_raw['mocks']}
    tried = ledger.get('_tried', [])
    for t in tried:
        if t['rules'] == rules:
            print(f'WARNING: these exact rules were already tried in {t["dir"]} '
                  f'with outcome {t["outcome"]}. Expect the same result.')

    cmd_emit(a)
    cmd_verify(a)
    spec, d = load(a.spec, a.iterdir)
    outcome = json.load(open(os.path.join(d, 'verify.json')))['outcome']
    if outcome == 'VIOLATION':
        cmd_replay(a)
        outcome = json.load(open(os.path.join(d, 'replay.json')))['outcome']
    if outcome == 'NOT_REPRODUCED':
        print(explain_mismatch(spec, d))

    ledger['_tried'] = tried + [{'dir': a.iterdir, 'rules': rules, 'outcome': outcome}]
    open(ledger_path(a.spec), 'w').write(json.dumps(ledger, indent=2))
    print(NEXT.get(outcome, f'NEXT: unexpected outcome {outcome}; finish with GAVE_UP.'))

def project_of(spec_path):
    """forge-example-modified/verification/add/spec.json -> forge-example-modified"""
    if '/verification/' not in spec_path:
        return ''                      # old-style spec: paths already relative to /work
    return spec_path.split('/verification/')[0]


def fix_path(p, project):
    if not project or not p or p.startswith(project + '/') or p.startswith('/'):
        return p
    return os.path.normpath(os.path.join(project, p))


def normalize(spec, project):
    s = dict(spec)
    s['target_file'] = fix_path(s['target_file'], project)
    s['test_sources'] = ' '.join(fix_path(p, project) for p in s['test_sources'].split())
    s['build_flags'] = re.sub(r'-I\s*(\S+)',
                              lambda m: '-I ' + fix_path(m.group(1), project),
                              s['build_flags'])
    hdr = fix_path(s['test_header'], project)
    if os.path.exists(os.path.join(ROOT, hdr)):
        s['test_header'] = os.path.join(ROOT, hdr)      # full path works in #include
    s['mocks'] = [dict(m, src=fix_path(m['src'], project)) for m in s['mocks']]
    return s


def load(spec_path, iterdir):
    spec = json.load(open(os.path.join(ROOT, spec_path)))
    spec = normalize(spec, project_of(spec_path))
    d = os.path.join(ROOT, iterdir)
    os.makedirs(d, exist_ok=True)
    return spec, d


def save(d, name, result):
    open(os.path.join(d, name), 'w').write(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

def real_return(spec, mock, args, d):
    """Run the REAL callee on concrete arguments; return its result as a string."""
    from contract_check import parse_params
    names = [n for _, n in parse_params(mock.get('params', 'void'))]
    call_args = ', '.join(args.get(n, '0') for n in names)
    src = os.path.join(d, f'real_{mock["name"]}.c')
    open(src, 'w').write(
        f'#include <limits.h>\n#include <stdio.h>\n'
        f'#include "{os.path.join(ROOT, mock["src"])}"\n'
        f'int main(void) {{ printf("%lld\\n", (long long){mock["name"]}({call_args})); return 0; }}\n')
    rc, out, err = run(f'clang -std=c99 -w {spec["build_flags"]} '
                       f'{os.path.relpath(src, ROOT)} -o /tmp/real_call && /tmp/real_call')
    return out.strip() if rc == 0 else None


def explain_mismatch(spec, d):
    """For each mock call in the counterexample: what the mock returned vs. the real function."""
    v = json.load(open(os.path.join(d, 'verify.json')))
    ins, rets = v['cex']['inputs'], v['cex']['mock_returns']
    lines = []
    for m in spec['mocks']:
        prefix = f'__cex_mockin_{m["name"]}_'
        args = {k[len(prefix):]: val for k, val in ins.items() if k.startswith(prefix)}
        mock_ret = rets.get(f'return_value_{m["name"]}')
        real = real_return(spec, m, args, d)
        argstr = ', '.join(f'{k}={val}' for k, val in args.items())
        lines.append(f'MISMATCH: {m["name"]}({argstr}): mock returned {mock_ret}, '
                     f'real function returns {real}')
    return '\n'.join(lines)


def cmd_emit(a):
    spec, d = load(a.spec, a.iterdir)
    s = dict(spec, target_src=os.path.relpath(os.path.join(ROOT, spec['target_file']), d))
    path = os.path.join(d, 'harness.c')
    open(path, 'w').write(emit_harness(s))
    print(f'harness written: {os.path.relpath(path, ROOT)}')


def cmd_verify(a):
    spec, d = load(a.spec, a.iterdir)
    harness = os.path.join(d, 'harness.c')
    cex = os.path.join(d, 'cex.json')
    v = verify(harness, cex, spec['build_flags'])
    if v['rc'] == 0:
        reach = os.path.join(d, 'reach.json')
        verify(harness, reach, spec['build_flags'] + ' -DHV_REACH')
        reachable = any(f['description'] == 'hv_reach' for f in parse(reach)['failures'])
        return save(d, 'verify.json',
                    {'outcome': 'VERIFIED_CLEAN' if reachable else 'VACUOUS'})
    if v['rc'] != 10:
        errors = ''
        try:
            msgs = json.load(open(cex))
            errors = '\n'.join(m['messageText'] for m in msgs
                               if m.get('messageType') == 'ERROR')
        except Exception:
            pass
        return save(d, 'verify.json', {'outcome': 'VERIFIER_ERROR', 'rc': v['rc'],
                                       'errors': errors[-1500:] or v['stderr'][-1500:]})
    f = parse(cex)['failures'][0]
    mocks = [m['name'] for m in spec['mocks']]
    save(d, 'verify.json', {'outcome': 'VIOLATION', 'property': f['property'],
                            'description': f['description'],
                            'cex': extract_inputs(f, mocks)})


def cmd_replay(a):
    spec, d = load(a.spec, a.iterdir)
    f = parse(os.path.join(d, 'cex.json'))['failures'][0]
    cex = extract_inputs(f, [m['name'] for m in spec['mocks']])
    test = os.path.join(d, 'test.c')
    open(test, 'w').write(emit_test(spec, cex))
    t = run_test(os.path.relpath(test, ROOT), spec)
    save(d, 'replay.json', {'outcome': t['outcome'],
                            'stdout': t.get('stdout', '')[-1000:],
                            'stderr': t.get('stderr', '')[-1000:]})


def cmd_check(a):
    spec, d = load(a.spec, a.iterdir)
    mock = next((m for m in spec['mocks'] if m['name'] == a.mock), None)
    if mock is None:
        print(f'ERROR: no mock named {a.mock} in the spec.'); return
    status, evidence = check(dict(mock, post=a.rule), spec, d)
    save(d, f'check_{a.mock}.json', {'rule': a.rule, 'outcome': status, 'evidence': evidence})
    if status == 'NOT_REFUTED':
        ledger = load_ledger(a.spec)
        ledger.setdefault(a.mock, []).append(a.rule)
        open(ledger_path(a.spec), 'w').write(json.dumps(ledger, indent=2))
        print('NEXT: put this exact rule in the spec as "post", then `run` with the next iter-00N DIR.')
    elif status == 'REFUTED':
        print('NEXT: the rule is FALSE for the real callee at the input above. '
              'Propose a WEAKER rule and check it.')
    else:
        print('NEXT: the rule could not be compiled. It must be a C boolean expression '
              'using `r` for the return value and the parameter names, e.g. "r >= 0".')


if __name__ == '__main__':
    p = argparse.ArgumentParser(prog='hv')
    sub = p.add_subparsers(required=True)


    for name, fn in [('help', cmd_help), ('schema', cmd_schema)]:
        sub.add_parser(name).set_defaults(fn=fn)

    for name, fn in [('emit', cmd_emit), ('verify', cmd_verify),
                     ('replay', cmd_replay), ('run', cmd_run)]:
        s = sub.add_parser(name)
        s.add_argument('spec')
        s.add_argument('iterdir')
        s.set_defaults(fn=fn)

    s = sub.add_parser('check')
    s.add_argument('spec')
    s.add_argument('mock')
    s.add_argument('rule')
    s.add_argument('iterdir')
    s.set_defaults(fn=cmd_check)
    s = sub.add_parser('test')
    s.add_argument('spec'); s.add_argument('iterdir'); s.add_argument('inputs', nargs='+')
    s.set_defaults(fn=cmd_test)

    a = p.parse_args()
    a.fn(a)