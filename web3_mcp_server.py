"""Thin wrapper module so the package has a stable import path for CLI entrypoints.

We keep the main implementation in `mcp-server.py` (historical filename), and
re-export `main()` here so `pyproject.toml` can refer to `web3_mcp_server:main`.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_impl():
    impl_path = Path(__file__).with_name("mcp-server.py")
    spec = importlib.util.spec_from_file_location("mcp_server_impl", impl_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load implementation module from {impl_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = _load_impl()
    module.main()


__all__ = ["main"]

