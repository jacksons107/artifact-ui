import json
from pathlib import Path

_EXAMPLES_DIR = Path(__file__).parent / "system_spec" / "examples"

EXAMPLES = {
    f.stem: json.loads(f.read_text())
    for f in sorted(_EXAMPLES_DIR.glob("*.json"))
}
