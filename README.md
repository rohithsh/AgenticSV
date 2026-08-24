# AgenticSV

## Scripts

| Script                               | Description                                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------------------|
| `agent/container.py`                 | Runs commands inside the Docker container that holds the verifier.                          |
| `agent/emitter.py`                   | Turns a spec JSON into a compilable harness: mocks, contracts, havocked entry states.       |
| `agent/verifier.py`                  | Invokes CBMC on a harness, and compiles/runs generated unit tests against the real program. |
| `agent/cex_parser.py`                | Extracts the counterexample, harness inputs and mock return values from CBMC's JSON output. |
| `agent/test_gen.py`                  | Creates a unit test that tests a counterexample's against the real callees.                 |
| `agent/runner.py`                    | Runner: emit harness, verify, parse counterexample, generate and run the validation test.   |
| `agent/specs/counter.json`           | Hand-written spec for the counterexample.                                                   |
| `agent/llm.py`                       | Provider-agnostic LLM call via LiteLLM; configured through `.env`.                          |
| `agent/spec_gen.py`                  | Reads the project sources and produces the harness spec JSON for a target function.         |

## Usage
Add your .env file with the following variables:
```
AGENT_MODEL=<model-tag>
AGENT_API_BASE=<api-endpoint>
OPENAI_API_KEY=<api-key>
```
### To Run:
```bash
git clone https://gitlab.com/cedricrupb/forge-example.git
docker build -t hagent .
docker run -d --name hagent-box -v "$PWD:/work" hagent sleep infinity
python agent/spec_gen.py
python agent/runner.py agent/specs/counter2_generated.json
```

