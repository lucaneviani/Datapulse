# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows for tests and linting
- Pre-commit hooks configuration
- Code of Conduct
- Contributing guidelines
- Security policy
- Issue templates (bug report, feature request)
- Comprehensive test suite (188+ tests)

### Changed
- Improved CSV upload handling with better error messages
- Enhanced SQL generation fallback when AI is unavailable
- Updated README badges and documentation

### Fixed
- CSV upload bug with BytesIO import
- Query validation blocking legitimate SELECT queries on custom databases
- Case-insensitive file extension checking

## [2.1.0] - 2025-01-XX

### Added
- Custom database upload support (CSV, Excel, SQLite)
- Session-based database management
- Fallback SQL generator for when AI is unavailable
- Dynamic SQL validation for custom databases
- Comprehensive security features (SQL injection protection, rate limiting)
- Multi-language support (IT, EN, ES, FR, DE)
- Export functionality (CSV, JSON, Excel, PDF)
- Interactive dashboard generation
- Query caching for performance
- Structured logging with rotation

### Changed
- Migrated to Pydantic v2 settings management
- Improved error handling and user feedback
- Enhanced test coverage

### Security
- SQL validation with whitelist and blacklist
- JWT authentication with bcrypt password hashing
- CORS configuration
- Rate limiting on API endpoints
- Input sanitization

## [2.0.0] - 2024-12-XX

### Added
- Initial public release
- FastAPI backend architecture
- Streamlit frontend interface
- Google Gemini AI integration
- Basic authentication system
- Demo Superstore database

### Changed
- Complete rewrite from version 1.x
- Modern async architecture
- Modular design pattern

## [1.0.0] - 2024-XX-XX

### Added
- Initial prototype release
- Basic SQL query generation
- Simple web interface

---

[Unreleased]: https://github.com/YOUR_USERNAME/Datapulse/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/YOUR_USERNAME/Datapulse/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/YOUR_USERNAME/Datapulse/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/YOUR_USERNAME/Datapulse/releases/tag/v1.0.0
