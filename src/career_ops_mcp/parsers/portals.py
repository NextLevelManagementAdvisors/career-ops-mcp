from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Portal:
    name: str
    careers_url: str
    api: str | None
    scan_method: str | None
    enabled: bool
    notes: str | None

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "careers_url": self.careers_url,
            "enabled": self.enabled,
        }
        if self.api:
            d["api"] = self.api
        if self.notes:
            d["notes"] = self.notes
        if self.scan_method:
            d["scan_method"] = self.scan_method
        return d


def parse(path: Path) -> list[Portal]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    companies = data.get("tracked_companies", [])
    portals = []
    for c in companies:
        portals.append(
            Portal(
                name=c.get("name", ""),
                careers_url=c.get("careers_url", ""),
                api=c.get("api"),
                scan_method=c.get("scan_method"),
                enabled=c.get("enabled", True),
                notes=c.get("notes"),
            )
        )
    return portals
