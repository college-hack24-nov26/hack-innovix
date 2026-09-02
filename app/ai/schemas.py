from dataclasses import dataclass, field
from typing import Any


@dataclass
class StructuredSummary:
    sections: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.sections)
