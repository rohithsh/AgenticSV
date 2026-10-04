import json, os, re
from llm import ask

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SYSTEM = """You refine the postcondition of a mocked C function inside a
verification harness.

The harness verifies a target function with its callees replaced by mocks. A
mock that is too permissive produces counterexamples that cannot occur in the
real program. Your job is to ensure those specific counterexamples are excluded.

The mock currently allows return values the real function never produces, so
the verifier reports false alarms. Previous iterations of the mock are also provided below. 

Output ONLY a JSON object:
{"post": "<C boolean expression>", "reasoning": "<one sentence>"}

Rules:
- Give the GENERAL condition that excludes every spurious counterexample listed
  below. Do not attempt to fully characterise the function. Do not add
  constraints that no listed counterexample requires.
- Never copy the function's logic into the rule.
- An over-tight postcondition hides real defects. When unsure, choose the weaker
  option.
- The expression may refer to the return value and the mock's own parameters
  by name. Do not use the names from the counterexamples. 
- Use only C operators and macros visible in the source.
- Never propose changes to assertions, properties, or the target function. Only
  the mock's postcondition.
- If no postcondition excludes the counterexamples without being false of the
  real function, return {"post": null, "reasoning": "..."}.
"""

USER = """Mock function: {name}

Actual implementation, for reference:
```c
{src}
```

Mock signature: {ret_type} {name}({params})

Current postcondition: {current}

Spurious counterexamples seen so far:
{history}
{extra}
Give the weakest postcondition excluding all of them using the variables from the mock signature and the return value 'r'."""

REFUTED = """
Your previous proposal `{post}` was REFUTED: the real function violates it at
these values, so it is too strong and would hide real behaviour.
Propose a WEAKER rule.
"""

TOO_NARROW = """
The rule currently installed, `{post}`, is true, but it was too narrow: with it
in place, the verifier immediately found a false alarm. Find a rule that
explains WHY all of these returns are impossible, so that it also covers cases
not yet seen.
"""


def strip_fences(s):
    s = re.sub(r'^```(?:json)?\s*', '', s.strip())
    return re.sub(r'\s*```$', '', s).strip()


def render_history(cex_history, mock_name):
    if not cex_history:
        return '(none)'
    lines = []
    for i, c in enumerate(cex_history, 1):
        ins = c.get('inputs', {})
        prefix = f'__cex_mockin_{mock_name}_'
        args = ', '.join(f'{k[len(prefix):]}={v}'
                         for k, v in ins.items() if k.startswith(prefix))
        ret = c.get('mock_returns', {}).get(f'return_value_{mock_name}', '?')
        lines.append(f'{i}. {mock_name}({args}) returned {ret}')
    return '\n'.join(lines)


def refine_contract(mock_name, mock_src_file, current_post, cex_history,
                    refuted_post=None, refuted_evidence=None,
                    ret_type='void', params='void'):
    src = open(os.path.join(ROOT, mock_src_file)).read()
    extra = ''
    if current_post and cex_history:
        extra += TOO_NARROW.format(post=current_post)
    if refuted_evidence:
        r_val = refuted_evidence.get('r')
        inputs = ', '.join(f'{k}={v}' for k, v in refuted_evidence.items() if k != 'r')
        extra += REFUTED.format(post=refuted_post, inputs=inputs, r=r_val)
    raw = ask(SYSTEM, USER.format(name=mock_name, src=src,
                                  ret_type=ret_type, params=params,
                                  current=current_post or 'none (unconstrained)',
                                  history=render_history(cex_history, mock_name),
                                  extra=extra))
    return json.loads(strip_fences(raw))