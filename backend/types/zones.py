
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class ZoneType(Enum):
    NATIONAL = "national"        # France, England, etc.
    CONTINENTAL = "continental"  # UEFA, CAF, etc.
    INTERNATIONAL = "international"  # FIFA


@dataclass
class Zone:
    """Représente une zone géographique ou confédération"""
    code: str                    # FR, GB, UEFA, CAF, FIFA
    name: str                    # France, UEFA, FIFA
    zone_type: ZoneType
    flag: str                    # URL ou emoji
    full_name: Optional[str] = None  # Nom complet de la confédération

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "zone_type": self.zone_type.value,
            "flag": self.flag,
            "full_name": self.full_name
        }
