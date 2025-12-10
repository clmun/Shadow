from datetime import datetime
from shadow_core import Shadow, ShadowConfig  # presupunând că fișierul tău se numește shadow_core.py

def main():
    # Config pentru locația ta (ex. Sibiu, România)
    conf = ShadowConfig(
        latitude=45.79,          # latitudine
        longitude=24.15,         # longitudine
        altitude=400,            # altitudine în metri
        timezone="Europe/Bucharest",
        town="Sibiu",
        output_path="test_shadow.svg"
    )

    # Instanțiere obiect Shadow
    shadow = Shadow(conf)

    # Construiește SVG
    svg_content = shadow._build_svg()

    # Scrie fișierul
    with open(conf.output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"SVG salvat ca {conf.output_path} — deschide-l în browser!")

if __name__ == "__main__":
    main()
