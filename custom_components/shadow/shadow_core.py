from __future__ import annotations

import math
import os
import asyncio
from dataclasses import dataclass
from datetime import datetime, date, time
import zoneinfo
import pylunar
from astral import sun, Observer
from astral.location import LocationInfo

# Constante vizuale
WIDTH = 100
HEIGHT = 100
PRIMARY_COLOR = '#1b3024'
LIGHT_COLOR = '#26bf75'
BG_COLOR = '#1a1919'
SUN_COLOR = '#ffff66'
SUN_RADIUS = 5
MOON_COLOR = '#999999'
MOON_RADIUS = 3

# Forma casei (original)
SHAPE = [
    {'x': 35.34, 'y': 70.00},
    {'x': 20.00, 'y': 38.54},
    {'x': 70.33, 'y': 13.99},
    {'x': 85.68, 'y': 45.45},
    {'x': 68.37, 'y': 53.89},
    {'x': 71.44, 'y': 60.18},
    {'x': 55.71, 'y': 67.85},
    {'x': 52.64, 'y': 61.56}
]

HOURS = 1

@dataclass
class ShadowConfig:
    latitude: float
    longitude: float
    altitude: float
    timezone: str
    town: str
    output_path: str

class Shadow:
    def __init__(self, conf: ShadowConfig):
        self.conf = conf
        self.location = LocationInfo(conf.town, conf.timezone, conf.latitude, conf.longitude)
        self.timezone = zoneinfo.ZoneInfo(conf.timezone)
        self.now = datetime.now(self.timezone)
        self.nowUTC = datetime.now(zoneinfo.ZoneInfo("UTC"))

        # Observer explicit (corect pentru astral)
        self._observer = Observer(
            latitude=self.conf.latitude,
            longitude=self.conf.longitude,
            elevation=self.conf.altitude
        )

        # Date solare (cu tzinfo explicit)
        self.sun_data = sun.sun(self._observer, date=self.now.date(), tzinfo=self.timezone)
        self.sunrise_azimuth = sun.azimuth(self._observer, self.sun_data['sunrise'])
        self.sunset_azimuth = sun.azimuth(self._observer, self.sun_data['sunset'])
        self.sun_azimuth = sun.azimuth(self._observer, self.now)
        self.sun_elevation = sun.elevation(self._observer, self.now)

        # Azimutul soarelui la fiecare oră (ore locale)
        self.degs = []
        local_date = self.now.date()
        for i in range(0, 24, HOURS):
            hour_time = datetime(local_date.year, local_date.month, local_date.day, i, 0, 0, tzinfo=self.timezone)
            a = sun.azimuth(self._observer, hour_time)
            self.degs.append(float(a) if a is not None else 0)

        # Date lunare
        self.moon_info = pylunar.MoonInfo(self.decdeg2dms(conf.latitude), self.decdeg2dms(conf.longitude))
        self.moon_info.update(self.nowUTC.replace(tzinfo=None))
        self.moon_azimuth = self.moon_info.azimuth()
        self.moon_elevation = self.moon_info.altitude()

        # Sursa curentă de lumină (altitudine)
        self.elevation = self.sun_elevation if self.sun_elevation > 0 else self.moon_elevation

        self._debug()

    def refresh(self):
        self.now = datetime.now(self.timezone)
        self.nowUTC = datetime.now(zoneinfo.ZoneInfo("UTC"))

        self.sun_data = sun.sun(self._observer, date=self.now.date(), tzinfo=self.timezone)
        self.sunrise_azimuth = sun.azimuth(self._observer, self.sun_data['sunrise'])
        self.sunset_azimuth = sun.azimuth(self._observer, self.sun_data['sunset'])
        self.sun_azimuth = sun.azimuth(self._observer, self.now)
        self.sun_elevation = sun.elevation(self._observer, self.now)

        self.degs = []
        local_date = self.now.date()
        for i in range(0, 24, HOURS):
            hour_time = datetime(local_date.year, local_date.month, local_date.day, i, 0, 0, tzinfo=self.timezone)
            a = sun.azimuth(self._observer, hour_time)
            self.degs.append(float(a) if a is not None else 0)

        self.moon_info.update(self.nowUTC.replace(tzinfo=None))
        self.moon_azimuth = self.moon_info.azimuth()
        self.moon_elevation = self.moon_info.altitude()

        self.elevation = self.sun_elevation if self.sun_elevation > 0 else self.moon_elevation

        self._debug()

    def decdeg2dms(self, dd: float):
        negative = dd < 0
        dd = abs(dd)
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        if negative:
            if degrees > 0:
                degrees = -degrees
            elif minutes > 0:
                minutes = -minutes
            else:
                seconds = -seconds
        return (int(degrees), int(minutes), int(seconds))

    def degrees_to_point(self, d: float, r: float):
        cx = WIDTH / 2
        cy = HEIGHT / 2
        d2 = 180 - d
        return {
            'x': cx + math.sin(math.radians(d2)) * r,
            'y': cy + math.cos(math.radians(d2)) * r
        }

    def generate_path(self, stroke: str, fill: str, points: list[dict], attrs: str | None = None) -> str:
        p = f'<path stroke="{stroke}" stroke-width="1" fill="{fill}" '
        if attrs:
            p += f'{attrs} '
        p += 'd="'
        for idx, point in enumerate(points):
            if idx == 0:
                p += f'M{point["x"]} {point["y"]}'
            else:
                p += f' L{point["x"]} {point["y"]}'
        p += '" />'
        return p

    def generate_arc(self, dist: float, stroke: str, fill: str | None, start: float, end: float, attrs: str | None = None) -> str:
        angle = end - start
        if angle < 0:
            angle = 360 + angle
        start_pt = self.degrees_to_point(start, dist)
        end_pt = self.degrees_to_point(end, dist)
        p = f'<path d="M{start_pt["x"]} {start_pt["y"]} A{dist} {dist} 0 '
        p += '0 1 ' if angle < 180 else '1 1 '
        p += f'{end_pt["x"]} {end_pt["y"]}" stroke="{stroke}" '
        p += f'fill="{fill}" ' if fill else 'fill="none" '
        p += attrs if attrs else 'stroke-width="1"'
        p += ' />'
        return p

    def _build_svg(self) -> str:
        # Flags pentru control modular
        show_shadow = True
        show_sun_moon = True
        show_compass = True
        show_hour_labels = True

        # Poziții soare/lună pe cerc
        sun_pos = self.degrees_to_point(self.sun_azimuth, WIDTH / 2)
        moon_pos = self.degrees_to_point(self.moon_azimuth, WIDTH / 2)

        svg = '<?xml version="1.0" encoding="utf-8"?>'
        svg += '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="-10 -10 120 120">'
        svg += f'<circle cx="{WIDTH / 2}" cy="{HEIGHT / 2}" r="{WIDTH / 2 - 1}" fill="{BG_COLOR}"/>'

        # Forma casei (mereu)
        svg += self.generate_path('none', PRIMARY_COLOR, SHAPE)

        # --- Umbra ---
        if show_shadow:
            if self.sun_elevation > 0:
                source_azimuth = self.sun_azimuth
                source_elevation = self.sun_elevation
            elif self.moon_elevation > 0:
                source_azimuth = self.moon_azimuth
                source_elevation = self.moon_elevation
            else:
                source_azimuth = None

            if source_azimuth is not None:
                shadow_azimuth = source_azimuth + 180
                length = 40 / max(math.tan(math.radians(source_elevation)), 0.1)
                shadow_end = self.degrees_to_point(shadow_azimuth, length)
                svg += self.generate_path("#000000", "none", [
                    {"x": WIDTH / 2, "y": HEIGHT / 2},
                    shadow_end
                ], 'stroke-opacity="0.5" stroke-width="2"')

        # --- Arce: noapte și zi ---
        svg += self.generate_arc(WIDTH / 2, PRIMARY_COLOR, 'none', self.sunset_azimuth, self.sunrise_azimuth)
        svg += self.generate_arc(WIDTH / 2, LIGHT_COLOR, 'none', self.sunrise_azimuth, self.sunset_azimuth)

        # --- Tick marks la răsărit/apus ---
        svg += self.generate_path(LIGHT_COLOR, 'none', [
            self.degrees_to_point(self.sunrise_azimuth, WIDTH / 2 - 2),
            self.degrees_to_point(self.sunrise_azimuth, WIDTH / 2 + 2)
        ])
        svg += self.generate_path(LIGHT_COLOR, 'none', [
            self.degrees_to_point(self.sunset_azimuth, WIDTH / 2 - 2),
            self.degrees_to_point(self.sunset_azimuth, WIDTH / 2 + 2)
        ])

        # --- Orele (arce pe cerc) ---
        for i in range(len(self.degs)):
            j = 0 if i == len(self.degs) - 1 else i + 1
            if i % 2 == 0:
                svg += self.generate_arc(WIDTH / 2 + 8, PRIMARY_COLOR, 'none', self.degs[i], self.degs[j],
                                         'stroke-width="3" stroke-opacity="0.2"')
            else:
                svg += self.generate_arc(WIDTH / 2 + 8, PRIMARY_COLOR, 'none', self.degs[i], self.degs[j],
                                         'stroke-width="3"')

        # --- Tick 00:00 și 12:00 ---
        svg += self.generate_path(LIGHT_COLOR, 'none', [
            self.degrees_to_point(self.degs[0], WIDTH / 2 + 5),
            self.degrees_to_point(self.degs[0], WIDTH / 2 + 11)
        ])
        mid_index = len(self.degs) // 2
        svg += self.generate_path(LIGHT_COLOR, 'none', [
            self.degrees_to_point(self.degs[mid_index], WIDTH / 2 + 5),
            self.degrees_to_point(self.degs[mid_index], WIDTH / 2 + 11)
        ])

        # --- Etichete orare ---
        if show_hour_labels:
            for i, deg in enumerate(self.degs):
                pt = self.degrees_to_point(deg, WIDTH / 2 + 12)
                svg += f'<text x="{pt["x"]}" y="{pt["y"]}" font-size="3" fill="white">{i}:00</text>'

        # --- Busolă ---
        if show_compass:
            compass_radius = 8
            directions = {'N': 0, 'E': 90, 'S': 180, 'W': 270}
            for label, deg in directions.items():
                pt = self.degrees_to_point(deg, compass_radius)
                svg += f'<text x="{pt["x"]}" y="{pt["y"]}" font-size="4" fill="white">{label}</text>'

        # --- Soare și lună ---
        if show_sun_moon:
            # Luna (arce pentru fază)
            phase = moon.phase(self.now)
            left_radius = MOON_RADIUS
            left_sweep = 0
            right_radius = MOON_RADIUS
            right_sweep = 0
            if phase > 14:
                right_radius = MOON_RADIUS - (2.0 * MOON_RADIUS * (1.0 - ((phase % 14) * 0.99 / 14.0)))
                if right_radius < 0:
                    right_radius = -right_radius
                    right_sweep = 0
                else:
                    right_sweep = 1
            if phase < 14:
                left_radius = MOON_RADIUS - (2.0 * MOON_RADIUS * (1.0 - ((phase % 14) * 0.99 / 14.0)))
                if left_radius < 0:
                    left_radius = -left_radius
                    left_sweep = 1

            if self.moon_elevation > 0:
                svg += f'<path stroke="none" fill="{MOON_COLOR}" d="M {moon_pos["x"]} {moon_pos["y"] - MOON_RADIUS} ' \
                       f'A {left_radius} {MOON_RADIUS} 0 0 {left_sweep} {moon_pos["x"]} {moon_pos["y"] + MOON_RADIUS} ' \
                       f'A {right_radius} {MOON_RADIUS} 0 0 {right_sweep} {moon_pos["x"]} {moon_pos["y"] - MOON_RADIUS} z" />'

            # Soare (cercuri concentrice)
            if self.sun_elevation > 0:
                svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS}" fill="{SUN_COLOR}55" />'
                svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS - 1}" fill="{SUN_COLOR}99" />'
                svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS - 2}" fill="{SUN_COLOR}" />'

        svg += '</svg>'
        return svg

    def _write_svg(self, svg_content: str):
        folder = os.path.dirname(self.conf.output_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        with open(self.conf.output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

    async def async_generate_svg(self, hass):
        # Recalculează înainte de generare
        self.refresh()
        svg_content = self._build_svg()
        # Scriere non-blocking prin executorul Home Assistant
        await hass.async_add_executor_job(self._write_svg, svg_content)

    def generate_svg(self, hass):
        """Compact wrapper for manifest action."""
        return asyncio.run_coroutine_threadsafe(
            self.async_generate_svg(hass),
            asyncio.get_event_loop()
        )

    def _debug(self):
        print("=== Debug Info ===")
        print("Town:", self.conf.town)
        print("Now local:", self.now.isoformat())
        print("Sunrise:", self.sun_data['sunrise'].isoformat())
        print("Sunset:", self.sun_data['sunset'].isoformat())
        print("Sun azimuth:", f"{self.sun_azimuth:.2f}")
        print("Sun elevation:", f"{self.sun_elevation:.2f}")
        print("Moon azimuth:", f"{self.moon_azimuth:.2f}")
        print("Moon elevation:", f"{self.moon_elevation:.2f}")
