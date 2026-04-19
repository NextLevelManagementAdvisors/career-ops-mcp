from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class State:
    id: str
    label: str
    aliases: list[str]
    description: str
    dashboard_group: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "aliases": self.aliases,
            "description": self.description,
        }


class StatesIndex:
    def __init__(self, states: list[State]):
        self.states = states
        self._lookup: dict[str, str] = {}
        for s in states:
            self._lookup[s.id.lower()] = s.id
            self._lookup[s.label.lower()] = s.id
            for alias in s.aliases:
                self._lookup[alias.lower()] = s.id

    def normalize(self, raw: str) -> str | None:
        """Return canonical state id for raw status string, or None if unknown."""
        return self._lookup.get(raw.strip().lower())


def parse(path: Path) -> StatesIndex:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    states = [
        State(
            id=s["id"],
            label=s["label"],
            aliases=s.get("aliases", []),
            description=s.get("description", ""),
            dashboard_group=s.get("dashboard_group", s["id"]),
        )
        for s in data.get("states", [])
    ]
    return StatesIndex(states)
