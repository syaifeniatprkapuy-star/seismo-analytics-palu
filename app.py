"""
SEISMO ANALYTICS · BMKG STASIUN GEOFISIKA KELAS I PALU
Dasbor analisis katalog gempa bumi (Streamlit + Plotly)

Jalankan:
    pip install -r requirements.txt
    streamlit run app.py
"""
import io
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Beri petunjuk ramah jika file dijalankan dengan "python app.py" / Code Runner
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    try:
        _ctx = get_script_run_ctx(suppress_warning=True)
    except TypeError:
        _ctx = get_script_run_ctx()
    if _ctx is None:
        print("\nAplikasi ini harus dijalankan dengan Streamlit, bukan tombol Run Python.\n"
              "Buka terminal di folder aplikasi, lalu ketik:\n\n"
              "    python -m streamlit run app.py\n")
        raise SystemExit
except ImportError:
    pass

# =========================================================
# 1. KONFIGURASI
# =========================================================
st.set_page_config(
    page_title="Seismo Analytics · BMKG Palu",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALU_LAT, PALU_LON = -0.8917, 119.8707

BIRU, CYAN, KUNING = "#1E6BFF", "#22D3EE", "#FFC72C"
ORANYE, MERAH, HIJAU = "#FF8A3D", "#FF4D5E", "#34D399"
SKALA_MAG = [[0, CYAN], [0.35, BIRU], [0.6, KUNING], [0.8, ORANYE], [1, MERAH]]


def _versi():
    try:
        return tuple(int(p) for p in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


# Streamlit baru memakai width="stretch", versi lama use_container_width
STRETCH = {"width": "stretch"} if _versi() >= (1, 50) else {"use_container_width": True}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Inter:wght@400;500;600&display=swap');

:root{
  --biru:#1E6BFF; --cyan:#22D3EE; --kuning:#FFC72C; --oranye:#FF8A3D;
  --merah:#FF4D5E; --hijau:#34D399;
  --teks:#DCE8FF; --teks2:#8FA8D0; --kartu:rgba(255,255,255,.05);
  --garis:rgba(140,180,255,.16);
}
html, body, [class*="css"], .stApp { font-family:'Inter',sans-serif; }

.stApp{
  background-color:#050E24;
  background-image:
    radial-gradient(ellipse 70% 50% at 8% 0%, rgba(30,107,255,.38), transparent 60%),
    radial-gradient(ellipse 60% 45% at 100% 8%, rgba(34,211,238,.18), transparent 60%),
    radial-gradient(ellipse 60% 50% at 92% 100%, rgba(255,199,44,.10), transparent 60%),
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size:auto,auto,auto,44px 44px,44px 44px;
  background-attachment:fixed;
}
header[data-testid="stHeader"]{ background:transparent; }
#MainMenu, footer{ visibility:hidden; }
.block-container{ padding-top:1.4rem; max-width:1240px; }

/* ---------- Judul seksi ---------- */
.sec{
  font-family:'Sora',sans-serif; font-weight:700; font-size:1.2rem;
  margin:1.6rem 0 .8rem; padding-left:.8rem; color:#fff;
  border-left:4px solid var(--kuning);
}
.sec small{ color:var(--teks2); font-weight:500; font-size:.8rem; margin-left:.5rem; }

/* ---------- Ticker ---------- */
.ticker{
  overflow:hidden; white-space:nowrap; border-radius:12px; margin-bottom:1rem;
  background:rgba(255,199,44,.08); border:1px solid rgba(255,199,44,.28);
  padding:.55rem 0; color:#FFE9A8; font-size:.88rem;
}
.ticker-isi{ display:inline-block; padding-left:100%; animation:geser 70s linear infinite; }
.ticker-isi span{ margin-right:3.5rem; }
@keyframes geser{ to{ transform:translateX(-100%); } }

/* ---------- Hero ---------- */
.hero{
  position:relative; border-radius:26px; padding:2.2rem 2.4rem 0; overflow:hidden;
  background:linear-gradient(135deg, rgba(16,52,120,.92), rgba(6,22,56,.94));
  border:1px solid rgba(120,170,255,.28);
  box-shadow:0 30px 80px rgba(0,20,80,.55), inset 0 1px 0 rgba(255,255,255,.1);
  margin-bottom:1.4rem;
}
.hero-top{ display:grid; grid-template-columns:1.6fr 1fr; gap:1.5rem; align-items:center; }
.baris-lencana{ display:flex; flex-wrap:wrap; gap:.7rem; align-items:center; margin-bottom:1rem; }
.logo{
  font-family:'Sora',sans-serif; font-weight:800; letter-spacing:.08em; font-size:.95rem;
  padding:.35rem .9rem; border-radius:10px; color:#06204F;
  background:linear-gradient(135deg,#FFC72C,#FFE08A);
  box-shadow:0 6px 18px rgba(255,199,44,.35);
}
.live{
  display:inline-flex; align-items:center; gap:.5rem; font-size:.85rem; font-weight:600;
  color:#BFEFFF; padding:.35rem .9rem; border-radius:999px;
  background:rgba(34,211,238,.12); border:1px solid rgba(34,211,238,.4);
}
.live i{ width:.55rem; height:.55rem; border-radius:50%; background:var(--hijau);
  box-shadow:0 0 0 0 rgba(52,211,153,.7); animation:denyut 1.6s infinite; }
@keyframes denyut{ 70%{ box-shadow:0 0 0 10px rgba(52,211,153,0); } 100%{ box-shadow:0 0 0 0 rgba(52,211,153,0); } }
.judul{
  font-family:'Sora',sans-serif; font-weight:800; font-size:3.3rem; line-height:1.02;
  letter-spacing:-.03em; color:#fff; margin:.2rem 0 .8rem;
}
.judul em{ font-style:normal;
  background:linear-gradient(90deg,var(--kuning),var(--oranye)); -webkit-background-clip:text;
  background-clip:text; color:transparent; }
.sub{ max-width:40rem; font-size:1.02rem; line-height:1.65; color:#B7CBEA; margin-bottom:1rem; }
.sub b{ color:#fff; }
.magang{ display:inline-block; font-size:.88rem; font-weight:600; color:#FFD9B8;
  background:rgba(255,138,61,.14); border:1px solid rgba(255,138,61,.5);
  border-radius:999px; padding:.3rem .95rem; }

.ripple{ position:relative; height:230px; display:grid; place-items:center; }
.ripple span{ position:absolute; width:30px; height:30px; border-radius:50%;
  border:2px solid rgba(34,211,238,.75); animation:riak 3.6s ease-out infinite; }
.ripple span:nth-child(2){ animation-delay:1.2s; }
.ripple span:nth-child(3){ animation-delay:2.4s; }
@keyframes riak{ from{ transform:scale(1); opacity:.95; } to{ transform:scale(8.5); opacity:0; } }
.ripple b{ z-index:2; width:16px; height:16px; border-radius:50%; background:var(--kuning);
  box-shadow:0 0 0 4px rgba(255,199,44,.25), 0 0 32px var(--kuning); }
.ripple em{ position:absolute; bottom:0; font-style:normal; font-size:.78rem; color:#9FC0F0;
  letter-spacing:.04em; }

.info-grid{ display:grid; grid-template-columns:1.1fr 1fr; gap:1rem; margin:1.4rem 0 1rem; }
.panel{ background:rgba(255,255,255,.06); border:1px solid var(--garis); border-radius:16px;
  padding:1rem 1.2rem; backdrop-filter:blur(6px); }
.panel h4{ font-family:'Sora',sans-serif; font-size:.9rem; font-weight:700; color:var(--cyan);
  margin:0 0 .6rem; letter-spacing:.02em; }
.anggota{ display:flex; justify-content:space-between; gap:1rem; padding:.38rem 0;
  border-bottom:1px solid rgba(255,255,255,.08); font-size:.93rem; color:#F2F7FF; }
.anggota:last-child{ border-bottom:none; }
.anggota span{ color:#8FB0DA; font-variant-numeric:tabular-nums; }
.instansi b{ display:block; color:#fff; font-size:1.02rem; line-height:1.4; margin-bottom:.35rem; }
.instansi p{ margin:0; font-size:.92rem; line-height:1.55; color:#B7CBEA; }
.hero svg{ display:block; width:100%; height:120px; margin-top:.4rem; }
.trace{ fill:none; stroke:var(--cyan); stroke-width:2; stroke-linejoin:round;
  stroke-dasharray:1; stroke-dashoffset:1; animation:gambar 3.4s ease-out forwards;
  filter:drop-shadow(0 0 6px rgba(34,211,238,.8)); }
@keyframes gambar{ to{ stroke-dashoffset:0; } }
@media (max-width:900px){
  .hero-top, .info-grid{ grid-template-columns:1fr; }
  .judul{ font-size:2.2rem; } .ripple{ display:none; }
}
@media (prefers-reduced-motion:reduce){
  .trace{ animation:none; stroke-dashoffset:0; }
  .ripple span, .ticker-isi, .live i{ animation:none; }
}

/* ---------- Kartu KPI ---------- */
.kpi-grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr)); gap:14px; margin:.4rem 0 1rem; }
.kpi{
  position:relative; overflow:hidden; border-radius:18px; padding:1.1rem 1.2rem;
  background:linear-gradient(160deg, rgba(255,255,255,.08), rgba(255,255,255,.03));
  border:1px solid var(--garis); transition:.3s;
}
.kpi::before{ content:""; position:absolute; inset:0 0 auto 0; height:3px; background:var(--acc); }
.kpi::after{ content:""; position:absolute; right:-30px; top:-30px; width:110px; height:110px;
  border-radius:50%; background:var(--acc); opacity:.13; filter:blur(18px); }
.kpi:hover{ transform:translateY(-5px); box-shadow:0 16px 36px rgba(0,0,0,.4); border-color:var(--acc); }
.kpi .ik{ font-size:1.4rem; margin-bottom:.35rem; }
.kpi .nl{ font-family:'Sora',sans-serif; font-weight:700; font-size:1.75rem; color:#fff; line-height:1.1; }
.kpi .lb{ color:var(--teks2); font-size:.82rem; margin-top:.3rem; }

.terkuat{
  display:grid; grid-template-columns:auto 1fr; gap:1.4rem; align-items:center;
  border-radius:20px; padding:1.3rem 1.6rem; margin:.4rem 0 1rem;
  background:linear-gradient(120deg, rgba(255,77,94,.20), rgba(255,138,61,.10) 55%, rgba(255,255,255,.03));
  border:1px solid rgba(255,77,94,.45);
}
.terkuat .besar{ font-family:'Sora',sans-serif; font-weight:800; font-size:3.2rem; color:#fff;
  text-shadow:0 0 28px rgba(255,77,94,.7); line-height:1; }
.terkuat .besar small{ display:block; font-size:.75rem; font-weight:600; color:#FFB7BE;
  letter-spacing:.12em; margin-bottom:.3rem; text-shadow:none; }
.terkuat p{ margin:0; color:#E3ECFF; line-height:1.7; font-size:.95rem; }
.terkuat p b{ color:#fff; }

.narasi{
  border-radius:16px; padding:1.1rem 1.3rem; line-height:1.75; color:#D5E3FA; font-size:.96rem;
  background:rgba(34,211,238,.07); border:1px solid rgba(34,211,238,.3);
}
.narasi b{ color:#fff; }
.chip{ display:inline-block; padding:.3rem .9rem; border-radius:999px; font-size:.82rem; font-weight:600;
  margin:.2rem .4rem .6rem 0; }
.chip.ok{ background:rgba(52,211,153,.14); border:1px solid rgba(52,211,153,.5); color:#8CF0C8; }
.chip.warn{ background:rgba(255,199,44,.12); border:1px solid rgba(255,199,44,.5); color:#FFE08A; }

/* ---------- Langkah ---------- */
.langkah{ background:var(--kartu); border:1px solid var(--garis); border-radius:18px;
  padding:1.2rem 1.3rem; height:100%; }
.langkah b{ font-family:'Sora',sans-serif; font-size:1rem; display:block; margin-bottom:.35rem; color:#fff; }
.langkah span{ color:#A9BEDF; font-size:.92rem; line-height:1.6; }
.nomor{ display:inline-flex; align-items:center; justify-content:center; width:1.9rem; height:1.9rem;
  border-radius:50%; background:linear-gradient(135deg,var(--kuning),var(--oranye)); color:#06204F;
  font-weight:800; font-size:.9rem; margin-bottom:.7rem; }

/* ---------- Komponen Streamlit ---------- */
[data-testid="stSidebar"]{ background:rgba(5,14,36,.88); backdrop-filter:blur(12px);
  border-right:1px solid var(--garis); }
[data-testid="stSidebar"] h2{ font-family:'Sora',sans-serif; font-size:1rem !important; color:var(--kuning); }
.sb-brand{ border-radius:14px; padding:.9rem 1rem; margin-bottom:.8rem;
  background:linear-gradient(135deg, rgba(30,107,255,.3), rgba(34,211,238,.12));
  border:1px solid var(--garis); font-size:.84rem; color:#BFD3F0; line-height:1.5; }
.sb-brand b{ display:block; font-family:'Sora',sans-serif; color:#fff; font-size:1rem; }

.stTabs [data-baseweb="tab-list"]{ gap:6px; background:rgba(255,255,255,.04); padding:6px;
  border-radius:16px; border:1px solid var(--garis); }
.stTabs [data-baseweb="tab"]{ border-radius:11px; padding:9px 20px; color:var(--teks2); font-weight:600; }
.stTabs [aria-selected="true"]{ background:linear-gradient(90deg,var(--biru),var(--cyan)); color:#fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none; }

[data-testid="stPlotlyChart"]{ background:var(--kartu); border:1px solid var(--garis);
  border-radius:18px; padding:6px; }
[data-testid="stDataFrame"]{ border-radius:14px; overflow:hidden; border:1px solid var(--garis); }
.stButton > button, .stDownloadButton > button{
  border-radius:12px; border:1px solid var(--cyan); color:#fff; font-weight:600;
  background:linear-gradient(90deg, rgba(30,107,255,.45), rgba(34,211,238,.25)); transition:.25s; }
.stButton > button:hover, .stDownloadButton > button:hover{
  border-color:var(--kuning); transform:translateY(-2px); box-shadow:0 10px 24px rgba(30,107,255,.4); color:#fff; }
:focus-visible{ outline:3px solid var(--kuning) !important; outline-offset:2px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =========================================================
# 2. FUNGSI BANTU: TAMPILAN
# =========================================================
def buat_jejak_seismogram(lebar=1200, tinggi=120, seed=7):
    """Garis seismogram: getaran kecil, gempa utama, lalu mereda."""
    rng = np.random.default_rng(seed)
    n = 420
    x = np.linspace(0, lebar, n)
    t = np.linspace(0, 1, n)
    derau = rng.normal(0, 1, n) * 3
    gempa = np.where(
        t > 0.36, np.exp(-(t - 0.36) * 5.5) * np.sin((t - 0.36) * 210) * 46, 0)
    awal = np.where(
        (t > 0.30) & (t <= 0.36), np.sin(t * 320) * 9 * (t - 0.30) / 0.06, 0)
    y = tinggi / 2 + derau + gempa + awal
    titik = " ".join(
        f"{'M' if i == 0 else 'L'}{xi:.1f},{yi:.1f}"
        for i, (xi, yi) in enumerate(zip(x, y)))
    return (
        f'<svg viewBox="0 0 {lebar} {tinggi}" preserveAspectRatio="none" '
        f'role="img" aria-label="Ilustrasi rekaman seismogram">'
        f'<path class="trace" pathLength="1" d="{titik}"/></svg>')


TICKER = [
    "Kota Palu berada di dekat jalur Sesar Palu–Koro, salah satu sesar aktif utama di Sulawesi.",
    "Gempa M7,4 Donggala–Palu pada 28 September 2018 menjadi pengingat pentingnya pemantauan seismik.",
    "Klasifikasi kedalaman BMKG: dangkal < 60 km, menengah 60–300 km, dalam > 300 km.",
    "Data yang diunggah hanya diproses pada sesi ini oleh aplikasi.",
]


def tampilkan_hero():
    svg = buat_jejak_seismogram()
    ticker = "".join(f"<span>🔸 {t}</span>" for t in TICKER * 2)
    html = (
        f'<div class="ticker"><div class="ticker-isi">{ticker}</div></div>'
        '<div class="hero"><div class="hero-top"><div>'
        '<div class="baris-lencana"><span class="logo">BMKG</span>'
        '<span class="live"><i></i>Pemantauan Seismik · Sulawesi Tengah</span></div>'
        '<div class="judul">Seismo <em>Analytics</em></div>'
        '<div class="sub">Dasbor analisis katalog gempa bumi untuk wilayah <b>Kota Palu</b> '
        'dan sekitarnya. Unggah katalog, saring menurut waktu, magnitudo, kedalaman, dan '
        'jarak dari Palu, lalu baca statistik, grafik, dan peta episenter dalam satu layar.</div>'
        '<span class="magang">🎓 Tugas Project Magang</span></div>'
        '<div class="ripple"><span></span><span></span><span></span><b></b>'
        '<em>KOTA PALU · 0,89° LS · 119,87° BT</em></div></div>'
        '<div class="info-grid">'
        '<div class="panel"><h4>👥 Disusun oleh</h4>'
        '<div class="anggota">Thelma<span>G20123022</span></div>'
        '<div class="anggota">Abid Qhosim<span>G20123029</span></div>'
        '<div class="anggota">Meriani Lestari<span>G20123040</span></div></div>'
        '<div class="panel instansi"><h4>📍 Lokasi magang</h4>'
        '<b>BMKG Stasiun Geofisika Kelas I Palu</b>'
        '<p>Jl. Sumur Yoga No.4, Balaroa, Palu</p></div></div>'
        f'{svg}</div>')
    st.markdown(html, unsafe_allow_html=True)


def judul(teks, kecil=""):
    ket = f"<small>{kecil}</small>" if kecil else ""
    st.markdown(f'<div class="sec">{teks}{ket}</div>', unsafe_allow_html=True)


def kartu(ikon, nilai, label, warna):
    return (f'<div class="kpi" style="--acc:{warna}"><div class="ik">{ikon}</div>'
            f'<div class="nl">{nilai}</div><div class="lb">{label}</div></div>')


def gaya(fig, tinggi=380):
    """Tema grafik gelap yang serasi dengan dasbor."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#DCE8FF"),
        title=dict(font=dict(size=16, family="Sora, sans-serif")),
        margin=dict(l=12, r=12, t=52, b=12), height=tinggi,
        hoverlabel=dict(bgcolor="#0B1E3F", font_color="#fff"),
        legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor="rgba(255,255,255,.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,.08)", zeroline=False)
    return fig


def tampilkan_panduan_awal():
    k1, k2, k3 = st.columns(3)
    langkah = [
        ("1", "Pilih sumber data",
         "Unggah file CSV atau Excel, atau coba dulu dengan data contoh di menu sebelah kiri."),
        ("2", "Atur filter",
         "Batasi tanggal, magnitudo, kedalaman, dan radius dari Kota Palu sesuai kebutuhan analisis."),
        ("3", "Baca dan unduh hasil",
         "Lihat ringkasan, grafik, dan peta, lalu unduh hasilnya dalam format CSV atau Excel."),
    ]
    for kolom, (no, jdl, isi) in zip((k1, k2, k3), langkah):
        kolom.markdown(
            f'<div class="langkah"><div class="nomor">{no}</div>'
            f'<b>{jdl}</b><span>{isi}</span></div>', unsafe_allow_html=True)

    judul("Kolom yang dibutuhkan")
    st.dataframe(pd.DataFrame({
        "Kolom": ["Waktu kejadian", "Latitude", "Longitude", "Kedalaman", "Magnitudo"],
        "Nama yang dikenali": [
            "datetime, tanggal, waktu, origin time", "latitude, lintang, lat",
            "longitude, bujur, lon", "depth_km, depth, kedalaman", "magnitude, magnitudo, mag"],
    }), hide_index=True, **STRETCH)


# =========================================================
# 3. FUNGSI BANTU: DATA & ANALISIS
# =========================================================
def jarak_km(lat, lon, lat0=PALU_LAT, lon0=PALU_LON):
    """Jarak lingkaran besar (haversine) ke titik acuan, dalam km."""
    r = 6371.0088
    p1, p2 = np.radians(lat), np.radians(lat0)
    dphi, dl = p2 - p1, np.radians(lon0 - lon)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def lingkaran(lat0, lon0, r_km, n=100):
    t = np.linspace(0, 2 * np.pi, n)
    lat = lat0 + (r_km / 111.195) * np.sin(t)
    lon = lon0 + (r_km / (111.195 * np.cos(np.radians(lat0)))) * np.cos(t)
    return lat, lon


BATAS_MAG = [-np.inf, 3, 4, 5, 6, 7, 8, np.inf]
LABEL_MAG = ["Mikro (<3)", "Minor (3–3,9)", "Ringan (4–4,9)", "Sedang (5–5,9)",
             "Kuat (6–6,9)", "Mayor (7–7,9)", "Great (≥8)"]
BATAS_DEPTH = [-np.inf, 60, 300, np.inf]
LABEL_DEPTH = ["Dangkal (<60 km)", "Menengah (60–300 km)", "Dalam (>300 km)"]


def perkaya(df):
    df = df.copy()
    df["jarak_palu_km"] = jarak_km(df["latitude"].values, df["longitude"].values).round(1)
    df["kelas_mag"] = pd.cut(df["magnitude"], BATAS_MAG, labels=LABEL_MAG, right=False)
    df["kelas_depth"] = pd.cut(df["depth_km"], BATAS_DEPTH, labels=LABEL_DEPTH, right=False)
    df["waktu_str"] = df["datetime"].dt.strftime("%d-%m-%Y %H:%M")
    return df


def buat_data_contoh(n=650, seed=11):
    """Data SINTETIS di sekitar Sulawesi Tengah (bukan data resmi BMKG)."""
    rng = np.random.default_rng(seed)
    # lat, lon, sebaran (derajat), bobot
    zona = [(-0.89, 119.87, 0.18, 0.30), (-1.30, 120.05, 0.30, 0.25),
            (-0.55, 119.65, 0.25, 0.15), (-1.45, 120.70, 0.35, 0.12),
            (-1.00, 119.30, 0.35, 0.10), (-0.95, 121.40, 0.40, 0.08)]
    bobot = np.array([z[3] for z in zona])
    idx = rng.choice(len(zona), size=n, p=bobot / bobot.sum())
    lat = np.array([zona[i][0] for i in idx]) + rng.normal(0, 1, n) * np.array([zona[i][2] for i in idx])
    lon = np.array([zona[i][1] for i in idx]) + rng.normal(0, 1, n) * np.array([zona[i][2] for i in idx])
    mag = np.round(np.minimum(2.5 + rng.exponential(1 / np.log(10), n), 7.0), 1)  # b ~ 1
    depth = np.clip(rng.lognormal(3.0, 0.9, n), 2, 250).round(0)
    akhir = pd.Timestamp.now().normalize()
    detik = np.sort(rng.uniform(0, 365 * 86400, n))
    waktu = (akhir - pd.Timedelta(days=365)) + pd.to_timedelta(detik, unit="s")
    return pd.DataFrame({
        "datetime": waktu.floor("s"), "latitude": lat.round(3), "longitude": lon.round(3),
        "depth_km": depth, "magnitude": mag})


def normalisasi_nama(nama):
    return re.sub(r"[^a-z0-9]", "", str(nama).strip().lower())


ALIAS_KOLOM = {
    "datetime": ["datetime", "tanggal", "waktu", "origin time", "date",
                 "tanggal waktu", "tanggal kejadian", "ot", "time"],
    "latitude": ["latitude", "lintang", "lat", "garis lintang"],
    "longitude": ["longitude", "bujur", "lon", "long", "garis bujur"],
    "depth_km": ["depth_km", "depth", "kedalaman", "kedalaman km", "depth (km)"],
    "magnitude": ["magnitude", "magnitudo", "mag", "magnitude ml", "mag ml"],
}


def rapikan_kolom(df):
    df = df.copy()
    peta = {normalisasi_nama(k): k for k in df.columns}
    nama_baru = {}
    for tujuan, daftar in ALIAS_KOLOM.items():
        for alias in daftar:
            if normalisasi_nama(alias) in peta:
                nama_baru[peta[normalisasi_nama(alias)]] = tujuan
                break
    df = df.rename(columns=nama_baru)

    wajib = ["datetime", "latitude", "longitude", "depth_km", "magnitude"]
    hilang = [k for k in wajib if k not in df.columns]
    if hilang:
        raise ValueError(
            "Kolom berikut belum ditemukan: " + ", ".join(hilang)
            + ". Pastikan file memiliki kolom tanggal/waktu, latitude, "
            "longitude, kedalaman, dan magnitudo.")

    df = df[wajib].copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", dayfirst=True)
    for k in ["latitude", "longitude", "depth_km", "magnitude"]:
        df[k] = pd.to_numeric(
            df[k].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    df = df.dropna(subset=wajib)
    df = df[df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)
            & (df["depth_km"] >= 0) & (df["magnitude"] >= 0)]
    return df.sort_values("datetime").reset_index(drop=True)


def hitung_b(mag, mc, dm=0.1):
    """b-value metode Aki (1965) dengan koreksi Utsu: b = log10(e)/(mean - (Mc - dM/2))."""
    sub = mag[mag >= mc]
    if len(sub) < 20 or sub.mean() <= mc - dm / 2:
        return None
    b = np.log10(np.e) / (sub.mean() - (mc - dm / 2))
    return b, b / np.sqrt(len(sub)), len(sub)


# --- kompatibilitas versi plotly (scatter_map vs scatter_mapbox) ---
BARU = hasattr(px, "scatter_map")
GAYA_PETA = "map_style" if BARU else "mapbox_style"
PETA_TITIK = px.scatter_map if BARU else px.scatter_mapbox
PETA_DENSITAS = px.density_map if BARU else px.density_mapbox
TRACE_PETA = go.Scattermap if hasattr(go, "Scattermap") else go.Scattermapbox


# =========================================================
# 4. TAMPILAN AWAL + SIDEBAR
# =========================================================
tampilkan_hero()

st.sidebar.markdown(
    '<div class="sb-brand"><b>🌏 Seismo Analytics</b>BMKG Stasiun Geofisika<br>Kelas I Palu</div>',
    unsafe_allow_html=True)
st.sidebar.header("📂 Sumber Data")
mode_data = st.sidebar.radio(
    "Pilih sumber data", ["Unggah CSV/Excel", "Gunakan data contoh"],
    label_visibility="collapsed")

file_upload = None
if mode_data == "Unggah CSV/Excel":
    file_upload = st.sidebar.file_uploader(
        "Pilih file katalog gempa", type=["csv", "xlsx", "xls"])
    st.sidebar.info("File harus memuat waktu, latitude, longitude, kedalaman, dan magnitudo.")
else:
    st.sidebar.download_button(
        "Unduh CSV data contoh",
        data=buat_data_contoh().to_csv(index=False).encode("utf-8"),
        file_name="contoh_data_gempa.csv", mime="text/csv")

# =========================================================
# 5. MEMPROSES DATA
# =========================================================
df_asli = None
try:
    if mode_data == "Gunakan data contoh":
        df_asli = rapikan_kolom(buat_data_contoh())
    elif file_upload is not None:
        if file_upload.name.lower().endswith(".csv"):
            try:
                df_baca = pd.read_csv(file_upload, sep=None, engine="python")
            except UnicodeDecodeError:
                file_upload.seek(0)
                df_baca = pd.read_csv(file_upload, sep=None, engine="python", encoding="latin-1")
        else:
            df_baca = pd.read_excel(file_upload)
        df_asli = rapikan_kolom(df_baca)
except Exception as e:
    st.error(f"Gagal membaca data: {e}")

if df_asli is None:
    tampilkan_panduan_awal()
    st.stop()
if df_asli.empty:
    st.error("Tidak ada baris data valid. Periksa format tanggal, koordinat, kedalaman, dan magnitudo.")
    st.stop()

df_asli = perkaya(df_asli)

# =========================================================
# 6. FILTER
# =========================================================
st.sidebar.header("🔎 Filter Analisis")
tgl_min, tgl_maks = df_asli["datetime"].min().date(), df_asli["datetime"].max().date()
rentang = st.sidebar.date_input(
    "Rentang tanggal", value=(tgl_min, tgl_maks), min_value=tgl_min, max_value=tgl_maks)
if isinstance(rentang, (tuple, list)):
    tgl_awal = rentang[0]
    tgl_akhir = rentang[1] if len(rentang) == 2 else rentang[0]
else:
    tgl_awal = tgl_akhir = rentang

mag_lo = float(np.floor(df_asli["magnitude"].min() * 10) / 10)
mag_hi = float(np.ceil(df_asli["magnitude"].max() * 10) / 10)
dep_lo = float(np.floor(df_asli["depth_km"].min()))
dep_hi = float(np.ceil(df_asli["depth_km"].max()))

f_mag = st.sidebar.slider("Rentang magnitudo", mag_lo, mag_hi if mag_hi > mag_lo else mag_lo + 0.1,
                          (mag_lo, mag_hi), step=0.1)
f_depth = st.sidebar.slider("Rentang kedalaman (km)", dep_lo, dep_hi if dep_hi > dep_lo else dep_lo + 1.0,
                            (dep_lo, dep_hi), step=1.0)

st.sidebar.header("📍 Fokus Kota Palu")
batasi = st.sidebar.checkbox("Batasi radius dari Kota Palu", value=False)
radius = st.sidebar.slider("Radius (km)", 25, 600, 200, 25, disabled=not batasi)

mask = ((df_asli["datetime"].dt.date >= tgl_awal) & (df_asli["datetime"].dt.date <= tgl_akhir)
        & df_asli["magnitude"].between(*f_mag) & df_asli["depth_km"].between(*f_depth))
if batasi:
    mask &= df_asli["jarak_palu_km"] <= radius
df = df_asli[mask].copy()

contoh = mode_data == "Gunakan data contoh"
chip = ('<span class="chip warn">⚠️ Data simulasi, bukan data resmi BMKG</span>' if contoh else "")
st.markdown(
    f'<span class="chip ok">✅ {len(df_asli):,} kejadian valid dibaca · {len(df):,} lolos filter</span>{chip}',
    unsafe_allow_html=True)

if df.empty:
    st.warning("Tidak ada data yang sesuai dengan filter.")
    st.stop()

# =========================================================
# 7. KPI
# =========================================================
n = len(df)
baris_maks = df.loc[df["magnitude"].idxmax()]
pct_dangkal = (df["depth_km"] < 60).mean() * 100
dekat = int((df["jarak_palu_km"] <= 100).sum())

st.markdown('<div class="kpi-grid">' + "".join([
    kartu("📡", f"{n:,}", "Jumlah kejadian", BIRU),
    kartu("⚡", f"M {df['magnitude'].max():.1f}", "Magnitudo maksimum", MERAH),
    kartu("📈", f"{df['magnitude'].mean():.2f}", "Magnitudo rata-rata", CYAN),
    kartu("⛏️", f"{df['depth_km'].mean():.1f} km", "Kedalaman rata-rata", KUNING),
    kartu("🌊", f"{pct_dangkal:.0f}%", "Gempa dangkal (<60 km)", ORANYE),
    kartu("📍", f"{dekat:,}", "Dalam radius 100 km dari Palu", HIJAU),
]) + "</div>", unsafe_allow_html=True)

st.markdown(
    '<div class="terkuat"><div class="besar"><small>GEMPA TERKUAT</small>'
    f'M {baris_maks["magnitude"]:.1f}</div><p>'
    f'<b>{baris_maks["datetime"]:%d-%m-%Y %H:%M}</b> · kedalaman <b>{baris_maks["depth_km"]:.0f} km</b> '
    f'({baris_maks["kelas_depth"]})<br>Koordinat <b>{baris_maks["latitude"]:.3f}, '
    f'{baris_maks["longitude"]:.3f}</b> · berjarak sekitar <b>{baris_maks["jarak_palu_km"]:.0f} km</b> '
    f'dari Kota Palu · kategori <b>{baris_maks["kelas_mag"]}</b></p></div>',
    unsafe_allow_html=True)

def buat_peta(data, gaya_peta="open-street-map", mode="Titik episenter", warna_oleh="Magnitudo",
              ukuran=14, pusat_palu=True, tampil_radius=True, tinggi=620):
    """Peta episenter interaktif dengan penanda Kota Palu dan lingkaran radius."""
    r_gambar = radius if batasi else 100
    pusat = (dict(lat=PALU_LAT, lon=PALU_LON) if pusat_palu
             else dict(lat=float(data["latitude"].mean()), lon=float(data["longitude"].mean())))
    zoom = 7 if pusat_palu else 5
    if mode == "Titik episenter":
        kol_warna = "magnitude" if warna_oleh == "Magnitudo" else "depth_km"
        skala = SKALA_MAG if warna_oleh == "Magnitudo" else [[0, KUNING], [0.5, BIRU], [1, "#8B5CF6"]]
        fig = PETA_TITIK(
            data, lat="latitude", lon="longitude", color=kol_warna, size="magnitude",
            size_max=ukuran, hover_name="waktu_str",
            hover_data={"latitude": ":.3f", "longitude": ":.3f", "depth_km": True,
                        "magnitude": True, "jarak_palu_km": True, "waktu_str": False},
            color_continuous_scale=skala, center=pusat, zoom=zoom, opacity=0.85,
            labels={"magnitude": "Magnitudo", "depth_km": "Kedalaman (km)",
                    "jarak_palu_km": "Jarak Palu (km)"})
    else:
        fig = PETA_DENSITAS(data, lat="latitude", lon="longitude", z="magnitude", radius=18,
                            center=pusat, zoom=zoom, color_continuous_scale=SKALA_MAG)
    if tampil_radius:
        la, lo = lingkaran(PALU_LAT, PALU_LON, r_gambar)
        fig.add_trace(TRACE_PETA(lat=la, lon=lo, mode="lines", name=f"Radius {r_gambar} km",
                                 line=dict(color=KUNING, width=2), hoverinfo="skip"))
    fig.add_trace(TRACE_PETA(lat=[PALU_LAT], lon=[PALU_LON], mode="markers+text", name="Kota Palu",
                             marker=dict(size=15, color=KUNING), text=["Kota Palu"],
                             textposition="top right", textfont=dict(color="#FFFFFF", size=13),
                             hoverinfo="text"))
    fig.update_layout(**{GAYA_PETA: gaya_peta})
    return gaya(fig, tinggi)


# =========================================================
# 8. TAB ANALISIS
# =========================================================
judul("Peta sebaran episenter", "titik kuning = Kota Palu")
st.plotly_chart(buat_peta(df, tinggi=500), key="peta_utama", **STRETCH)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Ringkasan", "📈 Grafik", "🗺️ Peta Episenter", "📋 Data & Unduh"])

statistik = pd.DataFrame({
    "Ukuran Statistik": ["Rata-rata", "Median", "Minimum", "Maksimum",
                         "Simpangan baku", "Kuartil 1", "Kuartil 3"],
    "Magnitudo": [df["magnitude"].mean(), df["magnitude"].median(), df["magnitude"].min(),
                  df["magnitude"].max(), df["magnitude"].std(),
                  df["magnitude"].quantile(.25), df["magnitude"].quantile(.75)],
    "Kedalaman (km)": [df["depth_km"].mean(), df["depth_km"].median(), df["depth_km"].min(),
                       df["depth_km"].max(), df["depth_km"].std(),
                       df["depth_km"].quantile(.25), df["depth_km"].quantile(.75)],
    "Jarak dari Palu (km)": [df["jarak_palu_km"].mean(), df["jarak_palu_km"].median(),
                             df["jarak_palu_km"].min(), df["jarak_palu_km"].max(),
                             df["jarak_palu_km"].std(), df["jarak_palu_km"].quantile(.25),
                             df["jarak_palu_km"].quantile(.75)],
}).round(3)

klas_mag = (df["kelas_mag"].value_counts().reindex(LABEL_MAG).fillna(0).astype(int)
            .rename_axis("Kategori").reset_index(name="Jumlah"))
klas_dep = (df["kelas_depth"].value_counts().reindex(LABEL_DEPTH).fillna(0).astype(int)
            .rename_axis("Kategori").reset_index(name="Jumlah"))

# ---------------- TAB 1 ----------------
with tab1:
    judul("Ringkasan otomatis", "siap dikutip ke laporan")
    st.markdown(
        f'<div class="narasi">Pada periode <b>{tgl_awal:%d-%m-%Y}</b> sampai <b>{tgl_akhir:%d-%m-%Y}</b> '
        f'tercatat <b>{n:,}</b> kejadian gempa dengan magnitudo rata-rata <b>{df["magnitude"].mean():.2f}</b> '
        f'(rentang {df["magnitude"].min():.1f}–{df["magnitude"].max():.1f}). '
        f'Sebanyak <b>{pct_dangkal:.1f}%</b> tergolong gempa dangkal (kedalaman &lt; 60 km), dan '
        f'<b>{dekat:,}</b> kejadian berada dalam radius 100 km dari Kota Palu. '
        f'Gempa terkuat bermagnitudo <b>M {baris_maks["magnitude"]:.1f}</b> pada '
        f'<b>{baris_maks["datetime"]:%d-%m-%Y}</b>, berjarak sekitar <b>{baris_maks["jarak_palu_km"]:.0f} km</b> '
        f'dari Kota Palu.</div>', unsafe_allow_html=True)

    judul("Statistik deskriptif")
    st.dataframe(statistik, hide_index=True, **STRETCH)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(klas_mag, x="Kategori", y="Jumlah", color="Jumlah",
                     color_continuous_scale=SKALA_MAG, text_auto=True,
                     title="Klasifikasi Magnitudo")
        fig.update_coloraxes(showscale=False)
        fig.update_traces(marker_line_width=0, textposition="outside")
        fig.update_layout(xaxis_title=None, yaxis_title="Jumlah kejadian")
        st.plotly_chart(gaya(fig), **STRETCH)
    with c2:
        d = klas_dep[klas_dep["Jumlah"] > 0]
        fig = px.pie(d, names="Kategori", values="Jumlah", hole=0.62,
                     color="Kategori", title="Klasifikasi Kedalaman",
                     color_discrete_map=dict(zip(LABEL_DEPTH, [CYAN, KUNING, MERAH])))
        fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color="#050E24", width=3)))
        fig.update_layout(showlegend=False)
        st.plotly_chart(gaya(fig), **STRETCH)

    judul("10 gempa terkuat")
    top = (df.nlargest(10, "magnitude")[["datetime", "magnitude", "depth_km", "latitude",
                                          "longitude", "jarak_palu_km"]]
           .rename(columns={"datetime": "Tanggal dan Waktu", "magnitude": "Magnitudo",
                            "depth_km": "Kedalaman (km)", "latitude": "Latitude",
                            "longitude": "Longitude", "jarak_palu_km": "Jarak dari Palu (km)"}))
    st.dataframe(top, hide_index=True, **STRETCH)

# ---------------- TAB 2 ----------------
with tab2:
    judul("Distribusi")
    g1, g2 = st.columns(2)
    with g1:
        fig = px.histogram(df, x="magnitude", nbins=20, marginal="box", title="Histogram Magnitudo",
                           color_discrete_sequence=[CYAN])
        fig.update_layout(xaxis_title="Magnitudo", yaxis_title="Jumlah kejadian")
        st.plotly_chart(gaya(fig, 420), **STRETCH)
    with g2:
        fig = px.histogram(df, x="depth_km", nbins=20, marginal="box", title="Histogram Kedalaman",
                           color_discrete_sequence=[KUNING])
        fig.update_layout(xaxis_title="Kedalaman (km)", yaxis_title="Jumlah kejadian")
        st.plotly_chart(gaya(fig, 420), **STRETCH)

    judul("Jumlah gempa terhadap waktu")
    periode = st.selectbox("Pengelompokan waktu", ["Harian", "Mingguan", "Bulanan"])
    aturan = {"Harian": "D", "Mingguan": "W", "Bulanan": "MS"}[periode]
    seri = df.set_index("datetime").resample(aturan).size().reset_index(name="jumlah_gempa")
    w1, w2 = st.columns(2)
    with w1:
        fig = px.bar(seri, x="datetime", y="jumlah_gempa", title=f"Jumlah Kejadian per {periode}",
                     labels={"datetime": "Waktu", "jumlah_gempa": "Jumlah kejadian"},
                     color_discrete_sequence=[BIRU])
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(gaya(fig), **STRETCH)
    with w2:
        kum = df[["datetime"]].copy()
        kum["kumulatif"] = np.arange(1, len(kum) + 1)
        fig = px.area(kum, x="datetime", y="kumulatif", title="Akumulasi Kejadian",
                      labels={"datetime": "Waktu", "kumulatif": "Kumulatif"},
                      color_discrete_sequence=[CYAN])
        st.plotly_chart(gaya(fig), **STRETCH)

    judul("Magnitudo terhadap kedalaman")
    fig = px.scatter(df, x="depth_km", y="magnitude", color="magnitude", size="magnitude",
                     size_max=16, opacity=0.8, color_continuous_scale=SKALA_MAG,
                     hover_name="waktu_str",
                     hover_data={"latitude": True, "longitude": True, "waktu_str": False},
                     title="Hubungan Magnitudo dan Kedalaman",
                     labels={"depth_km": "Kedalaman (km)", "magnitude": "Magnitudo"})
    st.plotly_chart(gaya(fig, 440), **STRETCH)

    judul("Frekuensi–magnitudo (Gutenberg–Richter)", "estimasi b-value")
    mc = st.number_input("Magnitudo kelengkapan (Mc)", 0.0, 10.0,
                         float(round(df["magnitude"].min(), 1)), 0.1,
                         help="Magnitudo terkecil yang dianggap tercatat lengkap oleh jaringan.")
    hasil_b = hitung_b(df["magnitude"], mc)
    ms = np.round(np.arange(mc, df["magnitude"].max() + 0.05, 0.1), 1)
    jml = np.array([(df["magnitude"] >= m - 1e-9).sum() for m in ms])
    ok = jml > 0
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ms[ok], y=jml[ok], mode="markers", name="N (≥ M)",
                             marker=dict(color=CYAN, size=8)))
    if hasil_b:
        b, se, nn = hasil_b
        a = np.log10(nn) + b * mc
        fig.add_trace(go.Scatter(x=ms, y=10 ** (a - b * ms), mode="lines", name="Garis regresi",
                                 line=dict(color=KUNING, width=3)))
    fig.update_layout(title="Distribusi Frekuensi Kumulatif", xaxis_title="Magnitudo",
                      yaxis_title="Jumlah kejadian ≥ M (skala log)", yaxis_type="log")
    st.plotly_chart(gaya(fig, 400), **STRETCH)
    if hasil_b:
        st.markdown(
            f'<div class="narasi">Estimasi <b>b-value = {b:.2f} ± {se:.2f}</b> '
            f'(n = {nn:,} kejadian dengan M ≥ {mc:.1f}). Nilai b sekitar 1 umum dijumpai pada '
            f'kawasan tektonik aktif. Hasil ini bersifat indikatif dan sensitif terhadap pemilihan Mc.</div>',
            unsafe_allow_html=True)
    else:
        st.info("Data dengan M ≥ Mc kurang dari 20 kejadian, sehingga b-value belum dapat diestimasi.")

# ---------------- TAB 3 ----------------
with tab3:
    judul("Peta episenter", "fokus Kota Palu")
    p1, p2, p3 = st.columns(3)
    gaya_peta = p1.selectbox("Gaya peta", ["open-street-map", "carto-darkmatter", "carto-positron"])
    mode_peta = p2.radio("Mode tampilan", ["Titik episenter", "Heatmap kepadatan"], horizontal=True)
    warna_oleh = p3.selectbox("Warna titik berdasarkan", ["Magnitudo", "Kedalaman"])
    q1, q2, q3 = st.columns(3)
    ukuran = q1.slider("Ukuran titik maksimum", 4, 30, 14)
    pusat_palu = q2.checkbox("Pusatkan ke Kota Palu", value=True)
    tampil_radius = q3.checkbox("Tampilkan lingkaran radius", value=True)

    st.plotly_chart(buat_peta(df, gaya_peta, mode_peta, warna_oleh, ukuran, pusat_palu,
                                tampil_radius, 620), key="peta_tab", **STRETCH)
    st.caption("Peta dasar membutuhkan koneksi internet. Posisi titik mengikuti koordinat pada file. "
               "Titik kuning menandai Kota Palu sebagai acuan jarak.")

# ---------------- TAB 4 ----------------
with tab4:
    judul("Data gempa yang dianalisis", f"{n:,} baris")
    tampilkan = df.rename(columns={
        "datetime": "Tanggal dan Waktu", "latitude": "Latitude", "longitude": "Longitude",
        "depth_km": "Kedalaman (km)", "magnitude": "Magnitudo", "jarak_palu_km": "Jarak dari Palu (km)",
        "kelas_mag": "Kategori Magnitudo", "kelas_depth": "Kategori Kedalaman",
    })[["Tanggal dan Waktu", "Latitude", "Longitude", "Kedalaman (km)", "Magnitudo",
        "Jarak dari Palu (km)", "Kategori Magnitudo", "Kategori Kedalaman"]]
    st.dataframe(tampilkan, hide_index=True, height=440, **STRETCH)

    judul("Unduh hasil analisis")
    csv_hasil = tampilkan.to_csv(index=False).encode("utf-8-sig")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        tampilkan.to_excel(writer, sheet_name="Data Gempa", index=False)
        statistik.to_excel(writer, sheet_name="Statistik", index=False)
        klas_mag.to_excel(writer, sheet_name="Klasifikasi Magnitudo", index=False)
        klas_dep.to_excel(writer, sheet_name="Klasifikasi Kedalaman", index=False)
    d1, d2, _ = st.columns([1, 1, 2])
    d1.download_button("⬇️ Unduh data (CSV)", data=csv_hasil,
                       file_name="hasil_analisis_gempa.csv", mime="text/csv")
    d2.download_button(
        "⬇️ Unduh laporan (Excel)", data=buffer.getvalue(), file_name="hasil_analisis_gempa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()
st.caption(
    "Seismo Analytics · BMKG Stasiun Geofisika Kelas I Palu — prototipe akademik. "
    "Periksa kualitas data dan validasi hasil sebelum digunakan untuk analisis operasional.")
