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
from astral import moon
from custom_components.shadow.shadow_config import WIDTH, HEIGHT, BG_COLOR, PRIMARY_COLOR, LIGHT_COLOR, SUN_RADIUS, SUN_COLOR, MOON_RADIUS, MOON_COLOR, SHAPE

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

    def refresh(self, override_time: datetime | None = None):
        self.now = override_time or datetime.now(self.timezone)
        self.nowUTC = self.now.astimezone(zoneinfo.ZoneInfo("UTC"))

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

    @staticmethod
    def decdeg2dms(dd: float):
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
        return int(degrees), int(minutes), int(seconds)

    # Azimuth mapping: 0° = North, clockwise
    @staticmethod
    def azimuth_to_point(d: float, r: float, cx: float = WIDTH / 2, cy: float = HEIGHT / 2):
        theta = math.radians(d)
        return {
            'x': cx + r * math.sin(theta),
            'y': cy - r * math.cos(theta)
        }
    @staticmethod
    def azimuth_to_unit_vector(d: float):
        theta = math.radians(d)
        return math.sin(theta), -math.cos(theta)

    @staticmethod
    def generate_path(stroke: str, fill: str, points: list[dict], attrs: str | None = None) -> str:
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
        start_pt = self.azimuth_to_point(start, dist)
        end_pt = self.azimuth_to_point(end, dist)
        p = f'<path d="M{start_pt["x"]} {start_pt["y"]} A{dist} {dist} 0 '
        p += '0 1 ' if angle < 180 else '1 1 '
        p += f'{end_pt["x"]} {end_pt["y"]}" stroke="{stroke}" '
        p += f'fill="{fill}" ' if fill else 'fill="none" '
        p += attrs if attrs else 'stroke-width="1"'
        p += ' />'
        return p
    # Signed area to get polygon winding (CW < 0, CCW > 0)
    @staticmethod
    def signed_area(poly):
        s = 0.0
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]['x'], poly[i]['y']
            x1, y1 = poly[(i + 1) % n]['x'], poly[(i + 1) % n]['y']
            s += x0 * y1 - x1 * y0
        return 0.5 * s

    @staticmethod
    # Outward normal based on winding
    def outward_normal(ex, ey, is_ccw):
        # Edge vector e = (ex, ey)
        # For CCW polygons, outward normal is (ey, -ex)
        # For CW polygons, outward normal is (-ey, ex)
        if is_ccw:
            return ey, -ex
        else:
            return -ey, ex
    # Build the complete SVG content
    @staticmethod
    def _svg_header() -> str:
        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="-10 -10 120 120">'
            f'<circle cx="{WIDTH/2}" cy="{HEIGHT/2}" r="{WIDTH/2-1}" fill="{BG_COLOR}"/>'
        )

    @staticmethod
    def _svg_shadow_mask() -> str:
        return (
            '<defs><mask id="shadowMask">'
            '<rect width="100%" height="100%" fill="black"/>'
            f'<circle cx="{WIDTH/2}" cy="{HEIGHT/2}" r="{WIDTH/2-1}" fill="white"/>'
            '</mask></defs>'
        )

    def _svg_outline(self) -> str:
        return self.generate_path('none', PRIMARY_COLOR, SHAPE)

    def _svg_shadow(self, sun_pos, moon_pos) -> str:
        use_sun = self.sun_elevation > 0
        use_moon = (not use_sun) and (self.moon_elevation > 0)
        if not (use_sun or use_moon):
            return self.generate_path(PRIMARY_COLOR, 'none', SHAPE)

        elev = self.sun_elevation if use_sun else self.moon_elevation
        az = self.sun_azimuth if use_sun else self.moon_azimuth
        light_pos = sun_pos if use_sun else moon_pos
        sdx, sdy = self.azimuth_to_unit_vector(az)

        # Centroid
        cx = sum(p['x'] for p in SHAPE) / len(SHAPE)
        cy = sum(p['y'] for p in SHAPE) / len(SHAPE)

        # Unghiuri față de lumină
        angles = []
        for i, pt in enumerate(SHAPE):
            dx = pt['x'] - light_pos['x']
            dy = pt['y'] - light_pos['y']
            ang = math.degrees(math.atan2(-dy, dx)) % 360  # y inversat
            angles.append((ang, i))

        # Puncte extreme
        min_angle, min_idx = min(angles)
        max_angle, max_idx = max(angles)

        # Lanț iluminat: de la min_idx la max_idx
        side1 = []
        i = min_idx
        while True:
            side1.append(SHAPE[i])
            if i == max_idx:
                break
            i = (i + 1) % len(SHAPE)

        # Lanț umbrit: restul
        side2 = []
        i = max_idx
        while True:
            side2.append(SHAPE[i])
            if i == min_idx:
                break
            i = (i + 1) % len(SHAPE)

        # Lungimea umbrei
        shadow_length = min(WIDTH * 2, WIDTH / max(0.001, math.tan(math.radians(elev))))

        # Proiecție pe capete
        min_proj = {
            'x': SHAPE[min_idx]['x'] - shadow_length * sdx,
            'y': SHAPE[min_idx]['y'] - shadow_length * sdy
        }
        max_proj = {
            'x': SHAPE[max_idx]['x'] - shadow_length * sdx,
            'y': SHAPE[max_idx]['y'] - shadow_length * sdy
        }

        # Umbra = capăt proiectat + side2 + celălalt capăt proiectat
        shadow = [max_proj] + side2 + [min_proj]
        shadow_svg = self.generate_path('none', 'black', shadow,
                                        'mask="url(#shadowMask)" fill-opacity="0.5"')

        shape_svg = self.generate_path(PRIMARY_COLOR, 'none', SHAPE)
        light_svg = self.generate_path(LIGHT_COLOR, 'none', side1)

        return shape_svg + light_svg + shadow_svg

    def _svg_day_night_arcs(self) -> str:
        return (
            self.generate_arc(WIDTH/2, PRIMARY_COLOR, 'none', self.sunset_azimuth, self.sunrise_azimuth) +
            self.generate_arc(WIDTH/2, LIGHT_COLOR, 'none', self.sunrise_azimuth, self.sunset_azimuth)
        )

    def _svg_sunrise_sunset_ticks(self) -> str:
        return (
            self.generate_path(LIGHT_COLOR, 'none', [
                self.azimuth_to_point(self.sunrise_azimuth, WIDTH/2 - 2),
                self.azimuth_to_point(self.sunrise_azimuth, WIDTH/2 + 2)
            ]) +
            self.generate_path(LIGHT_COLOR, 'none', [
                self.azimuth_to_point(self.sunset_azimuth, WIDTH/2 - 2),
                self.azimuth_to_point(self.sunset_azimuth, WIDTH/2 + 2)
            ])
        )

    def _svg_hour_arcs(self) -> str:
        svg = ""
        for i in range(len(self.degs)):
            j = 0 if i == len(self.degs) - 1 else i + 1
            attrs = 'stroke-width="3" stroke-opacity="0.2"' if i % 2 == 0 else 'stroke-width="3"'
            svg += self.generate_arc(WIDTH/2 + 8, PRIMARY_COLOR, 'none', self.degs[i], self.degs[j], attrs)
        return svg

    def _svg_ticks_midnight_noon(self) -> str:
        return (
            self.generate_path(LIGHT_COLOR, 'none', [
                self.azimuth_to_point(self.degs[0], WIDTH/2 + 5),
                self.azimuth_to_point(self.degs[0], WIDTH/2 + 11)
            ]) +
            self.generate_path(LIGHT_COLOR, 'none', [
                self.azimuth_to_point(self.degs[len(self.degs)//2], WIDTH/2 + 5),
                self.azimuth_to_point(self.degs[len(self.degs)//2], WIDTH/2 + 11)
            ])
        )

    def _svg_sun_marker(self, sun_pos) -> str:
        if self.sun_elevation <= 0:
            return ""
        return (
            f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS}" fill="{SUN_COLOR}55" />'
            f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS-1}" fill="{SUN_COLOR}99" />'
            f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS-2}" fill="{SUN_COLOR}" />'
        )

    def _svg_moon_marker(self, moon_pos) -> str:
        if self.moon_elevation <= 0:
            return ""

        phase = moon.phase(self.now)

        # valori implicite
        left_radius = MOON_RADIUS
        left_sweep = 0
        right_radius = MOON_RADIUS
        right_sweep = 0

        # faza lunii > 14 (după lună plină)
        if phase > 14:
            right_radius = MOON_RADIUS - (2.0 * MOON_RADIUS * (1.0 - ((phase % 14) * 0.99 / 14.0)))
            if right_radius < 0:
                right_radius = -right_radius
                right_sweep = 0
            else:
                right_sweep = 1

        # faza lunii < 14 (înainte de lună plină)
        if phase < 14:
            left_radius = MOON_RADIUS - (2.0 * MOON_RADIUS * (1.0 - ((phase % 14) * 0.99 / 14.0)))
            if left_radius < 0:
                left_radius = -left_radius
                left_sweep = 1

        # path SVG pentru disc lunar cu fază
        return (
            f'<path stroke="none" fill="{MOON_COLOR}" '
            f'd="M {moon_pos["x"]} {moon_pos["y"] - MOON_RADIUS} '
            f'A {left_radius} {MOON_RADIUS} 0 0 {left_sweep} {moon_pos["x"]} {moon_pos["y"] + MOON_RADIUS} '
            f'A {right_radius} {MOON_RADIUS} 0 0 {right_sweep} {moon_pos["x"]} {moon_pos["y"] - MOON_RADIUS} z" />'
        )

    def _svg_timestamp(self) -> str:
        ts = self.now.strftime("%Y-%m-%d %H:%M:%S")
        return f'<text x="{WIDTH+5}" y="{HEIGHT+10}" font-size="3" text-anchor="end" fill="yellow">{ts}</text>'

    # def _svg_sun_ray(self, sun_pos):
    #     # linie din centrul shape-ului spre direcția soarelui
    #     cx, cy = WIDTH / 2, HEIGHT / 2
    #     sdx, sdy = self.azimuth_to_unit_vector(self.sun_azimuth)
    #     ray = [
    #         {'x': cx, 'y': cy},
    #         {'x': cx + 100 * sdx, 'y': cy + 100 * sdy}
    #     ]
    #     return self.generate_path('yellow', 'none', ray, 'stroke-dasharray="2,2"')

    def _build_svg(self) -> str:
        sun_pos = self.azimuth_to_point(self.sun_azimuth, WIDTH/2)
        moon_pos = self.azimuth_to_point(self.moon_azimuth, WIDTH/2)

        svg = self._svg_header()
        svg += self._svg_shadow_mask()
        svg += self._svg_outline()
        svg += self._svg_shadow(sun_pos, moon_pos)
        svg += self._svg_day_night_arcs()
        svg += self._svg_sunrise_sunset_ticks()
        svg += self._svg_hour_arcs()
        svg += self._svg_ticks_midnight_noon()
        svg += self._svg_sun_marker(sun_pos)
        svg += self._svg_moon_marker(moon_pos)
        svg += self._svg_timestamp()
        # svg += self._svg_sun_ray(sun_pos)
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
