# CDPF Polling Runbook
This module polls preconfigured JSON event endpoints; it is not yet a native Plane/Kiwi/Langfuse API adapter.
Set CDPF_ALLOWED_HOSTS to comma-separated trusted hostnames and a separate secret token environment variable for each source.
Source JSON must be a list or an object with a results array. Each event needs id,event_type,severity,observed_at.
Only HTTPS is accepted. Redirects are disabled. Deploy with network egress allowlisting to mitigate DNS rebinding.
Call poll_once(source, httpx.Client()) from a trusted worker, never from untrusted user-provided URLs.
Schedule externally (cron/Kubernetes CronJob). Polling cursor, pagination, retries, and incremental windows are not yet implemented.
Run pytest -q tests/test_cdpf_polling.py tests/test_cdpf.py tests/test_cdpf_persistence_api.py and the full suite.
Do not enable production polling until the source APIs' actual response schemas and authentication methods are mapped and verified.
