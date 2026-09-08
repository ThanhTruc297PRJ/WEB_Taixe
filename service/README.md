# driver_monitoring_support_system
System 

## Backend B04 - Security & Load Balancing

1. Copy `.env.example` to `.env` and fill Firebase/Anthropic settings.
2. Put `serviceAccountKey.json` in the service root (it is ignored by git).
3. Run `docker compose up --build`.
4. Access the API through Nginx at `http://localhost:8080`.

B04 currently includes:
- Restricted CORS origins/methods/headers.
- Application-level rate limiting (`RATE_LIMIT_DEFAULT`, default `60/minute`).
- Nginx gateway rate limiting (`20r/s`, burst 40).
- Optional IP whitelist (`IP_WHITELIST_ENABLED`, `IP_WHITELIST`).
- Structured request logging with `X-Request-ID`, client IP and duration.
- Nginx least-connections load balancing across two FastAPI containers.

When running behind Nginx, `TRUST_PROXY_HEADERS=true` lets the app read the original
client address from `X-Forwarded-For`. Do not enable this when FastAPI is directly
exposed to untrusted clients.
