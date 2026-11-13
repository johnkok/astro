from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass(slots=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 11111
    discovery: bool = True


@dataclass(slots=True)
class CanConfig:
    interface: str = "virtual"
    channel: str = "servo42d"
    bitrate: int = 500_000
    ra_motor_id: int = 1
    dec_motor_id: int = 2


@dataclass(slots=True)
class MountConfig:
    ra_gear_ratio: float = 144.0
    dec_gear_ratio: float = 144.0
    microsteps: int = 16
    ra_positive_direction: str = "ccw"
    dec_positive_direction: str = "ccw"
    acceleration: int = 236
    max_axis_rate_deg_per_sec: float = 2.0
    goto_rate_deg_per_sec: float = 1.0
    initial_ra_hours: float = 0.0
    initial_dec_degrees: float = 0.0


@dataclass(slots=True)
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    can: CanConfig = field(default_factory=CanConfig)
    mount: MountConfig = field(default_factory=MountConfig)

    @classmethod
    def load(cls, path: str | Path | None) -> "AppConfig":
        if path is None:
            return cls()
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            server=ServerConfig(**raw.get("server", {})),
            can=CanConfig(**raw.get("can", {})),
            mount=MountConfig(**raw.get("mount", {})),
        )

    def validate(self) -> None:
        ids = (self.can.ra_motor_id, self.can.dec_motor_id)
        if any(not 0 <= value <= 0x7FF for value in ids) or ids[0] == ids[1]:
            raise ValueError("RA/DEC motor IDs must be distinct 11-bit CAN identifiers")
        if min(self.mount.ra_gear_ratio, self.mount.dec_gear_ratio, self.mount.microsteps) <= 0:
            raise ValueError("gear ratios and microsteps must be positive")
        if self.mount.ra_positive_direction not in {"cw", "ccw"} or self.mount.dec_positive_direction not in {"cw", "ccw"}:
            raise ValueError("axis directions must be 'cw' or 'ccw'")
        if not 0 <= self.mount.acceleration <= 255:
            raise ValueError("acceleration must be from 0 to 255")
