from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Protocol

import can


CMD_READ_ENCODER_CARRY = 0x30
CMD_RUN_SPEED = 0xF6
CMD_RUN_RELATIVE_AXIS = 0xF4
CMD_EMERGENCY_STOP = 0xF7
ENCODER_COUNTS_PER_REV = 16_384


def checksum(can_id: int, payload: bytes) -> int:
    """MKS checksum: low byte of CAN ID plus all payload bytes."""
    return (can_id + sum(payload)) & 0xFF


def command_frame(can_id: int, command: int, data: bytes = b"") -> can.Message:
    body = bytes([command]) + data
    return can.Message(
        arbitration_id=can_id,
        is_extended_id=False,
        data=body + bytes([checksum(can_id, body)]),
    )


class MotorIO(Protocol):
    def start_speed(self, ccw: bool, speed_parameter: int, acceleration: int) -> None: ...
    def stop(self, acceleration: int) -> None: ...
    def emergency_stop(self) -> None: ...
    def read_encoder(self) -> int: ...
    def move_relative(self, encoder_counts: int, speed_parameter: int, acceleration: int) -> None: ...
    def close(self) -> None: ...


class Servo42dCan:
    """Thread-safe subset of the official Servo42D/57D CAN protocol."""

    def __init__(self, bus: can.BusABC, motor_id: int, timeout: float = 0.4, bus_lock: threading.Lock | None = None):
        self.bus, self.motor_id, self.timeout = bus, motor_id, timeout
        self._lock = bus_lock or threading.Lock()

    def _send(self, command: int, data: bytes = b"", response_len: int | None = None) -> bytes:
        with self._lock:
            self.bus.send(command_frame(self.motor_id, command, data), timeout=self.timeout)
            if response_len is None:
                return b""
            deadline = time.monotonic() + self.timeout
            while time.monotonic() < deadline:
                message = self.bus.recv(max(0.0, deadline - time.monotonic()))
                if message is None or message.arbitration_id != self.motor_id:
                    continue
                reply = bytes(message.data)
                if len(reply) == response_len and reply[0] == command:
                    if checksum(self.motor_id, reply[:-1]) != reply[-1]:
                        raise IOError("Servo42D response checksum mismatch")
                    return reply
            raise TimeoutError(f"No Servo42D response to command 0x{command:02X}")

    def start_speed(self, ccw: bool, speed_parameter: int, acceleration: int) -> None:
        if not 0 <= speed_parameter <= 3000 or not 0 <= acceleration <= 255:
            raise ValueError("speed must be 0..3000 and acceleration 0..255")
        direction_and_high = (0x00 if ccw else 0x80) | ((speed_parameter >> 8) & 0x0F)
        self._send(CMD_RUN_SPEED, bytes([direction_and_high, speed_parameter & 0xFF, acceleration]))

    def stop(self, acceleration: int) -> None:
        self.start_speed(True, 0, acceleration)

    def emergency_stop(self) -> None:
        self._send(CMD_EMERGENCY_STOP)

    def read_encoder(self) -> int:
        reply = self._send(CMD_READ_ENCODER_CARRY, response_len=8)
        carry = int.from_bytes(reply[1:5], "big", signed=True)
        within_turn = int.from_bytes(reply[5:7], "big", signed=False)
        return carry * ENCODER_COUNTS_PER_REV + within_turn

    def move_relative(self, encoder_counts: int, speed_parameter: int, acceleration: int) -> None:
        if not -0x800000 <= encoder_counts <= 0x7FFFFF:
            raise ValueError("relative encoder move exceeds signed 24-bit range")
        if not 0 <= speed_parameter <= 3000 or not 0 <= acceleration <= 255:
            raise ValueError("speed must be 0..3000 and acceleration 0..255")
        raw = encoder_counts & 0xFFFFFF
        data = speed_parameter.to_bytes(2, "big") + bytes([acceleration]) + raw.to_bytes(3, "big")
        self._send(CMD_RUN_RELATIVE_AXIS, data)

    def close(self) -> None:
        self.bus.shutdown()


@dataclass
class SimulatedMotor:
    """Deterministic-enough motor model for API testing without CAN hardware."""
    gear_ratio: float
    encoder: float = 0.0
    shaft_rpm: float = 0.0
    _updated: float = field(default_factory=time.monotonic)

    def _advance(self) -> None:
        now = time.monotonic()
        self.encoder += self.shaft_rpm * (now - self._updated) / 60.0 * ENCODER_COUNTS_PER_REV
        self._updated = now

    def start_speed(self, ccw: bool, speed_parameter: int, acceleration: int) -> None:
        self._advance()
        self.shaft_rpm = speed_parameter * (1 if ccw else -1)

    def stop(self, acceleration: int) -> None:
        self._advance(); self.shaft_rpm = 0.0

    def emergency_stop(self) -> None:
        self.stop(0)

    def read_encoder(self) -> int:
        self._advance(); return round(self.encoder)

    def move_relative(self, encoder_counts: int, speed_parameter: int, acceleration: int) -> None:
        self._advance(); self.encoder += encoder_counts

    def close(self) -> None: pass
