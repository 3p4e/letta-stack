# Live container snapshot — letta stack on KVM4 (dockge, 2026-08-09)

Owner-provided during the consolidation session. This is the ground truth the sanitized
compose's drift notes refer to.

| Container | State | Ports | RAM |
|---|---|---|---|
| letta | running | 8283:8283 | 601.90 MB |
| letta-mcp-rust | running | 6507:6507 | 9.87 MB |
| letta-postgres | running | (internal) | 87.88 MB |
| qms-api | running | 8500:8500 | 37.79 MB |
| suma-api | running | 8501:8501 | 39.16 MB |

Notable: no letta-oss-ui / letta-daemon containers in the stack listing (both are in the
original suma-platform compose) — reconcile when recovering the authoritative compose
from /opt/stacks/ (open item #3).
