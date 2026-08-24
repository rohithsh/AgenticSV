import json, sys


def parse(path):
    """Read CBMC --json-ui output; return status and all failing properties."""
    msgs = json.load(open(path))
    status = next((m['cProverStatus'] for m in msgs if 'cProverStatus' in m), None)
    result = next((m['result'] for m in msgs if 'result' in m), [])

    failures = []
    for prop in result:
        if prop['status'] != 'FAILURE':
            continue
        values = {}
        for step in prop.get('trace', []):
            if step.get('stepType') != 'assignment':
                continue
            data = step.get('value', {}).get('data')
            if data is None:
                continue                 # struct-level assignment, no scalar
            values[step['lhs']] = data   # last write wins
        failures.append({
            'property': prop['property'],
            'description': prop['description'],
            'location': prop.get('sourceLocation', {}),
            'values': values,
        })
    return {'status': status, 'failures': failures}


def extract_inputs(failure, mocks):
    """The counterexample proper: harness inputs plus mock return values."""
    vals = failure['values']
    inputs = {k: v for k, v in vals.items() if k.startswith('__cex_')}
    returns = {}
    for m in mocks:
        prefix = f'return_value_{m}'
        for k, v in vals.items():
            if k == prefix or k.startswith(prefix + '$'):
                returns[k] = v
    return {'inputs': inputs, 'mock_returns': returns}


if __name__ == '__main__':
    path = sys.argv[1]
    mocks = sys.argv[2:]
    report = parse(path)
    print(f'status: {report["status"]}, failures: {len(report["failures"])}, '
          f'mocks: {mocks}', file=sys.stderr)
    for f in report['failures']:
        print(json.dumps({
            'property': f['property'],
            'description': f['description'],
            **extract_inputs(f, mocks),
        }, indent=2))