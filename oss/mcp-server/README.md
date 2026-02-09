# Continuum MCP Server

MCP server exposing Continuum decision tools: inspect, resolve, enforce, commit, supersede.

## Install

```bash
pip install continuum-mcp-server
pip install "mcp>=1.0"
```

## Run

```bash
continuum-mcp serve
```

Point at a repo-local store:

```bash
CONTINUUM_STORE="/path/to/.continuum" continuum-mcp serve
```
