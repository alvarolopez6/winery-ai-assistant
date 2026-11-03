# Security policy

## Supported versions

Only the `main` branch is supported with security updates.

## Reporting a vulnerability

Do not open a public issue. Use GitHub Security Advisories on this repository
or contact the maintainer privately.

Please include:

- A description of the issue.
- Steps to reproduce.
- Affected files or workflows.
- Any suggested mitigation.

## Secrets

If you accidentally commit a secret:

1. Revoke it at the provider immediately.
2. Rotate every related credential.
3. Remove it from the repository and, if it was pushed, rewrite the history.
4. Check n8n execution data and backups for the same value.

The full production checklist is in [`docs/SECURITY.md`](docs/SECURITY.md).
