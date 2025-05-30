#%%
import streamlit as st
import json
import ezdxf
from ezdxf.enums import TextEntityAlignment
import math
from pyproj import Geod
import tempfile

st.image('logo.png', caption="ⓒ przemeks505@gmail.com")

uploaded_file = st.file_uploader("Prześlij plik GeoJSON", type=["geojson"])

if uploaded_file:
    try:
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

    except Exception as e:
        st.error("Błąd: Niepoprawny plik GeoJSON. Upewnij się, że przesłany plik pochodzi z narzędzia 'Profil podłużny' na stronie https://polska.e-mapa.net.")

with st.expander("Zobacz instrukcję."):
    st.markdown("""
Szybki profil działki z NMT – eksport do DXF

Krok 1: Wejdź na stronę
🔗 https://polska.e-mapa.net

Krok 2: Wygeneruj profil terenu
Wyszukaj interesującą Cię działkę.
W menu narzędzi wybierz „Profil podłużny”.
Zaznacz linię profilu na mapie i kliknij „Generuj”.

Krok 3: Pobierz plik GeoJSON
Po wygenerowaniu profilu kliknij przycisk „Pobierz GeoJSON (WGS84)”.
Zapisz plik na dysku – będzie on miał nazwę profil.geojson.
Pobrany plik powinien mieć taką strukturę:\n
{"name":"demo.geojson","type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"LineString","coordinates":[[20.508315289026996,50.45245033244687,199.68], [20.508320567942125,50.452467736108744,199.45], [20.508325846861265,50.45248513977032,199.39], [20.508331125784412,50.452502543431535,198.91], [20.508336404711564,50.452519947092455,198.84], [20.508341683642726,50.45253735075303,198.29],

Krok 4: Skorzystaj z konwertera online
🔗 Przejdź na stronę: https://geojsonprofil.streamlit.app

Przeciągnij plik profil.geojson na stronę lub użyj przycisku „Wybierz plik”, aby go załadować.

Krok 5: Pobierz gotowy plik DXF
Kliknij przycisk „Pobierz DXF”.
Plik profil.dxf zostanie pobrany automatycznie i będzie wyglądał jak
rysunek poniżej.
""")
    st.image('wynik.png', caption="ⓒ przemeks505@gmail.com")

