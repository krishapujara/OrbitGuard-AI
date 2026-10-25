"""Verify the Python environment, imports, and required directories."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_MODULES = [
    "streamlit",
    "numpy",
    "pandas",
    "scipy",
    "sgp4",
    "requests",
    "plotly",
    "sklearn",
    "joblib",
    "pytest",
    "pydantic",
    "dotenv",
]

REQUIRED_DIRS = [
    ROOT / "backend",
    ROOT / "frontend",
    ROOT / "ml",
    ROOT / "data" / "raw",
    ROOT / "data" / "processed",
    ROOT / "tests",
    ROOT / "docs",
]


def main() -> int:
    print(f"Python {sys.version}")
    print(f"Executable {sys.executable}")
    print(f"Project {ROOT}")
    failed = False
    for name in REQUIRED_MODULES:
        try:
            mod = importlib.import_module(name)
            version = getattr(mod, "__version__", "unknown")
            print(f"OK  {name} {version}")
        except Exception as exc:
            print(f"FAIL {name}: {exc}")
            failed = True
    for path in REQUIRED_DIRS:
        if path.exists():
            print(f"OK  dir {path.relative_to(ROOT)}")
        else:
            print(f"FAIL dir missing {path}")
            failed = True
    try:
        from backend.tle_parser import TLEValidationService
        from backend.orbital_propagation import OrbitalPropagationService
        from config.settings import get_settings

        get_settings()
        TLEValidationService()
        OrbitalPropagationService()
        print("OK  application imports")
    except Exception as exc:
        print(f"FAIL application imports: {exc}")
        failed = True
    if sys.version_info < (3, 11):
        print("FAIL Python 3.11+ required")
        failed = True
    elif sys.version_info[:2] not in {(3, 11), (3, 12)}:
        print(
            f"WARN specification asked for 3.11/3.12; running {sys.version_info.major}.{sys.version_info.minor}"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
