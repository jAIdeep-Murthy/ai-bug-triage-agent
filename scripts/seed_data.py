"""
DEPRECATED as of Upgrade 2.
Synthetic data has been replaced with real Eclipse JDT bug reports.
Use scripts/load_real_data.py instead.

This file is kept only so existing imports and workflows that expect
`scripts/seed_data.py` continue to work without modification.
"""

from __future__ import annotations

from scripts.generate_synthetic_data import generate

__all__ = ["generate"]


if __name__ == "__main__":
    generate()

