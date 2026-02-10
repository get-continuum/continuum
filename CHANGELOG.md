# Changelog

All notable changes to this repository are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [v0.2.0] — 2026-02-10

### Added
- **TypeScript SDK** (`oss/sdk-ts/`): `@get-continuum/sdk` with full type definitions and HTTP client matching Python SDK surface area
- **Capability registry** (`oss/capabilities/`): a-la-carte module system with `continuum.yaml` config loader and adapter interfaces (ModelAdapter, OrchestratorAdapter, MemorySignalSource)
- **Demo UI polish**: Decision Artifact panel (typed contract view with version, scope, options, rationale), color-coded enforcement verdicts, clickable inspector items
- **Hosted backend MVP**: `POST /commit_simple` endpoint, auth middleware with API key + workspace tenancy, SQLite DB schema (workspaces, api_keys, decisions tables)
- **SDK docs**: Python and TypeScript reference pages (`docs/sdks/`)
- **CI boundary check**: `scripts/check-boundary.sh` verifies oss/ never imports from continuum_engine
- **v2 repo streamline**: Froze v1 in both repos (branch + tag), pushed v2 monorepo to `get-continuum/continuum` main

### Changed
- Demo UI: Updated metadata, title, and header from boilerplate to branded Continuum
- Demo API: Bumped to v0.2.0, added auth + DB modules
- Docs navigation: Added SDKs section (Python + TypeScript)

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
