import plotly.graph_objects as go
import numpy as np
from PIL import Image
import os

def textured_earth_mesh(fig):
    try:
        texture_path = os.path.join(os.path.dirname(__file__), "land_ocean_ice_2048.png")
        img = Image.open(texture_path)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)  # Flip for correct orientation
        img_data = np.asarray(img) / 255.0  # Normalize

        # Generate spherical coordinates
        lat_steps = img_data.shape[0]
        lon_steps = img_data.shape[1]
        lats = np.linspace(-np.pi / 2, np.pi / 2, lat_steps)
        lons = np.linspace(0, 2 * np.pi, lon_steps)
        lons, lats = np.meshgrid(lons, lats)

        r = 6371  # Earth's radius in km (approx.)
        x = r * np.cos(lats) * np.cos(lons)
        y = r * np.cos(lats) * np.sin(lons)
        z = r * np.sin(lats)

        surfacecolor = np.mean(img_data[:, :, :3], axis=2)  # grayscale for shading

        fig.add_trace(go.Surface(
            x=x, y=y, z=z,
            surfacecolor=surfacecolor,
            colorscale='gray',
            cmin=0, cmax=1,
            showscale=False,
            lighting=dict(ambient=0.8, diffuse=0.5),
            hoverinfo='skip',
            name="Earth"
        ))
    except Exception as e:
        print(f"Failed to render textured Earth: {e}")
