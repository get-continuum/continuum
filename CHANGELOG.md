# Changelog

All notable changes to this repository are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- CLI: `resolve`, `enforce`, and `list` commands (full MCP parity)
- CLI: `inspect --scope` for binding set queries
- CLI: `commit --options/--metadata/--activate/--stakeholder/--precedence/--override-policy/--supersedes` flags
- CLI: `supersede --new-title` for full replacement (matching MCP supersede)
- CLI: test suite (`oss/cli/tests/test_cli.py`)
- Demo: Docker Compose setup (`demo/docker-compose.yml`) for one-command startup
- Demo: `seed.py` script for seeding demo decisions
- CI: Tag-triggered PyPI publish workflows for SDK, CLI, and MCP server
- CI: `scripts/bump-version.sh` helper for release tagging
- SDK: `SQLiteMemorySource` concrete implementation of `MemorySignalSource`
- MCP: End-to-end test suite (`oss/mcp-server/tests/test_mcp_e2e.py`)
- LlamaIndex: Working example and unit tests
- Contracts: Schema v0.2 migration plan document

### Changed
- Makefile: Removed `core/` references (engine lives in separate `continuum-core` repo)
- CHANGELOG: Adopted Keep a Changelog format

## [v0.1.1]

### Changed
- SDK: Stabilized v0.1 convenience methods (`inspect`, `resolve`, `enforce`, `supersede`) and aligned scope/override behavior with the contracts spec.
- Docs: Updated install + quickstart to use `pip install continuum-sdk`.

### Added
- Examples: Root `examples/flagship-demo/flagship_demo.py` wrapper for the 5-minute demo run.

## [v0.1.0]

### Added
- Initial OSS draft release (contracts + deterministic SDK + stubs for MCP/integrations).
