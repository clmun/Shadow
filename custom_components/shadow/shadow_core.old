from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, date, time

import pytz
import pylunar
from astral import sun
from astral.location import LocationInfo

# Default visual constants (can be edited here)
WIDTH = 100
HEIGHT = 100
PRIMARY_COLOR = '#1b3024'
LIGHT_COLOR = '#26bf75'
BG_COLOR = '#1a1919'
HOUSE_COLOR = '#3f3f3f'
STROKE_WIDTH = '1'
SUN_COLOR = '#ffff66'
SUN_RADIUS = 5
MOON_COLOR = '#999999'
MOON_RADIUS = 3

# Shape of the house in a 100 by 100 units square
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
        self.debug = False
        self.conf = conf
        self.location = LocationInfo(conf.town, conf.timezone, conf.latitude, conf.longitude)
        self.timezone = pytz.timezone(conf.timezone)
        self.now = self.timezone.localize(datetime.now())
        self.nowUTC = datetime.utcnow().replace(tzinfo=None)

        self.sun_data = sun.sun(self.location.observer, date=self.now.date(), tzinfo=self.timezone)
        self.sunrise_azimuth = sun.azimuth(self.location.observer, self.sun_data['sunrise'])
        self.sunset_azimuth = sun.azimuth(self.location.observer, self.sun_data['sunset'])
        self.sun_azimuth = sun.azimuth(self.location.observer, self.now)
        self.sun_elevation = sun.elevation(self.location.observer, self.now)

        self.degs = []
        for i in range(0, 24, HOURS):
            hour_time = self.timezone.localize(datetime.combine(date.today(), time(i)))
            a = sun.azimuth(self.location.observer, hour_time)
            self.degs.append(float(a) if a is not None else 0)

        self.moon_info = pylunar.MoonInfo(self.decdeg2dms(conf.latitude), self.decdeg2dms(conf.longitude))
        self.moon_info.update(self.nowUTC)
        self.moon_azimuth = self.moon_info.azimuth()
        self.moon_elevation = self.moon_info.altitude()

        self.elevation = self.sun_elevation if self.sun_elevation > 0 else self.moon_elevation

    def refresh(self):
        self.now = self.timezone.localize(datetime.now())
        self.nowUTC = datetime.utcnow().replace(tzinfo=None)
        self.sun_data = sun.sun(self.location.observer, date=self.now.date(), tzinfo=self.timezone)
        self.sunrise_azimuth = sun.azimuth(self.location.observer, self.sun_data['sunrise'])
        self.sunset_azimuth = sun.azimuth(self.location.observer, self.sun_data['sunset'])
        self.sun_azimuth = sun.azimuth(self.location.observer, self.now)
        self.sun_elevation = sun.elevation(self.location.observer, self.now)
        self.moon_info.update(self.nowUTC)
        self.moon_azimuth = self.moon_info.azimuth()
        self.moon_elevation = self.moon_info.altitude()
        self.elevation = self.sun_elevation if self.sun_elevation > 0 else self.moon_elevation

    def decdeg2dms(self, dd):
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
        return (degrees, minutes, seconds)

    def degrees_to_point(self, d, r):
        coordinates = {'x': 0, 'y': 0}
        cx = WIDTH / 2
        cy = HEIGHT / 2
        d2 = 180 - d
        coordinates['x'] = cx + math.sin(math.radians(d2)) * r
        coordinates['y'] = cy + math.cos(math.radians(d2)) * r
        return coordinates

    def generate_path(self, stroke, fill, points, attrs=None):
        p = ''
        p += f'<path stroke="{stroke}" stroke-width="{STROKE_WIDTH}" fill="{fill}" '
        if attrs is not None:
            p += f' {attrs} '
        p += ' d="'
        for idx, point in enumerate(points):
            if idx == 0:
                p += f'M{point["x"]} {point["y"]}'
            else:
                p += f' L{point["x"]} {point["y"]}'
        p += '" />'
        return p

    def generate_arc(self, dist, stroke, fill, start, end, attrs=None):
        p = ''
        try:
            angle = end - start
            if angle < 0:
                angle = 360 + angle

            start_pt = self.degrees_to_point(start, dist)
            end_pt = self.degrees_to_point(end, dist)

            p += f'<path d="M{start_pt["x"]} {start_pt["y"]} '
            p += f'A{dist} {dist} 0 '
            p += '0 1 ' if angle < 180 else '1 1 '
            p += f'{end_pt["x"]} {end_pt["y"]}"'
            p += f' stroke="{stroke}"'
            if fill is not None:
                p += f' fill="{fill}" '
            else:
                p += ' fill="none" '
            if attrs is not None:
                p += f' {attrs} '
            else:
                p += f' stroke-width="{STROKE_WIDTH}"'
            p += ' />'
        except Exception:
            p = ''
        return p

    def generate_svg(self):
        sun_pos = self.degrees_to_point(self.sun_azimuth, WIDTH / 2)
        moon_pos = self.degrees_to_point(self.moon_azimuth, WIDTH / 2)

        if self.sun_elevation > 0:
            angle_pos = sun_pos
            real_pos = self.degrees_to_point(self.sun_azimuth, 10000)
        else:
            angle_pos = moon_pos
            real_pos = self.degrees_to_point(self.moon_azimuth, 10000)

        min_point = -1
        max_point = -1
        min_angle = 999
        max_angle = -999

        shape = [dict(p) for p in SHAPE]  # copy

        for i, point in enumerate(shape):
            angle = -math.degrees(math.atan2(point['y'] - real_pos['y'], point['x'] - real_pos['x']))
            distance = math.sqrt((angle_pos['y'] - point['y']) ** 2 + (angle_pos['x'] - point['x']) ** 2)

            if angle < min_angle:
                min_angle = angle
                min_point = i
            if angle > max_angle:
                max_angle = angle
                max_point = i

            point['angle'] = angle
            point['distance'] = distance

        # split into two sides
        i = min_point
        k = 0
        side1_distance = 0
        side2_distance = 0
        side1_done = False
        side2_done = False
        side1 = []
        side2 = []

        while True:
            if not side1_done:
                side1_distance += shape[i]['distance']
                if i != min_point and i != max_point:
                    shape[i]['side'] = 1
                if i == max_point:
                    side1_done = True
                side1.append({'x': shape[i]['x'], 'y': shape[i]['y']})
            else:
                side2_distance += shape[i]['distance']
                if i != min_point and i != max_point:
                    shape[i]['side'] = 2
                if i == min_point:
                    side2_done = True
                side2.append({'x': shape[i]['x'], 'y': shape[i]['y']})

            i += 1
            if i > len(shape) - 1:
                i = 0

            if side1_done and side2_done:
                break

            k += 1
            if k == 20:
                break

        svg = '<?xml version="1.0" encoding="utf-8"?>'
        svg += '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'
        svg += '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="-10 -10 120 120" xml:space="preserve">'

        # background disk
        svg += f'<circle cx="{WIDTH/2}" cy="{HEIGHT/2}" r="{WIDTH/2-1}" fill="{BG_COLOR}"/>'

        # shadow polygon
        min_shadow_x = shape[min_point]['x'] + WIDTH * math.cos(math.radians(min_angle))
        min_shadow_y = shape[min_point]['y'] - HEIGHT * math.sin(math.radians(min_angle))
        max_shadow_x = shape[max_point]['x'] + WIDTH * math.cos(math.radians(max_angle))
        max_shadow_y = shape[max_point]['y'] - HEIGHT * math.sin(math.radians(max_angle))

        shadow_poly = [{'x': max_shadow_x, 'y': max_shadow_y}] + side2 + [{'x': min_shadow_x, 'y': min_shadow_y}]

        svg += '<defs><mask id="shadowMask">'
        svg += '  <rect width="100%" height="100%" fill="black"/>'
        svg += f'  <circle cx="{WIDTH/2}" cy="{HEIGHT/2}" r="{WIDTH/2-1}" fill="white"/>'
        svg += '</mask></defs>'

        # house
        svg += self.generate_path('none', PRIMARY_COLOR, shape)

        shadow_svg = self.generate_path('none', 'black', shadow_poly, 'mask="url(#shadowMask)" fill-opacity="0.5"')

        # lit edge based on elevation
        if self.elevation > 0:
            svg += self.generate_path(LIGHT_COLOR, 'none', side1)
            svg += shadow_svg
        else:
            svg += self.generate_path(PRIMARY_COLOR, 'none', side2)

        # day-night arcs
        svg += self.generate_arc(WIDTH/2, PRIMARY_COLOR, 'none', self.sunset_azimuth, self.sunrise_azimuth)
        svg += self.generate_arc(WIDTH/2, LIGHT_COLOR, 'none', self.sunrise_azimuth, self.sunset_azimuth)

        # sunrise/sunset tick marks
        svg += self.generate_path(LIGHT_COLOR, 'none', [self.degrees_to_point(self.sunrise_azimuth, WIDTH/2-2), self.degrees_to_point(self.sunrise_azimuth, WIDTH/2+2)])
        svg += self.generate_path(LIGHT_COLOR, 'none', [self.degrees_to_point(self.sunset_azimuth, WIDTH/2-2), self.degrees_to_point(self.sunset_azimuth, WIDTH/2+2)])

        # hourly arcs around the disk
        for i in range(0, len(self.degs)):
            j = 0 if i == len(self.degs) - 1 else i + 1
            if i % 2 == 0:
                svg += self.generate_arc(WIDTH/2+8, PRIMARY_COLOR, 'none', self.degs[i], self.degs[j], 'stroke-width="3" stroke-opacity="0.2"')
            else:
                svg += self.generate_arc(WIDTH/2+8, PRIMARY_COLOR, 'none', self.degs[i], self.degs[j], 'stroke-width="3" ')

        # 00:00 and 12:00 ticks
        svg += self.generate_path(LIGHT_COLOR, 'none', [self.degrees_to_point(self.degs[0], WIDTH/2+5), self.degrees_to_point(self.degs[0], WIDTH/2+11)])
        mid_index = len(self.degs) // 2
        svg += self.generate_path(LIGHT_COLOR, 'none', [self.degrees_to_point(self.degs[mid_index], WIDTH/2+5), self.degrees_to_point(self.degs[mid_index], WIDTH/2+11)])

        # sun marker
        if self.sun_elevation > 0:
            svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS}" stroke="none" stroke-width="0" fill="{SUN_COLOR}55" />'
            svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS-1}" stroke="none" stroke-width="0" fill="{SUN_COLOR}99" />'
            svg += f'<circle cx="{sun_pos["x"]}" cy="{sun_pos["y"]}" r="{SUN_RADIUS-2}" stroke="{SUN_COLOR}" stroke-width="0" fill="{SUN_COLOR}" />'

        svg += '</svg>'

        # write to output path
        try:
            folder = os.path.dirname(self.conf.output_path)
            if folder and not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
            with open(self.conf.output_path, 'w', encoding='utf-8') as f:
                f.write(svg)
        except Exception as e:
            # Let caller log the error; silently fail here
            raise e
