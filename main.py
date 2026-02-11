from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from model_master import Lokasi, Cuaca, VsText, WeatherDesc, WeatherDescEn, cuaca_to_dict, parse_cuaca_matrix, parse_cuaca_matrix_for_listcuaca
from typing import List, Optional   
import requests
import html
import json

app = FastAPI()

@app.get("/")
def prakiraan_cuaca():
    api_url = "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=64.71.01.1001"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json() 
        # parse Lokasi using pydantic (support v2/v1)
        lokasi_raw = data.get("lokasi", {})
        try:
            loc = Lokasi.model_validate(lokasi_raw)
        except Exception:
            try:
                loc = Lokasi.parse_obj(lokasi_raw)
            except Exception:
                loc = Lokasi(**lokasi_raw)

        cuaca_raw = data.get("data", [{}])[0].get("cuaca", [[]])
        list_cuaca = parse_cuaca_matrix_for_listcuaca(cuaca_raw)

        def serialize_model(m):
            if hasattr(m, "model_dump"):
                return m.model_dump()
            if hasattr(m, "dict"):
                return m.dict()
            try:
                return vars(m)
            except Exception:
                return None

        cuaca_serialized = {
            "now": [cuaca_to_dict(c) for c in (list_cuaca.now or [])],
            "day1": [cuaca_to_dict(c) for c in (list_cuaca.day1 or [])],
            "day2": [cuaca_to_dict(c) for c in (list_cuaca.day2 or [])],
        }

        return JSONResponse(content={
            "lokasi": serialize_model(loc),
            "cuaca": cuaca_serialized
        })
    except Exception as e:
        return Response(
            content=f"ERROR: Gagal mengambil data. ({e})",
            media_type="text/plain"
        )
 
    # lokasi = data.get("lokasi", {})
    # if "desa" in lokasi and "kecamatan" in lokasi:
    #     html_content += f"<h2>Desa/Kelurahan: {html.escape(lokasi.get('desa','N/A'))}</h2>"
    #     html_content += "<p>"
    #     html_content += f"Kecamatan: {html.escape(lokasi.get('kecamatan','N/A'))}<br>"
    #     html_content += f"Kota/Kabupaten: {html.escape(lokasi.get('kotkab','N/A'))}<br>"
    #     html_content += f"Provinsi: {html.escape(lokasi.get('provinsi','N/A'))}<br>"
    #     html_content += f"Koordinat Latitude: {html.escape(lokasi.get('lat','N/A'))}, Longitude: {html.escape(lokasi.get('lon','N/A'))}<br>"
    #     html_content += f"Timezone: {html.escape(lokasi.get('timezone','N/A'))}<br>"
    #     html_content += "</p>"
    # else:
    #     html_content += "<h2>Lokasi Tidak Ditemukan</h2>"

    # html_content += "<h3>Detail Prakiraan Cuaca:</h3>"
    # cuaca_data = data.get("data", [{}])[0].get("cuaca", [])
    # if isinstance(cuaca_data, list):
    #     for index_hari, prakiraan_harian in enumerate(cuaca_data):
    #         html_content += f"<h4>Hari ke-{index_hari+1}</h4><ul>"
    #         if isinstance(prakiraan_harian, list):
    #             for prakiraan in prakiraan_harian:
    #                 waktu_lokal = html.escape(prakiraan.get("local_datetime", "N/A"))
    #                 deskripsi = html.escape(prakiraan.get("weather_desc", "N/A"))
    #                 alt_text = html.escape(prakiraan.get("weather_desc", "Ikon Cuaca"))
    #                 suhu = html.escape(prakiraan.get("t", "N/A"))
    #                 kelembapan = html.escape(prakiraan.get("hu", "N/A"))
    #                 kec_angin = html.escape(prakiraan.get("ws", "N/A"))
    #                 arah_angin = html.escape(prakiraan.get("wd", "N/A"))
    #                 jarak_pandang = html.escape(prakiraan.get("vs_text", "N/A"))

    #                 raw_img_url = prakiraan.get("image", "")
    #                 img_url_processed = raw_img_url.replace(" ", "%20") if raw_img_url else ""

    #                 html_content += "<li>"
    #                 html_content += f"<strong>Jam:</strong> {waktu_lokal} | "
    #                 html_content += f"<strong>Cuaca:</strong> {deskripsi} "
    #                 if img_url_processed:
    #                     html_content += f'<img src="{img_url_processed}" alt="{alt_text}" title="{alt_text}"> | '
    #                 html_content += f"<strong>Suhu:</strong> {suhu}°C | "
    #                 html_content += f"<strong>Kelembapan:</strong> {kelembapan}% | "
    #                 html_content += f"<strong>Kec. Angin:</strong> {kec_angin}km/j | "
    #                 html_content += f"<strong>Arah Angin:</strong> dari {arah_angin} | "
    #                 html_content += f"<strong>Jarak Pandang:</strong> {jarak_pandang}"
    #                 html_content += "</li>"
    #         else:
    #             html_content += "<li>Data tidak valid.</li>"
    #         html_content += "</ul>"
    # else:
    #     html_content += "<p>Struktur data prakiraan cuaca tidak ditemukan.</p>"

    # html_content += "</body></html>"
