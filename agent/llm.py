import os
import sys
from dotenv import load_dotenv

load_dotenv()

from litellm import completion

MODEL = os.environ.get('AGENT_MODEL', 'ollama/qwen2.5-coder')
API_BASE = os.environ.get('AGENT_API_BASE')

def ask(system, user, temperature=0.0):
    """Send one prompt to the configured model; return the text of the reply."""
    kwargs = {}
    if API_BASE:
        kwargs['api_base'] = API_BASE
    r = completion(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        temperature=temperature,
        **kwargs,
    )
    return r.choices[0].message.content


if __name__ == '__main__':
    print(f'model:    {MODEL}', file=sys.stderr)
    print(f'api_base: {API_BASE or "(provider default)"}', file=sys.stderr)
    print(ask('You are terse.', 'Reply with exactly the word: ok'))