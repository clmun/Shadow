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
from config import WIDTH, HEIGHT, BG_COLOR, PRIMARY_COLOR, LIGHT_COLOR, SUN_RADIUS, SUN_COLOR, MOON_RADIUS, MOON_COLOR, SHAPE

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

    @staticmethod
    def degrees_to_point(d: float, r: float):
        cx = WIDTH / 2
        cy = HEIGHT / 2
        d2 = 180 - d
        return {
            'x': cx + math.sin(math.radians(d2)) * r,
            'y': cy + math.cos(math.radians(d2)) * r
        }

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
        # Azimuth mapping: 0° = North, clockwise
        def point_from_azimuth(d: float, r: float):
            cx = WIDTH / 2
            cy = HEIGHT / 2
            theta = math.radians(d)
            return {
                'x': cx + r * math.sin(theta),
                'y': cy - r * math.cos(theta)
            }

        # Signed area to get polygon winding (CW < 0, CCW > 0)
        def signed_area(poly):
            s = 0.0
            n = len(poly)
            for i in range(n):
                x0, y0 = poly[i]['x'], poly[i]['y']
                x1, y1 = poly[(i + 1) % n]['x'], poly[(i + 1) % n]['y']
                s += x0 * y1 - x1 * y0
            return 0.5 * s

        # Outward normal based on winding
        def outward_normal(ex, ey, is_ccw):
            # Edge vector e = (ex, ey)
            # For CCW polygons, outward normal is (ey, -ex)
            # For CW polygons, outward normal is (-ey, ex)
            if is_ccw:
                return ey, -ex
            else:
                return -ey, ex

        # Light marker positions
        sun_pos = point_from_azimuth(self.sun_azimuth, WIDTH / 2)
        moon_pos = point_from_azimuth(self.moon_azimuth, WIDTH / 2)

        svg = '<?xml version="1.0" encoding="utf-8"?>'
        svg += '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="-10 -10 120 120">'
        svg += f'<circle cx="{WIDTH / 2}" cy="{HEIGHT / 2}" r="{WIDTH / 2 - 1}" fill="{BG_COLOR}"/>'

        # Shadow mask
        svg += '<defs><mask id="shadowMask">'
        svg += '<rect width="100%" height="100%" fill="black"/>'
        svg += f'<circle cx="{WIDTH / 2}" cy="{HEIGHT / 2}" r="{WIDTH / 2 - 1}" fill="white"/>'
        svg += '</mask></defs>'

        # Base house outline
        svg += self.generate_path('none', PRIMARY_COLOR, SHAPE)

        # Choose active source
        use_sun = self.sun_elevation > 0
        use_moon = (not use_sun) and (self.moon_elevation > 0)
        active = use_sun or use_moon
        light_pos = sun_pos if use_sun else (moon_pos if use_moon else None)
        active_elevation = self.sun_elevation if use_sun else (self.moon_elevation if use_moon else -1)

        if active and light_pos is not None:
            n = len(SHAPE)
            # Centroid and light direction
            cx = sum(p['x'] for p in SHAPE) / n
            cy = sum(p['y'] for p in SHAPE) / n
            Lx = light_pos['x'] - cx
            Ly = light_pos['y'] - cy

            # Polygon winding
            is_ccw = signed_area(SHAPE) > 0

            # Mark lit edges using outward normals
            edges = []
            for i in range(n):
                p0 = SHAPE[i]
                p1 = SHAPE[(i + 1) % n]
                ex = p1['x'] - p0['x']
                ey = p1['y'] - p0['y']
                nx, ny = outward_normal(ex, ey, is_ccw)
                dot = nx * Lx + ny * Ly
                edges.append({'i0': i, 'i1': (i + 1) % n, 'lit': dot > 0})

            # Longest contiguous lit chain (wrap once)
            best_start = None
            best_len = 0
            cur_start = None
            cur_len = 0
            for i in range(len(edges) * 2):
                e = edges[i % len(edges)]
                if e['lit']:
                    if cur_start is None:
                        cur_start = i
                        cur_len = 1
                    else:
                        cur_len += 1
                    if cur_len > best_len:
                        best_len = cur_len
                        best_start = cur_start
                else:
                    cur_start = None
                    cur_len = 0

            # Construct side1 (lit vertices) and side2 (the complementary chain)
            side1 = []
            side2 = []
            if best_len > 0:
                for k in range(best_len):
                    e = edges[(best_start + k) % len(edges)]
                    side1.append({'x': SHAPE[e['i0']]['x'], 'y': SHAPE[e['i0']]['y']})
                last_e = edges[(best_start + best_len - 1) % len(edges)]
                side1.append({'x': SHAPE[last_e['i1']]['x'], 'y': SHAPE[last_e['i1']]['y']})

                start_idx = edges[best_start % len(edges)]['i0']
                i_idx = last_e['i1']
                while True:
                    side2.append({'x': SHAPE[i_idx]['x'], 'y': SHAPE[i_idx]['y']})
                    if i_idx == start_idx:
                        break
                    i_idx = (i_idx + 1) % n

                # Shadow length by altitude (works for sun and moon)
                shadow_length = min(WIDTH * 2, WIDTH / max(0.001, math.tan(math.radians(active_elevation))))

                # Projection angles of illuminated chain endpoints relative to light_pos
                def proj(pt):
                    dx = pt['x'] - light_pos['x']
                    dy = pt['y'] - light_pos['y']
                    ang = math.degrees(math.atan2(-dy, dx))  # invert screen y to math y
                    return (
                        pt['x'] + shadow_length * math.cos(math.radians(ang)),
                        pt['y'] - shadow_length * math.sin(math.radians(ang))
                    )

                min_proj_x, min_proj_y = proj(side1[0])
                max_proj_x, max_proj_y = proj(side1[-1])

                shadow = [{'x': max_proj_x, 'y': max_proj_y}] + side2 + [{'x': min_proj_x, 'y': min_proj_y}]
                shadow_svg = self.generate_path('none', 'black', shadow, 'mask="url(#shadowMask)" fill-opacity="0.5"')

                # Draw illuminated edge and shadow behind
                svg += self.generate_path(LIGHT_COLOR, 'none', side1)
                svg += shadow_svg
            else:
                # Fallback: draw full outline if no lit chain found
                svg += self.generate_path(PRIMARY_COLOR, 'none', SHAPE)
        else:
            # No active source
            svg += self.generate_path(PRIMARY_COLOR, 'none', SHAPE)

        # Day/Night arcs
        svg += self.generate_arc(WIDTH / 2, PRIMARY_COLOR, 'none', self.sunset_azimuth, self.sunrise_azimuth)
        svg += self.generate_arc(WIDTH / 2, LIGHT_COLOR, 'none', self.sunrise_azimuth, self.sunset_azimuth)

        # Sunrise/Sunset ticks
        svg += self.generate_path(LIGHT_COLOR, 'none', [
            point_from_azimuth(self.sunrise_azimuth, WIDTH / 2 - 2),
            point_from_azimuth(self.sunrise_azimuth, WIDTH / 2 + 2)
        ])
        svg += self.generate_path(LIGHT_COLOR, 'none', [
            point_from_azimuth(self.sunset_azimuth, WIDTH / 2 - 2),
            point_from_azimuth(self.sunset_azimuth, WIDTH / 2 + 2)
        ])

        # Hour arcs
        for i in range(len(self.degs)):
            j = 0 if i == len(self.degs) - 1 else i + 1
            if i % 2 == 0:
                svg += self.generate_arc(WIDTH / 2 + 8, PRIMARY_COLOR, 'none', self.degs[i], self.degs[j],
                                         'stroke-width="3" stroke-opacity="0.2"')
            else:
                svg += self.generate_arc(WIDTH / 2 + 8, PRIMARY_COLOR, 'none', self.degs[i], self.degs[j],
                                         'stroke-width="3"')

        # 00:00 and 12:00 ticks
        svg += self.generate_path(LIGHT_COLOR, 'none', [
            point_from_azimuth(self.degs[0], WIDTH / 2 + 5),
            point_from_azimuth(self.degs[0], WIDTH / 2 + 11)
        ])
        mid_index = len(self.degs) // 2
        svg += self.generate_path(LIGHT_COLOR, 'none', [
            point_from_azimuth(self.degs[mid_index], WIDTH / 2 + 5),
            point_from_azimuth(self.degs[mid_index], WIDTH / 2 + 11)
        ])

        # Sun marker
        if self.sun_elevation > 0:
            svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS}" fill="{SUN_COLOR}55" />'
            svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS - 1}" fill="{SUN_COLOR}99" />'
            svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS - 2}" fill="{SUN_COLOR}" />'

        # Moon phase marker
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

        # Add the timestamp to the SVG in the bottom-right corner
        timestamp = self.now.strftime("%Y-%m-%d %H:%M:%S")
        svg += f'<text x="{WIDTH + 5}" y="{HEIGHT + 10}" font-size="3" text-anchor="end" fill="yellow">{timestamp}</text>'

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
