# AgenticSV

## Scripts

| Script                     | Description                                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------|
| `agent/container.py`       | Runs commands inside the Docker container that holds the verifier.                          |
| `agent/emitter.py`         | Turns a spec JSON into a compilable harness: mocks, contracts, havocked entry states.       |
| `agent/verifier.py`        | Invokes CBMC on a harness, and compiles/runs generated unit tests against the real program. |
| `agent/cex_parser.py`      | Extracts the counterexample, harness inputs and mock return values from CBMC's JSON output. |
| `agent/test_gen.py`        | Creates a unit test that tests a counterexample's against the real callees.                 |
| `agent/runner.py`          | Runner: emit harness, verify, parse counterexample, generate and run the validation test.   |
| `agent/specs/counter.json` | Hand-written spec for the counterexample.                                                   |

## Usage

```bash
docker build -t hagent .
docker run -d --name hagent-box -v "$PWD/forge-example:/work" hagent sleep infinity
python3 agent/runner.py agent/specs/counter.json
```