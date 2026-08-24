import json, os, re, sys
from llm import ask

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


STATIC = {
    'target_src': '../../src/counter.c',
    'out': 'forge-example/verification/counter/harness.c',
    'build_flags': '-I includes -I src/common -DRANGE=10',
    'test_header': 'counter.h',
    'test_sources': 'src/counter.c src/random/rng.c',
}

SYSTEM = """You analyse C code to plan a verification harness for one function.
You output ONLY a JSON object. No prose, no markdown fences, no explanation.

The harness verifies the target function in isolation. Callees are replaced by
mocks that return unconstrained values. Global state the function reads is set
to unconstrained values before the call.

Schema:
{
  "target": "<function name>",
  "target_ret_type": "<return type, or void>",
  "guard_value": "<constant the function returns on an early-exit guard, or null>",
  "mocks": [{"name": "<callee>", "ret_type": "<type>", "params": "<C params or void>", "post": null}],
  "havoc": [{"name": "<global variable or field>", "type": "<C scalar type>"}]
}

Rules:
- "mocks" lists only functions the target calls directly that are defined
  outside the target's own source file. Do not mock standard library functions.
- "havoc" lists global variables the target reads or writes, field by field for
  structs, using the exact C expression to assign to (e.g. "g.field").
- "post" is always null at this stage.
- "guard_value" is the constant returned by an early guard that skips the
  function's main body, if one exists.
"""

USER = """Target function: {target}

Source file containing the target:
```c
{target_src}
```

Other project sources:
```c
{other_src}
```

Output the JSON object."""


def strip_fences(s):
    s = s.strip()
    s = re.sub(r'^```(?:json)?\s*', '', s)
    s = re.sub(r'\s*```$', '', s)
    return s.strip()


def generate(target, target_file, other_files):
    target_src = open(os.path.join(ROOT, target_file)).read()
    other_src = '\n\n'.join(
        f'/* {f} */\n' + open(os.path.join(ROOT, f)).read() for f in other_files)
    raw = ask(SYSTEM, USER.format(target=target, target_src=target_src,
                                  other_src=other_src))
    return json.loads(strip_fences(raw))


if __name__ == '__main__':
    TARGET = 'addRandom'
    TARGET_FILE = 'forge-example/src/counter.c'
    OTHER_FILES = [
        'forge-example/src/random/rng.c',
        'forge-example/includes/counter.h',
        'forge-example/includes/rng.h',
    ]

    spec = generate(TARGET, TARGET_FILE, OTHER_FILES)
    spec.update(STATIC)
    out_path = os.path.join(ROOT, 'agent/specs/counter_generated.json')
    open(out_path, 'w').write(json.dumps(spec, indent=2))
    print(json.dumps(spec, indent=2))