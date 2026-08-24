import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEST = '''/* generated unit test - do not edit by hand */
#include <stdio.h>
#include "{header}"

int main(void) {{
    int guarded = 0;
    for (int i = 0; i < {reps}; i++) {{
{reset}
{call}
    }}
    if (guarded == {reps}) {{
        printf("VERDICT: GUARDED\\n");
    }} else {{
        printf("VERDICT: CLEAN (guarded %d/{reps})\\n", guarded);
    }}
    return 0;
}}
'''


def emit_test(spec, cex, reps=1000):
    assigns = []
    for g in spec['havoc']:
        var = '__cex_' + g['name'].replace('.', '_')
        if var in cex['inputs']:
            assigns.append(f'        {g["name"]} = {cex["inputs"][var]};')

    ret = spec.get('target_ret_type', 'void')
    if ret == 'void':
        call = f'        {spec["target"]}();'
    else:
        guard = spec.get('guard_value')
        call = f'        {ret} s = {spec["target"]}();\n'
        if guard:
            call += f'        if (s == {guard}) guarded++;\n'
        call += '        (void)s;'

    return TEST.format(header=spec['test_header'],
                       reset='\n'.join(assigns),
                       call=call,
                       reps=reps)