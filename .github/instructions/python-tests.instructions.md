# Python Tests

- Use `pytest` for unit and integration tests.
- Keep tests fast, deterministic, and isolated from the network by default.
- Add fixtures for reusable market data or broker payloads.
- When a test touches execution or risk, cover the fail-closed path too.

Example:

```bash
poetry run pytest -q
```
