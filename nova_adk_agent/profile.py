import json
from dataclasses import dataclass
from pathlib import Path

PROFILE_PATH = Path("user_profile.json")


@dataclass
class UserProfile:
    name: str
    role: str
    interests: list[str]
    wants_from_episodes: str


def load_profile() -> dict:
    """Load the user profile from disk. Returns {} if no profile exists yet."""
    if not PROFILE_PATH.exists():
        return {}
    try:
        return json.loads(PROFILE_PATH.read_text())
    except Exception:
        return {}


def save_profile(name: str, role: str, interests: str, wants_from_episodes: str) -> dict:
    """Save the user profile to disk.

    interests is a comma-separated string and is stored as a list.
    Returns the saved profile dict.
    """
    profile = {
        "name": name,
        "role": role,
        "interests": [i.strip() for i in interests.split(",") if i.strip()],
        "wants_from_episodes": wants_from_episodes,
    }
    PROFILE_PATH.write_text(json.dumps(profile, indent=2))
    return profile
