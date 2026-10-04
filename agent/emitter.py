import json, os

HEADER = '''/* generated harness */
#include "{target_src}"

short __VERIFIER_nondet_short(void);
void __CPROVER_assume(_Bool);
'''

MOCK = '''
{ret_type} {name}({params}) {{
{record}    {ret_type} r = __VERIFIER_nondet_{ret_type}();
{assume}    return r;
}}
'''

MAIN = '''
int main(void) {{
{havoc}
{call}
#ifdef HV_REACH
    __CPROVER_assert(0, "hv_reach");
#endif
    return 0;
}}
'''


def emit_mock(m):
    from contract_check import parse_params
    record = ''.join(f'    {t} __cex_mockin_{m["name"]}_{n} = {n};\n'
                     for t, n in parse_params(m.get('params', 'void')))
    assume = f'    __CPROVER_assume({m["post"]});\n' if m.get('post') else ''
    return MOCK.format(ret_type=m['ret_type'], name=m['name'],
                       params=m.get('params', 'void'),
                       record=record, assume=assume)


def emit_harness(spec):
    parts = [HEADER.format(target_src=spec['target_src'])]

    for m in spec['mocks']:
        parts.append(emit_mock(m))

    havoc, names = [], []
    for g in spec['havoc']:
        var = f'__cex_{g["name"].replace(".", "_")}'
        havoc.append(f'    {g["type"]} {var} = __VERIFIER_nondet_{g["type"]}();')
        names.append((g['name'], var))
    for target, var in names:
        havoc.append(f'    {target} = {var};')

    args = []
    for p in spec.get('target_params', []):
        var = f'__cex_arg_{p["name"]}'
        havoc.append(f'    {p["type"]} {var} = __VERIFIER_nondet_{p["type"]}();')
        args.append(var)
    call = f'    {spec["target"]}({", ".join(args)});'
    parts.append(MAIN.format(havoc='\n'.join(havoc), call=call))
    return ''.join(parts)


if __name__ == '__main__':
    import sys
    spec = json.load(open(sys.argv[1]))
    out = emit_harness(spec)
    os.makedirs(os.path.dirname(spec['out']), exist_ok=True)
    open(spec['out'], 'w').write(out)
    print(out)