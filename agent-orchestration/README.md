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

The repository also contains the owner-gated `openai-codex` SDK boundary. The first live integration proof used `openai/codex-action@v1` in a read-only sandbox, preserving the same task scope and owner gates.

## First live integration proof

GitHub Actions run `34503423279` completed the bounded chain `Astra plan -> Codex execution -> Astra review` with final decision `PASS`. Codex inspected only this README, changed no files, and the checkout-clean assertion passed. Sanitized durable evidence is stored in `evidence/astra-codex-joint-run-34503423279.json`.

The one-shot paid trigger was removed after the successful run. Ordinary CI remains network-free unless a new, explicitly owner-authorized, SHA-bound trigger is added.

Development orchestration runs from GitHub Actions directly against OpenAI. It has no Yandex dependency and sends no orchestration signal through Yandex.
