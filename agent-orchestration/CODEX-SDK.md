# Codex SDK integration boundary

Eksamio uses the official stable Python Codex SDK (`openai-codex`) for the programmatic executor path.

The adapter is `codex_sdk_executor.py`. It is intentionally optional at import time so ordinary pull-request CI remains network-free and does not need OpenAI credentials.

Before a non-dry-run SDK turn it fails closed unless all of these are true:

- the task contract is valid;
- every dangerous requested action has a matching owner grant;
- the local Git repository root is exactly the configured Eksamio checkout;
- checkout `HEAD` exactly equals the task `base_sha`;
- current branch exactly equals `target_branch`;
- `OPENAI_API_KEY` exists;
- `openai-codex` is installed.

The SDK thread is started with an exact `cwd` and `Sandbox.workspace_write`. The task prompt repeats the no-merge/no-deploy/no-production-action boundary. Returned turn metadata and token usage are converted to JSON-safe run evidence.

Installation for a controlled live environment follows the official OpenAI SDK documentation:

```bash
pip install openai-codex
```

No live SDK call is made by GitHub Actions in v0.1.
