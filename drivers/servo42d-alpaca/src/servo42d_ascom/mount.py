from __future__ import annotations
from datetime import datetime, timedelta, timezone
import math
import threading
from .config import MountConfig
from .mks_protocol import ENCODER_COUNTS_PER_REV, MotorIO

SIDEREAL_DEG_PER_SEC = 360.0 / 86164.0905


class EquatorialMount:
    """Two-axis equatorial model. Coordinate origin is established by Sync."""
    def __init__(self, ra_motor: MotorIO, dec_motor: MotorIO, config: MountConfig):
        self.ra_motor, self.dec_motor, self.config = ra_motor, dec_motor, config
        self.connected = self.tracking = self.slewing = self.is_pulse_guiding = False
        self._ra_encoder_zero = self._dec_encoder_zero = 0
        self._ra_zero, self._dec_zero = config.initial_ra_hours % 24, config.initial_dec_degrees
        self.site_latitude = 0.0
        self.site_longitude = 0.0
        self.site_elevation = 0.0
        self._utc_offset = timedelta(0)
        self._lock = threading.RLock()
        self._guide_generation = [0, 0]
        self._guiding_axes: set[int] = set()

    def connect(self) -> None:
        with self._lock:
            self._ra_encoder_zero, self._dec_encoder_zero = self.ra_motor.read_encoder(), self.dec_motor.read_encoder()
            self.connected = True

    def disconnect(self) -> None:
        with self._lock:
            self.ra_motor.stop(self.config.acceleration); self.dec_motor.stop(self.config.acceleration)
            self.connected = self.tracking = self.slewing = self.is_pulse_guiding = False

    def _ensure(self) -> None:
        if not self.connected: raise RuntimeError("Mount is not connected")

    @staticmethod
    def _axis_degrees(counts: int, zero: int, ratio: float, ccw_positive: bool) -> float:
        return (1 if ccw_positive else -1) * (counts-zero) * 360 / (ENCODER_COUNTS_PER_REV*ratio)

    @property
    def right_ascension(self) -> float:
        self._ensure()
        deg = self._axis_degrees(self.ra_motor.read_encoder(), self._ra_encoder_zero, self.config.ra_gear_ratio, self.config.ra_positive_direction == "ccw")
        return (self._ra_zero + deg/15) % 24

    @property
    def declination(self) -> float:
        self._ensure()
        deg = self._dec_zero + self._axis_degrees(self.dec_motor.read_encoder(), self._dec_encoder_zero, self.config.dec_gear_ratio, self.config.dec_positive_direction == "ccw")
        return max(-90.0, min(90.0, deg))

    @property
    def utc_date(self) -> datetime:
        return datetime.now(timezone.utc) + self._utc_offset

    def set_utc_date(self, value: str) -> None:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone(timezone.utc)
        self._utc_offset = parsed - datetime.now(timezone.utc)

    @property
    def sidereal_time(self) -> float:
        utc = self.utc_date
        jd = utc.timestamp() / 86400.0 + 2440587.5
        centuries = (jd - 2451545.0) / 36525.0
        gmst_degrees = (
            280.46061837
            + 360.98564736629 * (jd - 2451545.0)
            + 0.000387933 * centuries * centuries
            - centuries * centuries * centuries / 38710000.0
        )
        return ((gmst_degrees + self.site_longitude) % 360.0) / 15.0

    def _horizontal_coordinates(self) -> tuple[float, float]:
        ra_degrees = self.right_ascension * 15.0
        dec = math.radians(self.declination)
        latitude = math.radians(self.site_latitude)
        hour_angle = math.radians((self.sidereal_time * 15.0 - ra_degrees) % 360.0)
        sin_altitude = (
            math.sin(dec) * math.sin(latitude)
            + math.cos(dec) * math.cos(latitude) * math.cos(hour_angle)
        )
        altitude = math.asin(max(-1.0, min(1.0, sin_altitude)))
        east = -math.cos(dec) * math.sin(hour_angle)
        north = (
            math.sin(dec) * math.cos(latitude)
            - math.cos(dec) * math.sin(latitude) * math.cos(hour_angle)
        )
        if abs(east) < 1e-12 and abs(north) < 1e-12:
            azimuth = 0.0
        else:
            azimuth = math.atan2(east, north)
        return math.degrees(altitude), math.degrees(azimuth) % 360.0

    @property
    def altitude(self) -> float:
        return self._horizontal_coordinates()[0]

    @property
    def azimuth(self) -> float:
        return self._horizontal_coordinates()[1]

    def set_site_latitude(self, value: float) -> None:
        if not -90.0 <= value <= 90.0:
            raise ValueError("Site latitude must be between -90 and 90 degrees")
        self.site_latitude = value

    def set_site_longitude(self, value: float) -> None:
        if not -180.0 <= value <= 180.0:
            raise ValueError("Site longitude must be between -180 and 180 degrees")
        self.site_longitude = value

    def set_site_elevation(self, value: float) -> None:
        if not -300.0 <= value <= 10000.0:
            raise ValueError("Site elevation must be between -300 and 10000 metres")
        self.site_elevation = value

    def sync(self, ra_hours: float, dec_degrees: float) -> None:
        self._ensure()
        if not 0 <= ra_hours < 24 or not -90 <= dec_degrees <= 90: raise ValueError("Invalid equatorial coordinates")
        self._ra_encoder_zero, self._dec_encoder_zero = self.ra_motor.read_encoder(), self.dec_motor.read_encoder()
        self._ra_zero, self._dec_zero = ra_hours, dec_degrees

    def _speed(self, output_rate: float, ratio: float) -> int:
        shaft_rpm = abs(output_rate)*ratio/6
        factor = 1 if self.config.microsteps in (16,32,64) else 16/self.config.microsteps
        value = round(shaft_rpm/factor)
        if output_rate and value == 0: raise ValueError("Rate below motor resolution; increase gear ratio")
        if value > 3000: raise ValueError("Rate exceeds motor limit")
        return value

    def set_tracking(self, enabled: bool) -> None:
        with self._lock:
            self._ensure()
            if enabled: self.ra_motor.start_speed(self.config.ra_positive_direction == "ccw", self._speed(SIDEREAL_DEG_PER_SEC, self.config.ra_gear_ratio), self.config.acceleration)
            else: self.ra_motor.stop(self.config.acceleration)
            self.tracking = enabled

    def move_axis(self, axis: int, rate: float) -> None:
        self._ensure()
        if axis not in (0,1) or abs(rate) > self.config.max_axis_rate_deg_per_sec: raise ValueError("Invalid axis/rate")
        motor = self.ra_motor if axis == 0 else self.dec_motor
        ratio = self.config.ra_gear_ratio if axis == 0 else self.config.dec_gear_ratio
        positive = (self.config.ra_positive_direction if axis == 0 else self.config.dec_positive_direction) == "ccw"
        if rate == 0:
            if axis == 0: self.set_tracking(self.tracking)
            else: motor.stop(self.config.acceleration)
        else: motor.start_speed(positive if rate > 0 else not positive, self._speed(rate, ratio), self.config.acceleration)

    def slew_to(self, ra_hours: float, dec_degrees: float) -> None:
        self._ensure()
        if not 0 <= ra_hours < 24 or not -90 <= dec_degrees <= 90: raise ValueError("Invalid equatorial coordinates")
        dra = ((ra_hours-self.right_ascension+12)%24-12)*15
        ddec = dec_degrees-self.declination
        ra_counts = round(dra/360*ENCODER_COUNTS_PER_REV*self.config.ra_gear_ratio)*(1 if self.config.ra_positive_direction == "ccw" else -1)
        dec_counts = round(ddec/360*ENCODER_COUNTS_PER_REV*self.config.dec_gear_ratio)*(1 if self.config.dec_positive_direction == "ccw" else -1)
        self.slewing = True
        try:
            self.ra_motor.move_relative(ra_counts, self._speed(self.config.goto_rate_deg_per_sec,self.config.ra_gear_ratio), self.config.acceleration)
            self.dec_motor.move_relative(dec_counts, self._speed(self.config.goto_rate_deg_per_sec,self.config.dec_gear_ratio), self.config.acceleration)
        finally: self.slewing = False
        if self.tracking: self.set_tracking(True)

    def pulse_guide(self, direction: int, duration_ms: int) -> None:
        with self._lock:
            self._ensure()
            if direction not in range(4) or not 0 < duration_ms <= 60000:
                raise ValueError("Invalid guide direction/duration")

            # Alpaca directions: North=0, South=1, East=2, West=3.  The
            # Servo42D speed command has an integer-RPM floor, so normal guide
            # rates (especially 0.5x sidereal on RA) round to zero.  Use an F4
            # relative encoder move instead: the requested pulse duration is
            # converted to the exact angular displacement at the output axis.
            axis, sign = ((1, 1) if direction == 0 else
                          (1, -1) if direction == 1 else
                          (0, -1) if direction == 2 else (0, 1))
            ratio = self.config.ra_gear_ratio if axis == 0 else self.config.dec_gear_ratio
            positive = (self.config.ra_positive_direction if axis == 0 else
                        self.config.dec_positive_direction) == "ccw"
            rate = SIDEREAL_DEG_PER_SEC * (0.5 if axis == 0 else 1.0) * sign

            # While tracking, an RA guide pulse replaces the normal speed
            # command, so include the base sidereal displacement in the move.
            if axis == 0 and self.tracking:
                rate += SIDEREAL_DEG_PER_SEC

            duration_seconds = duration_ms / 1000.0
            counts = round(rate * duration_seconds / 360.0 * ENCODER_COUNTS_PER_REV * ratio)
            if not positive:
                counts = -counts
            if counts == 0:
                counts = (1 if rate > 0 else -1) * (1 if positive else -1)

            # Run at the nearest supported motor speed (minimum 1 RPM).  F4
            # controls distance independently, so rounding speed cannot lose
            # the small guide displacement as it did with F6.
            shaft_rpm = abs(counts) * 60.0 / (ENCODER_COUNTS_PER_REV * duration_seconds)
            speed_parameter = min(3000, max(1, round(shaft_rpm)))
            motor = self.ra_motor if axis == 0 else self.dec_motor
            motor.move_relative(counts, speed_parameter, self.config.acceleration)

            self._guide_generation[axis] += 1
            generation = self._guide_generation[axis]
            self._guiding_axes.add(axis)
            self.is_pulse_guiding = True
            timer = threading.Timer(duration_seconds, self._end_guide, args=(axis, generation))
            timer.daemon = True
            timer.start()

    def _end_guide(self, axis: int, generation: int) -> None:
        with self._lock:
            # Ignore an old timer if a newer pulse has replaced it on this axis.
            if generation != self._guide_generation[axis]:
                return
            self._guiding_axes.discard(axis)
            self.is_pulse_guiding = bool(self._guiding_axes)
            self.move_axis(axis, 0)

    def abort(self) -> None:
        self._ensure(); self.ra_motor.emergency_stop(); self.dec_motor.emergency_stop()
        self.tracking=self.slewing=self.is_pulse_guiding=False
