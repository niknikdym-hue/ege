# Eksamio Agent Orchestration v0.1

Minimal fail-closed development loop for the owner-approved architecture:

`GitHub truth -> Astra Senior Brain -> bounded Codex executor -> CI -> Astra review -> GitHub`.

This directory does **not** grant autonomous merge/deploy/payment/provider/production-data authority.

## Offline checks

```bash
python3 -m unittest discover -s agent-orchestration/tests -v
```

The test suite is network-free and requires only Python 3.10+ standard library.

## Astra

Live Astra calls use the Responses API, default model `gpt-6-astra`, and Structured Outputs. They are opt-in and require `OPENAI_API_KEY`. `OPENAI_ASTRA_MODEL` can override the model. Tests never make a live call.

## Codex

The v0.1 Python boundary passes a validated task contract to a trusted executor configured through `EKSAMIO_CODEX_COMMAND`; task JSON goes through stdin and `shell=True` is never used. Dry-run never executes the command.

The next bounded integration may replace that trusted-command boundary with the OpenAI Codex SDK without changing the task contract or owner gates.
