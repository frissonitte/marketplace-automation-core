import json
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
EXAMPLE_TARGETS_PATH = BASE_DIR / "automation_targets.example.json"


@lru_cache(maxsize=1)
def _load_targets() -> dict:
    target_path = EXAMPLE_TARGETS_PATH
    if not target_path.exists():
        raise FileNotFoundError(
            "Target profile file not found. Expected automation_targets.example.json."
        )

    with target_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_target_profile(profile_key: str) -> dict:
    data = _load_targets()
    targets = data.get("targets", {})
    if profile_key not in targets:
        raise KeyError(f"Unknown target profile: {profile_key}")
    return targets[profile_key]
