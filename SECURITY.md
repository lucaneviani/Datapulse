# Security Policy

## Supported Versions

Currently supported versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via:
- **Email**: Create a GitHub Security Advisory (preferred)
- **GitHub**: Use "Security" tab → "Report a vulnerability"

You should receive a response within 48 hours. If for some reason you do not, please follow up to ensure we received your original message.

Please include the following information:

- Type of issue (e.g., SQL injection, XSS, authentication bypass)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue

## Security Best Practices

When deploying DataPulse:

1. **Never commit `.env` files** - These contain sensitive credentials
2. **Use strong JWT secrets** - Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
3. **Set CORS_ORIGINS in production** - Don't use wildcard `*` in production
4. **Keep dependencies updated** - Run `pip install -U -r requirements.txt` regularly
5. **Use HTTPS in production** - Never use plain HTTP for production deployments
6. **Limit file upload sizes** - Default is 50MB, adjust as needed
7. **Review uploaded databases** - User-uploaded SQLite files are executed; ensure you trust the source
8. **Enable rate limiting** - Configure `RATE_LIMIT_REQUESTS` appropriately
9. **Monitor logs** - Enable structured JSON logging in production
10. **Use environment variables** - Never hardcode credentials

## Known Security Features

- SQL injection protection via query validation
- Table whitelist for demo database
- Dynamic SQL validation for custom databases
- Rate limiting on API endpoints
- JWT-based authentication
- Input sanitization (XSS prevention)
- File upload validation (type, size)
- Session management with TTL
- No comments allowed in SQL queries
- UNION queries blocked

## Security Updates

Security updates will be released as patch versions (e.g., 2.1.1, 2.1.2) and announced via:

- GitHub Security Advisories
- Release notes
- Repository README

Please update to the latest version regularly to receive security fixes.
