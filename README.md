# Shadow

Shadow este o integrare Home Assistant care:
- calculează azimutul și elevația soarelui și lunii pentru o locație configurată
- generează un SVG cu umbre pe un contur de casă 100x100
- expune un senzor cu stare `elevation` (pozitiv: zi, negativ: noapte) și atribute utile
- oferă un serviciu pentru re-generarea SVG la cerere

Integrarea este disponibilă via HACS ca custom repo.

## Instalare

1. Copiază folderul `custom_components/shadow` în `<config>/custom_components/`.
2. Sau adaugă repo-ul ca Custom Repository în HACS și instalează integrarea.
3. Adaugă în `configuration.yaml`:

## Configurare

Integrarea folosește automat datele din Home Assistant (`latitude`, `longitude`, `elevation`, `time_zone`).

Exemplu minimal:

```yaml
sensor:
  - platform: shadow
    name: Shadow Elevation
    town: Sibiu
    output_path: /config/www/shadow.svg
    update_interval: 60
```

## ☕ Susține dezvoltatorul

Dacă ți-a plăcut această integrare și vrei să sprijini munca depusă, **invită-mă la o cafea**! 🫶  
Nu costă nimic, iar contribuția ta ajută la dezvoltarea viitoare a proiectului. 🙌  

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Susține%20dezvoltatorul-orange?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/clmun01c)

Mulțumesc pentru sprijin și apreciez fiecare gest de susținere! 🤗
