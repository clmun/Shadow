from shadow_core import ShadowConfig, Shadow

def main():
    # Config de test – poți schimba coordonatele
    conf = ShadowConfig(
        latitude=45.8,          # Sibiu
        longitude=24.1,
        altitude=400,
        timezone="Europe/Bucharest",
        town="Sibiu",
        output_path="shadow_test.svg"
    )

    shadow = Shadow(conf)

    # Reîmprospătăm calculele
    shadow.refresh()

    # Generăm SVG
    shadow.generate_svg()

    # Printăm câteva valori pentru verificare
    print("Town:", conf.town)
    print("Elevation:", shadow.elevation)
    print("Sun azimuth:", shadow.sun_azimuth)
    print("Sun elevation:", shadow.sun_elevation)
    print("Moon azimuth:", shadow.moon_azimuth)
    print("Moon elevation:", shadow.moon_elevation)
    print("SVG file generated at:", conf.output_path)

if __name__ == "__main__":
    main()

