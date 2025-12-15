# Shadow SVG Generator
![Example Day](https://raw.githubusercontent.com/clmun/Shadow/main/images/Example_day.png)

---

## 📄 Shadow SVG Generator
A Home Assistant custom component (via HACS) that generates dynamic SVG graphics showing illuminated sides and realistic shadows based on the Sun or Moon position.  
The SVG image illustrates where the Sun is currently positioned and which side of the house is facing the Sun.  
The integration automatically uses data from Home Assistant (`latitude`, `longitude`, `elevation`, `time_zone`).

---
## 🌟 Features
- House shadow representation based on real-time Sun or Moon position.
- Positioning based on user-defined location (town).
- Customizable colors, dimensions, and shapes via `shadow_config.py`.
- Easy integration with Home Assistant via HACS or manual installation.
- Configurable update intervals for real-time shadow representation.
- Output SVG file accessible via Home Assistant's web server.
- Lightweight and efficient, suitable for various Home Assistant setups.
--- 
## Lovelace Example
You can display the generated SVG in your Lovelace dashboard using the Picture Entity card or Picture card.
```yaml
type: picture-entity
entity: sensor.shadow_elevation
image: /local/shadow.svg
```
![Lovelace Example](https://raw.githubusercontent.com/clmun/Shadow/main/images/Example_day.png)
![Lovelace Example](https://raw.githubusercontent.com/clmun/Shadow/main/images/Example_night_w_moon.png)
---
## 🚀 Installation
### Add the Shadow integration via HACS: ###
1. In HACS, go to "Integrations".
2. Click on the three dots in the top right corner and select "Custom Repositories".
3. Enter the repository URL: https://github.com/clmun/Shadow
4. Select "Integration" as the category and click "Add".
5. Restart Home Assistant.
### Add the Shadow integration manually: ###
1. Download the component from the GitHub repository: https://github.com/clmun/Shadow
2. Extract the downloaded files.
3. Create a directory named `shadow` in your Home Assistant `custom_components` folder if it doesn't already exist.
4. Copy the extracted files into the `custom_components/shadow` directory.
5. In `configuration.yaml`, add the Shadow sensor configuration as described above.
6. Save the file and restart Home Assistant.
---
## 🔧 Setup Instructions
1. Search for "Shadow" in HACS and install it.
2. In configuration.yaml, add the Shadow sensor configuration as described below.
```yaml
sensor:
  - platform: shadow
    name: Shadow Elevation
    town: Sibiu
    output_path: /config/www/shadow.svg
    update_interval: 60
```
3. All settings needed for generating the picture (.svg format) are stored in `config.py` (colors, dimensions, shape coordinates).
Minimal example configuration:
 ```python
WIDTH = 100
HEIGHT = 100
BG_COLOR = "black" # Background color
PRIMARY_COLOR = "green" # Color of the shape
LIGHT_COLOR = "yellow" # Color of the illuminated side
SUN_RADIUS = 4 # Radius of the sun
SUN_COLOR = "orange" # Color of the sun
MOON_RADIUS = 4 # Radius of the moon
MOON_COLOR = "gray" # Color of the moon

SHAPE = [
    {'x': 40, 'y': 40}, # Bottom-left corner
    {'x': 60, 'y': 40}, # Bottom-right corner
    {'x': 60, 'y': 60}, # Top-right corner
    {'x': 40, 'y': 60}  # Top-left corner
]
```
4. After configuring the `shadow_config.py` file, restart Home Assistant.
5. The SVG file will be generated at the specified output path: `/config/www/shadow.svg`.
6. Access the SVG file via Home Assistant's web server at `http://<your-home-assistant-url>/local/shadow.svg`.
7. You can then use this SVG in your Lovelace dashboard or other places within Home Assistant.
8. Somehow the picture is not updating in the picture card. A solution is to add it as a camera entity using the local file camera integration: 
```yaml
camera:
  - platform: local_file
    name: Shadow Camera
    file_path: /config/www/shadow.svg
    content_type: image/svg+xml
```
Then use the camera entity in the picture card:
```yaml
type: picture-entity
entity: camera.shadow_camera
```
or you can do this via UI.
  
9. Enjoy your dynamic shadow SVG graphics!
---
## ⚙️ How to generate the points for shape
To define the shape of your house in the SVG, you need to specify the coordinates of its corners in the `SHAPE` list within the `shadow_config.py` file. Each corner is represented as a dictionary with `x` and `y` keys.
Here's how to generate the points for your shape:
1. **Determine the Shape**: Decide on the shape you want to represent (e.g., rectangle, polygon).
2. **Coordinate System**: The SVG coordinate system starts in the top-left corner (0,0). The `x` coordinate increases to the right, and the `y` coordinate increases downward.
3. **Calculate Points**: For each corner of your shape, calculate its `x` and `y` coordinates based on the desired dimensions and position within the SVG canvas.
4. **Create Point Dictionaries**: For each corner, create a dictionary with the calculated `x` and `y` values.
5. **Use the Following Methods to Get Coordinates**:
   - **Graph Paper Method**:
     1. Print a piece of graph paper.
     2. Draw the shape of your house on the graph paper.
     3. Count the squares to determine the `x` and `y` coordinates of each corner.
     4. Scale the coordinates if necessary to fit within the SVG dimensions. (SVG size is 100x100 by default, so you might need to scale down your measurements accordingly.)
   - **Google Maps Method**:
     1. Open Google Maps and locate your house.
     2. Use the "Measure distance" tool to find the coordinates of each corner of your house. (right-click on the map to access it)
     3. Copy the latitude and longitude coordinates for each corner and put them into the script from tools/coords_to_shape.py
     4. Run the script and this will generate the shadow_config.py file with the SHAPE variable filled in. Also will generate a shadow.svg file that you can use to see how it looks like.
     5. Shadow_config.py will be generated in the same folder where you run the script. You have to copy it to the custom_components/shadow folder.
## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 📝 Disclaimer

This integration is provided "as is" without warranty of any kind. Use at your own risk
. The author is not responsible for any damage or data loss that may occur from using this integration.
By using this integration, you agree to the terms of this disclaimer.


## Inspiration
This integration was inspired by the OpenHAB community and adapted for Home Assistant.

When I started with home automation, 10 years ago, I've started with OpenHAB and found this script and this idea fascinating.

Later, when I moved to Home Assistant, I kept the script and had the shadow running for all this time, but always waited for somebody more experienced to bring this to Home Assistant.

Well, in the end, with a big help from AI, I did it myself and share it now with the community.

So many thanks to the OpenHAB community for the original idea! And big thanks to AI for helping me with the adaptation to Home Assistant.:) (this line was generated by AI :) )

## 🙏 Acknowledgements
- Thanks to the OpenHAB community for the original idea and script.https://community.openhab.org/t/show-current-sun-position-and-shadow-of-house-generate-svg/34764
- Thanks to the Home Assistant community for continuous support and inspiration.
- Thanks to all contributors and users who provide feedback and help improve this integration.

## 📧 Contact
For questions, suggestions, or support, please reach out via the Home Assistant Community Forums or GitHub Issues page.
- Home Assistant Community Forums: https://community.home-assistant.io/
- GitHub Issues: https://github.com/clmun/Shadow/issues

## ☕ Support me
If you liked this integration and want to support the work done, **buy me a coffee!**  🫶

It costs nothing, and your contribution helps the future development of the project. 🙌  

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20the%20developer-orange?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/clmun01c)

Thanks for the support, I appreciate any gesture of support! 🤗
