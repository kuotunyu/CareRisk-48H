"""Make the independent MVP source root importable for repository-root tests."""

from __future__ import annotations

import sys
from pathlib import Path

MVP_ROOT = Path(__file__).parents[1]
if str(MVP_ROOT) not in sys.path:
    sys.path.insert(0, str(MVP_ROOT))
