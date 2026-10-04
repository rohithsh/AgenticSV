import json, os, re, sys, time
import subprocess

from llm import MODEL
from litellm import completion
from container import run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_BASE = os.environ.get('AGENT_API_BASE')

SYSTEM = r"""You are a verification agent in a Linux shell. The repository is
in /work; use paths relative to /work in commands.

Goal: verify a C function with CBMC, and find out whether a reported
violation is a real bug or a false alarm caused by a mock.

Each reply: one short thought, then ONE ```bash block with ONE command, then
STOP. Never write the command's output yourself; you will receive it.
Do not read files in agent/ — use `python3 agent/hv.py help` instead.

Start with: python3 agent/hv.py help
Then follow the NEXT line printed by each tool.

Never edit the project's source files. Only write files under
<project>/verification/.

When finished run: echo TASK_DONE <verdict> <one-line summary>
"""


def chat(messages):
    kw = {'api_base': API_BASE} if API_BASE else {}
    r = completion(model=MODEL, messages=messages, temperature=0.0, **kw)
    return r.choices[0].message.content

def snapshot(project):
    """Hash every project file outside verification/."""
    rc, out, _ = run(f"cd {project} && find . -path ./verification -prune -o -type f "
                     f"-print0 | sort -z | xargs -0 sha256sum")
    return out

def save_pristine(project):
    """Keep an untouched copy of the project (inside the container, outside /work)."""
    run(f'rm -rf /tmp/pristine && mkdir -p /tmp/pristine && '
        f'cd {project} && tar --exclude=./verification -cf - . | tar -xf - -C /tmp/pristine')


def restore_pristine(project):
    run(f'cd /tmp/pristine && tar -cf - . | tar -xf - -C /work/{project}')

def extract_command(text):
    m = re.search(r'```bash\s*\n(.*?)```', text, re.DOTALL)
    if not m:
        return None, text
    return m.group(1).strip(), text[:m.end()]


def agent(task, project, max_steps=100, log_path=None):
    messages = [{'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': task}]
    log, seen = [], {}
    produced = {'GAVE_UP'}

    save_pristine(project)
    base = snapshot(project)

    for step in range(max_steps):
        print(f'[{step}] waiting for model...', flush=True)
        reply = chat(messages)
        cmd, kept = extract_command(reply)
        messages.append({'role': 'assistant', 'content': kept})

        if cmd is None:
            print(f'[{step}] (no command) reply was:\n{reply[:500]}\n')
            obs = 'Error: your reply must contain one ```bash block. Try again.'
        else:
            rc, out, err = run(cmd, timeout=300)
            obs = f'exit code: {rc}\n{out}{err}'[-4000:]

            # rule: project files are read-only
            if snapshot(project) != base:
                restore_pristine(project)
                obs += ('\nREJECTED: this command changed project files outside '
                        'verification/. The change was undone. Only write files under '
                        f'{project}/verification/.')

            # rule: repeated commands
            seen[cmd] = seen.get(cmd, 0) + 1
            if seen[cmd] >= 3:
                obs += (f'\nNOTE: you have run this exact command {seen[cmd]} times. '
                        'Repeating it will not change the result. Try something different.')

            # record verdicts reported by tools
            if cmd.startswith('python3 agent/hv.py'):
                for v in ('REPRODUCED', 'VERIFIED_CLEAN', 'GUARDED'):
                    if f'"outcome": "{v}"' in out:
                        produced.add(v)

            # rule: verdicts must come from tools
            if cmd.startswith('echo TASK_DONE'):
                parts = cmd.split()
                verdict = parts[2] if len(parts) > 2 else ''
                if verdict in produced:
                    log.append({'step': step, 'cmd': cmd, 'obs': obs})
                    print(f'[{step}] DONE: {out.strip()}')
                    break
                obs = (f'REJECTED: verdict "{verdict}" was not reported by any tool. '
                       f'Allowed now: {sorted(produced)}. If you believe there is a real '
                       'bug, confirm it with `hv test` on the real program.')

        print(f'[{step}] $ {cmd}\n{obs[:300]}\n')
        log.append({'step': step, 'cmd': cmd, 'obs': obs})
        messages.append({'role': 'user', 'content': obs})

    if log_path:
        open(log_path, 'w').write(json.dumps(log, indent=2))
    return log


if __name__ == '__main__':

    project, target = sys.argv[1], sys.argv[2]
    base = snapshot(project)
    task = (f'Project directory: {project}\nTarget function: {target}\n'
            f'Verify the target and report the final verdict.')
    task = f'Project directory: {project}\nRun: echo "// x" >> {project}/src/counter.c'
    log_dir = os.path.join(ROOT, project, 'verification', target)
    os.makedirs(log_dir, exist_ok=True)
    import shutil, time
    vdir = os.path.join(ROOT, project, 'verification')
    if os.path.exists(vdir):
        archive = os.path.join(ROOT, 'runs', f'{project}-{time.strftime("%Y%m%d-%H%M%S")}')
        os.makedirs(os.path.dirname(archive), exist_ok=True)
        subprocess.run(['sudo', 'mv', vdir, archive])   # files may be owned by root
    agent(task, project, max_steps=100,log_path=os.path.join(log_dir, 'agent_log.json'))