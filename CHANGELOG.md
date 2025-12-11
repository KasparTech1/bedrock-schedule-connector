# Changelog

All notable changes to the KAI ERP Connector project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pre-commit hooks for code quality (ruff, mypy, bandit)
- GitHub Actions CI pipeline for automated testing
- CONTRIBUTING.md with development setup guide
- This CHANGELOG.md file

### Changed
- **BREAKING**: Connector `_build_join_sql()` methods now return `tuple[str, list]` for parameterized queries
- Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)` throughout codebase
- CORS configuration now uses explicit origins by default instead of wildcard

### Fixed
- **SECURITY**: Fixed SQL injection vulnerabilities in all connectors by implementing parameterized queries
- Fixed potential security issue with open CORS configuration

### Security
- Added bandit security scanner to CI pipeline
- Implemented parameterized queries for DuckDB staging layer

## [3.0.0] - 2024-12-01

### Added
- Three-layer architecture: Data Sources → Connectors → MCP/API
- Bedrock Ops Scheduler connector for production schedule visibility
- Customer Search connector
- Inventory Status connector
- Sales Order Tracker connector
- Order Availability connector with allocation logic
- MCP Server for AI agent integration
- FastAPI REST API for traditional applications
- DuckDB staging layer for client-side joins
- Parallel IDO fetching with asyncio
- Docker and Docker Compose configurations
- React frontend with shadcn/ui components
- Comprehensive documentation (BLUEPRINT.md)

### Changed
- Complete rewrite from v2.x architecture
- Migrated from direct SQL to REST API access
- New configuration system using Pydantic Settings

## [2.0.0] - 2024-09-01

### Added
- Initial SyteLine 10 CloudSuite integration
- Basic REST API client

## [1.0.0] - 2024-06-01

### Added
- Initial release with SyteLine 8 SQL connectivity
- Basic production schedule queries
