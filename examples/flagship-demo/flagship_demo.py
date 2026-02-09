#!/usr/bin/env python3
"""Flagship end-to-end demo for the Continuum decision framework.

This is a thin wrapper around the OSS demo in `oss/examples/flagship-demo/`,
but placed at `examples/` so the root README quickstart can run:

    pip install continuum-sdk
    python examples/flagship-demo/flagship_demo.py
"""

from __future__ import annotations

from pathlib import Path
import runpy


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    demo_path = repo_root / "oss" / "examples" / "flagship-demo" / "flagship_demo.py"
    runpy.run_path(str(demo_path), run_name="__main__")


if __name__ == "__main__":
    main()

