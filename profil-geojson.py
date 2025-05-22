#%%
import streamlit as st
import json
import ezdxf
from ezdxf.enums import TextEntityAlignment
import math
from pyproj import Geod
import tempfile
import os

st.title("Generator profilu z GeoJSON do DXF")
st.subheader("Copyright przemeks505@gmail.com")
uploaded_file = st.file_uploader("Prześlij plik GeoJSON", type=["geojson"])

if uploaded_file:
    geojson = json.load(uploaded_file)

    coordinates = geojson["features"][0]["geometry"]["coordinates"]
    geod = Geod(ellps="WGS84")
    points = []
    distance = 0.0

    for i, coord in enumerate(coordinates):
        lon, lat, z = coord
        if i == 0:
            points.append({"x": 0.0, "z": z})
            prev_lon, prev_lat = lon, lat
        else:
            az12, az21, dist = geod.inv(prev_lon, prev_lat, lon, lat)
            distance += dist
            points.append({"x": distance, "z": z})
            prev_lon, prev_lat = lon, lat

    # Tworzenie dokumentu DXF
    doc = ezdxf.new()
    msp = doc.modelspace()

    profile_points = [(p["x"], p["z"]) for p in points]
    msp.add_lwpolyline(profile_points, dxfattribs={"layer": "PROFIL"})

    z_min = math.floor(min(p["z"] for p in points))
    z_max = math.ceil(max(p["z"] for p in points))
    x_start = min(p["x"] for p in points)
    x_end = max(p["x"] for p in points)

    for z in range(z_min, z_max + 1):
        msp.add_line((x_start, z), (x_end, z), dxfattribs={"layer": "SIATKA", "linetype": "DASHED"})
        msp.add_text(
            f"{z:.2f}",
            dxfattribs={"height": 0.25, "layer": "OPISY"}
        ).set_placement((x_start - 2, z), align=TextEntityAlignment.LEFT)

    # Zapis do pliku tymczasowego
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
        doc.saveas(tmp_file.name)
        dxf_path = tmp_file.name

    st.success("Plik DXF został wygenerowany.")
    with open(dxf_path, "rb") as f:
        st.download_button("📥 Pobierz plik DXF", f, file_name="profil.dxf")

    # Usuwamy plik tymczasowy po pobraniu (opcjonalnie)
    # os.remove(dxf_path)
