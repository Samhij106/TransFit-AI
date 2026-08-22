# Security policy

## Supported version

The latest commit on `main` is the supported version of this research and
portfolio project.

## Reporting a vulnerability

Please do not publish credentials, personal data, or reproducible exploit
details in a public issue. Use GitHub's private vulnerability reporting for
this repository when it is available. Otherwise, open a minimal issue asking
the maintainer for a private reporting channel without including the sensitive
details.

## Data and secrets

- The public application has no user accounts, payments, or private user data.
- API credentials must be supplied through environment variables and must not
  be committed. Copy `.env.example` to `.env` for local data refreshes.
- Render receives configuration through `render.yaml`; secret values should be
  configured in the Render dashboard rather than written into the repository.
- Transfer recommendations are research outputs, not financial, contractual,
  medical, or legal advice.
