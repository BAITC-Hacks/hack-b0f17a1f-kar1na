from pathlib import Path
import json
import os
import tempfile
import numpy as np

def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value

def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False, encoding='utf-8') as f:
        json.dump(clean_json(value), f, ensure_ascii=False, indent=2, allow_nan=False)
        tmp = f.name
    os.replace(tmp, path)
