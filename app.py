import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime
from supabase import create_client, Client

# Page Configuration
st.set_page_config(page_title="Manolya Trend Yönetimi", page_icon="🏢", layout="wide")

STORAGE_BUCKET = "dekontlar"  # Supabase Storage'da oluşturduğun bucket adı

# --- SUPABASE BAĞLANTISI ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Türkçe Para Formatı Yardımcı Fonksiyonu (1.250,50 ₺)
def para_format(deger):
    if deger is None:
        deger = 0.0
    try:
        deger = float(deger)
    except:
        deger = 0.0
    tmp = f"{deger:,.2f}"
    tmp = tmp.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{tmp} ₺"

# Türkçe Ay ve Tarih Sözlüğü
TURKCE_AYLAR = {
    "January": "Ocak", "February": "Şubat", "March": "Mart", "April": "Nisan",
    "May": "Mayıs", "June": "Haziran", "July": "Temmuz", "August": "Ağustos",
    "September": "Eylül", "October": "Ekim", "November": "Kasım", "December": "Aralık"
}

def turkce_donem_adi(ingilizce_donem):
    for ing, tr in TURKCE_AYLAR.items():
        ingilizce_donem = str(ingilizce_donem).replace(ing, tr)
    return ingilizce_donem

# Açıklama metninden daire kodunu ve borç türünü çıkaran akıllı fonksiyon
def aciklama_analiz_et(aciklama):
    if not isinstance(aciklama, str):
        return None, "Aidat"
    
    aciklama_upper = aciklama.upper()
    
    # Daire kodunu bul (Örn: A-1, B3, C-4, G-2 vb.)
    daire_match = re.search(r'\b([A-G])\s*[-]?\s*([1-8])\b', aciklama_upper)
    daire_kodu = None
    if daire_match:
        daire_kodu = f"{daire_match.group(1)}-{daire_match.group(2)}"
        
    # Borç türünü tahmin et
    borc_turu = "Aidat"
    if "SU" in aciklama_upper:
        borc_turu = "Su"
    elif "ESKİ" in aciklama_upper or "GEÇMİŞ" in aciklama_upper:
        borc_turu = "Eski Borç"
        
    return daire_kodu, borc_turu

# İlk Kurulum / Tablo Kontrolü ve Varsayılan Veriler
def init_db():
    try:
        res = supabase.table("daireler").select("*", count="exact").execute()
        if res.count == 0 or not res.data:
            daire_verileri = [
                {"daire_kodu": "A-1", "sakin_adi": "EDA BÜYÜKYILDIRIM", "aidat_tutari": 2620.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.05702},
                {"daire_kodu": "A-2", "sakin_adi": "FATMA CEYLAN", "aidat_tutari": 2210.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.039439},
                {"daire_kodu": "A-3", "sakin_adi": "ZEYNEP HANIM", "aidat_tutari": 2030.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.031403},
                {"daire_kodu": "A-4", "sakin_adi": "CEREN ÇINAR", "aidat_tutari": 2410.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.047884},
                {"daire_kodu": "A-5", "sakin_adi": "VENÜS PALA", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "A-6", "sakin_adi": "ÖZLEM ÖZDİLEK", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "A-7", "sakin_adi": "ORHUN SEZGİN", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "A-8", "sakin_adi": "SALİH ERGONDU", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "B-1", "sakin_adi": "EGE OĞUZ", "aidat_tutari": 3790.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "B-2", "sakin_adi": "ESRA KOÇ-MURAT GÜRKAN KINA", "aidat_tutari": 3520.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "B-3", "sakin_adi": "YİĞİT ATİLAY", "aidat_tutari": 3370.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "B-4", "sakin_adi": "EMİN GENÇPINAR", "aidat_tutari": 3710.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "C-1", "sakin_adi": "NİHAT KARABULUT", "aidat_tutari": 3700.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "C-2", "sakin_adi": "NİHAT KARABULUT", "aidat_tutari": 3370.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "C-3", "sakin_adi": "EGE DOĞAN DURMUŞ", "aidat_tutari": 3560.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "C-4", "sakin_adi": "ERSİN ALTIN", "aidat_tutari": 3860.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "D-1", "sakin_adi": "GÜLİSTAN COŞKUN", "aidat_tutari": 2680.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "D-2", "sakin_adi": "TEVFİK TAMER GÜRDEREOĞLU", "aidat_tutari": 2610.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "D-3", "sakin_adi": "BANU AYTAÇER", "aidat_tutari": 2290.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "D-4", "sakin_adi": "ASİME DAĞ", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "D-5", "sakin_adi": "HASAN BEY", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "D-6", "sakin_adi": "İBRAHİM CERİT", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "E-1", "sakin_adi": "MURAT YAMAN", "aidat_tutari": 2650.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "E-2", "sakin_adi": "MERT RECEP SAYGIN", "aidat_tutari": 2230.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "E-3", "sakin_adi": "CEREN - EZGİ ŞİMŞİR", "aidat_tutari": 1920.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "E-4", "sakin_adi": "CELAL DAĞDELEN", "aidat_tutari": 2090.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "E-5", "sakin_adi": "CANAN TOSBAT/JALE TOSBAT", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "E-6", "sakin_adi": "HAKAN NURHAN", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "E-7", "sakin_adi": "SERDAL YAZĞAN", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "E-8", "sakin_adi": "HURİYE FIRTINA", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "F-1", "sakin_adi": "BAHADIR DİNÇER", "aidat_tutari": 1930.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "F-2", "sakin_adi": "MUKADDER AYHAN", "aidat_tutari": 1900.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "F-3", "sakin_adi": "MEHMET BAŞEĞMEZ", "aidat_tutari": 2040.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "F-4", "sakin_adi": "ÜNSAL TERLİKLİ", "aidat_tutari": 2120.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "F-5", "sakin_adi": "MELİSA HANIM", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "F-6", "sakin_adi": "HAMİYET YONGA", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "F-7", "sakin_adi": "EMEL TURAN", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "F-8", "sakin_adi": "NURTAÇ GÜLTEN", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "G-1", "sakin_adi": "BETÜL ALTIOK", "aidat_tutari": 0.0, "aidat_muaf": True, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "G-2", "sakin_adi": "ECE TEKTEKİN", "aidat_tutari": 0.0, "aidat_muaf": True, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "G-3", "sakin_adi": "CEM ÜNSAL", "aidat_tutari": 0.0, "aidat_muaf": True, "son_su_endeks": 0.0, "bahce_orani": 0.0},
                {"daire_kodu": "G-4", "sakin_adi": "HAKAN BİRLİKER", "aidat_tutari": 0.0, "aidat_muaf": True, "son_su_endeks": 0.0, "bahce_orani": 0.0}
            ]
            supabase.table("daireler").upsert(daire_verileri).execute()
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {e}")

init_db()

st.title("🏢 Manolya Trend Site Yönetim Paneli")

ing_simdiki_ay = datetime.now().strftime("%B %Y")
simdiki_donem_tr = turkce_donem_adi(ing_simdiki_ay)

# Sidebar Giriş
st.sidebar.markdown("### 🔐 Yönetici Girişi")
yonetici_sifresi = st.sidebar.text_input("Yönetici Şifresi", type="password")
dogru_sifre = st.secrets["admin"]["password"]
yonetici_giris_yapildi = (yonetici_sifresi != "" and yonetici_sifresi == dogru_sifre)

if yonetici_giris_yapildi:
    st.sidebar.success("Yönetici Girişi Başarılı ✅")
    menu = [
        "🏠 Daire Hesap Özeti (Sakin Ekranı)",
        "📊 Dashboard / Kasa", 
        "💳 Tahsilat Yönetimi (Aidat / Su / Eski Borç)", 
        "💧 Su Faturası Girişi", 
        "💸 Gider Ekle & Dekont Takibi", 
        "⚙️ Daire & Muafiyet Ayarları"
    ]
else:
    st.sidebar.info("Kat maliki görünümündesiniz.")
    menu = [
        "🏠 Daire Hesap Özeti (Sakin Ekranı)",
        "📊 Dashboard / Kasa", 
        "💸 Gider Ekle & Dekont Takibi"
    ]

secim = st.sidebar.selectbox("Navigasyon", menu)

# --- 1. DAİRE HESAP ÖZETİ ---
if secim == "🏠 Daire Hesap Özeti (Sakin Ekranı)":
    st.header("🏠 Daire Borç ve Hesap Özeti")
    
    daireler_res = supabase.table("daireler").select("daire_kodu, sakin_adi").order("daire_kodu").execute()
    daire_listesi = daireler_res.data if daireler_res.data else []
    
    secilen_daire = st.selectbox(
        "Lütfen Dairenizi Seçin", 
        options=[d["daire_kodu"] for d in daire_listesi],
        format_func=lambda x: f"{x} - {[d['sakin_adi'] for d in daire_listesi if d['daire_kodu'] == x][0]}"
    )
    
    if secilen_daire:
        d_info = supabase.table("daireler").select("*").eq("daire_kodu", secilen_daire).execute().data[0]
        
        borc_res = supabase.table("borclar").select("*").eq("daire_kodu", secilen_daire).order("id", desc=True).execute()
        borclar_data = borc_res.data if borc_res.data else []
        
        tahsilat_res = supabase.table("tahsilat").select("*").eq("daire_kodu", secilen_daire).order("id", desc=True).execute()
        tahsilat_data = tahsilat_res.data if tahsilat_res.data else []
        
        kalan_borc = sum([b["tutar"] for b in borclar_data if not b["odendi"]])
        toplam_odenen = sum([t["tutar"] for t in tahsilat_data])
        
        borclar_df = pd.DataFrame(borclar_data)
        if not borclar_df.empty:
            borclar_df['Durum'] = borclar_df['odendi'].apply(lambda x: 'Ödendi ✅' if x else 'Ödenmedi ❌')
            borclar_df['Tutar (TL)'] = borclar_df['tutar'].apply(para_format)
            borclar_df = borclar_df[['donem', 'tur', 'Tutar (TL)', 'Durum']]
            borclar_df.columns = ['Dönem', 'Borç Türü', 'Tutar (TL)', 'Durum']
            borclar_df['Dönem'] = borclar_df['Dönem'].apply(turkce_donem_adi)
            
        tahsilat_df = pd.DataFrame(tahsilat_data)
        if not tahsilat_df.empty:
            tahsilat_df['Ödenen Tutar (TL)'] = tahsilat_df['tutar'].apply(para_format)
            tahsilat_df = tahsilat_df[['tarih', 'tur', 'Ödenen Tutar (TL)', 'aciklama']]
            tahsilat_df.columns = ['Ödeme Tarihi', 'Ödeme Türü', 'Ödenen Tutar (TL)', 'Açıklama']

        st.markdown(f"### Daire: **{secilen_daire}** | Malik/Sakin: **{d_info['sakin_adi']}**")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("📌 Sabit Aidat Tutarı", para_format(d_info['aidat_tutari']) if not d_info['aidat_muaf'] else "Muaf (G Blok)")
        m2.metric("⚠️ Güncel Kalan Borç", para_format(kalan_borc))
        m3.metric("✅ Yapılan Toplam Ödeme", para_format(toplam_odenen))
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📅 Ay Ay Kalem Kalem Borç Durumu")
            if not borclar_df.empty:
                st.dataframe(borclar_df, use_container_width=True)
            else:
                st.info("Borç kaydı bulunmuyor.")
        with c2:
            st.subheader("💰 Yapılan Geçmiş Ödemeler")
            if not tahsilat_df.empty:
                st.dataframe(tahsilat_df, use_container_width=True)
            else:
                st.info("Geçmiş ödeme kaydı bulunmuyor.")

# --- 2. DASHBOARD / KASA ---
elif secim == "📊 Dashboard / Kasa":
    st.header("🏢 Kasa ve Genel Site Durumu")
    
    tahsilat_all = supabase.table("tahsilat").select("tutar").execute().data
    gider_all = supabase.table("giderler").select("tutar").execute().data
    borc_all = supabase.table("borclar").select("tutar, odendi").execute().data
    
    toplam_gelir = sum([t["tutar"] for t in tahsilat_all]) if tahsilat_all else 0.0
    toplam_gider = sum([g["tutar"] for g in gider_all]) if gider_all else 0.0
    kasa = toplam_gelir - toplam_gider
    toplam_alacak = sum([b["tutar"] for b in borc_all if not b["odendi"]]) if borc_all else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Mevcut Kasa Bakiye", para_format(kasa))
    col2.metric("📈 Toplam Tahsilat", para_format(toplam_gelir))
    col3.metric("📉 Toplam Gider", para_format(toplam_gider))
    col4.metric("⚠️ Bekleyen Toplam Alacak", para_format(toplam_alacak))

    st.markdown("---")
    st.subheader("📊 Aylık Gelir / Gider Trendi")

    tahsilat_tarihli = supabase.table("tahsilat").select("tarih, tutar").execute().data
    gider_tarihli = supabase.table("giderler").select("tarih, tutar").execute().data

    if tahsilat_tarihli or gider_tarihli:
        df_gelir = pd.DataFrame(tahsilat_tarihli) if tahsilat_tarihli else pd.DataFrame(columns=["tarih", "tutar"])
        df_gider = pd.DataFrame(gider_tarihli) if gider_tarihli else pd.DataFrame(columns=["tarih", "tutar"])

        if not df_gelir.empty:
            df_gelir["Ay"] = pd.to_datetime(df_gelir["tarih"], errors='coerce').dt.strftime("%Y-%m")
        if not df_gider.empty:
            df_gider["Ay"] = pd.to_datetime(df_gider["tarih"], errors='coerce').dt.strftime("%Y-%m")

        aylik_gelir = df_gelir.groupby("Ay")["tutar"].sum() if not df_gelir.empty else pd.Series(dtype=float)
        aylik_gider = df_gider.groupby("Ay")["tutar"].sum() if not df_gider.empty else pd.Series(dtype=float)

        aylik_ozet = pd.DataFrame({"Gelir": aylik_gelir, "Gider": aylik_gider}).fillna(0.0).sort_index()
        aylik_ozet = aylik_ozet[aylik_ozet.index.notna() & (aylik_ozet.index != "NaT")]
        aylik_ozet.index = [turkce_donem_adi(pd.to_datetime(ay + "-01").strftime("%B %Y")) for ay in aylik_ozet.index]

        st.bar_chart(aylik_ozet, color=["#2ecc71", "#e74c3c"], stack=False)
    else:
        st.info("Henüz grafik oluşturacak kadar tahsilat veya gider kaydı bulunmuyor.")

    st.markdown("---")
    st.subheader("📋 Ödenmeyen Borçlar Listesi")
    
    bekleyen_borclar = supabase.table("borclar").select("daire_kodu, tur, tutar, donem").eq("odendi", False).order("daire_kodu").execute().data
    daireler_map = {d["daire_kodu"]: d["sakin_adi"] for d in supabase.table("daireler").select("daire_kodu, sakin_adi").execute().data}
    
    if bekleyen_borclar:
        bekleyen_list = []
        for b in bekleyen_borclar:
            bekleyen_list.append({
                "Daire": b["daire_kodu"],
                "Malik/Sakin": daireler_map.get(b["daire_kodu"], ""),
                "Borç Türü": b["tur"],
                "Tutar (TL)": para_format(b["tutar"]),
                "Dönem": turkce_donem_adi(b["donem"])
            })
        st.dataframe(pd.DataFrame(bekleyen_list), use_container_width=True)
    else:
        st.success("Tüm borçlar ödenmiş, harika!")

    st.markdown("---")
    st.subheader("📥 Excel Raporu")
    st.caption("Bekleyen borçlar, tüm tahsilatlar ve tüm giderleri tek bir Excel dosyasında (3 ayrı sayfa halinde) indir.")

    if yonetici_giris_yapildi:
        tahsilat_rapor = supabase.table("tahsilat").select("*").order("tarih", desc=True).execute().data
        gider_rapor = supabase.table("giderler").select("*").order("tarih", desc=True).execute().data

        df_bekleyen_excel = pd.DataFrame(bekleyen_list) if bekleyen_borclar else pd.DataFrame(columns=["Daire", "Malik/Sakin", "Borç Türü", "Tutar (TL)", "Dönem"])

        df_tahsilat_excel = pd.DataFrame(tahsilat_rapor) if tahsilat_rapor else pd.DataFrame()
        if not df_tahsilat_excel.empty:
            df_tahsilat_excel = df_tahsilat_excel[["tarih", "daire_kodu", "tur", "tutar", "aciklama"]]
            df_tahsilat_excel.columns = ["Tarih", "Daire", "Tür", "Tutar (TL)", "Açıklama"]

        df_gider_excel = pd.DataFrame(gider_rapor) if gider_rapor else pd.DataFrame()
        if not df_gider_excel.empty:
            df_gider_excel = df_gider_excel[["tarih", "kategori", "tutar", "aciklama"]]
            df_gider_excel.columns = ["Tarih", "Kategori", "Tutar (TL)", "Açıklama"]

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_bekleyen_excel.to_excel(writer, sheet_name="Bekleyen Borclar", index=False)
            df_tahsilat_excel.to_excel(writer, sheet_name="Tahsilatlar", index=False)
            df_gider_excel.to_excel(writer, sheet_name="Giderler", index=False)
        excel_buffer.seek(0)

        st.download_button(
            label="📥 Excel Raporunu İndir",
            data=excel_buffer,
            file_name=f"manolya_rapor_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Excel raporu indirmek için yönetici girişi yapmalısınız.")

# --- 3. TAHSİLAT YÖNETİMİ ---
elif secim == "💳 Tahsilat Yönetimi (Aidat / Su / Eski Borç)" and yonetici_giris_yapildi:
    st.header("💳 Tahsilat Yönetimi")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📌 Toplu Aidat Borçlandır", 
        "💳 Aidat Tahsil Et (Tablo)", 
        "💧 Su Tahsil Et (Tablo)", 
        "📜 Eski Borç Tahsil Et",
        "📂 Akbank Ekstresi İle Otomatik Tahsilat"
    ])
    
    with tab1:
        st.subheader("Tüm Dairelere Özel Aidat Borcu Yansıt")
        donem = st.text_input("Dönem / Ay", value=simdiki_donem_tr)

        mevcut_kayit = supabase.table("borclar").select("id").eq("donem", donem).eq("tur", "Aidat").limit(1).execute().data
        if mevcut_kayit:
            st.warning(f"'{donem}' dönemi için zaten aidat borcu oluşturulmuş. Tekrar eklersen mükerrer kayıt oluşur.")

        if st.button("Toplu Aidat Yansıt"):
            daireler = supabase.table("daireler").select("daire_kodu, aidat_tutari").eq("aidat_muaf", False).execute().data
            kayitlar = []
            for d in daireler:
                kayitlar.append({
                    "daire_kodu": d["daire_kodu"], "tur": "Aidat", 
                    "tutar": d["aidat_tutari"], "donem": donem, "odendi": False
                })
            if kayitlar:
                supabase.table("borclar").insert(kayitlar).execute()
            st.success(f"{len(daireler)} daireye özel aidat borçları başarıyla eklendi!")
            st.rerun()

    with tab2:
        st.subheader("💳 Aidat Tahsil Et (Tablodan Seçerek)")
        st.info("Tablodan ödeme alan dairelerin yanındaki kutucuğu işaretleyin ve aşağıdaki butona basın.")
        
        aidat_borclari = supabase.table("borclar").select("*").eq("odendi", False).eq("tur", "Aidat").order("daire_kodu").execute().data
        daireler_map = {d["daire_kodu"]: d["sakin_adi"] for d in supabase.table("daireler").select("daire_kodu, sakin_adi").execute().data}
        
        if aidat_borclari:
            df_aidat = pd.DataFrame(aidat_borclari)
            df_aidat['Sec'] = False
            df_aidat['Malik / Sakin'] = df_aidat['daire_kodu'].map(daireler_map)
            df_aidat['Dönem'] = df_aidat['donem'].apply(turkce_donem_adi)
            df_aidat['Tutar (TL)'] = df_aidat['tutar'].apply(para_format)
            
            df_aidat_goster = df_aidat[['Sec', 'id', 'daire_kodu', 'Malik / Sakin', 'Dönem', 'Tutar (TL)']]
            df_aidat_goster.columns = ['Seç', 'ID', 'Daire', 'Malik / Sakin', 'Dönem', 'Tutar (TL)']
            
            edited_aidat_df = st.data_editor(
                df_aidat_goster, hide_index=True, use_container_width=True, key="aidat_tahsil_editor",
                disabled=["ID", "Daire", "Malik / Sakin", "Dönem", "Tutar (TL)"],
                column_config={"ID": None}
            )
            aciklama_toplu_aidat = st.text_input("Ödeme Açıklaması", value="EFT/Nakit Aidat Ödemesi", key="aidat_ack_input")
            
            if st.button("Seçilen Aidatları Tahsil Et ve Kasaya İşle"):
                secilenler = edited_aidat_df[edited_aidat_df['Seç'] == True]
                if not secilenler.empty:
                    borc_map = {b['id']: b for b in aidat_borclari}
                    tahsilat_listesi = []
                    for _, row in secilenler.iterrows():
                        b_item = borc_map[row['ID']]
                        supabase.table("borclar").update({"odendi": True}).eq("id", b_item['id']).execute()
                        tahsilat_listesi.append({
                            "daire_kodu": b_item["daire_kodu"], "tur": "Aidat", 
                            "tutar": b_item["tutar"], "tarih": datetime.now().strftime("%Y-%m-%d"), "aciklama": aciklama_toplu_aidat
                        })
                    if tahsilat_listesi:
                        supabase.table("tahsilat").insert(tahsilat_listesi).execute()
                    st.success(f"Seçilen {len(secilenler)} dairenin aidat ödemesi başarıyla kasaya işlendi!")
                    st.rerun()
                else:
                    st.warning("Lütfen tablodan en az bir daire seçin.")
        else:
            st.info("Ödenmemiş bekleyen aidat borcu bulunmuyor.")

    with tab3:
        st.subheader("💧 Su Tahsil Et (Tablodan Seçerek)")
        st.info("Tablodan suyu ödeyen dairelerin yanındaki kutucuğu işaretleyin ve aşağıdaki butona basın.")
        
        su_borclari = supabase.table("borclar").select("*").eq("odendi", False).eq("tur", "Su").order("daire_kodu").execute().data
        daireler_map = {d["daire_kodu"]: d["sakin_adi"] for d in supabase.table("daireler").select("daire_kodu, sakin_adi").execute().data}
        
        if su_borclari:
            df_su_borc = pd.DataFrame(su_borclari)
            df_su_borc['Sec'] = False
            df_su_borc['Malik / Sakin'] = df_su_borc['daire_kodu'].map(daireler_map)
            df_su_borc['Dönem'] = df_su_borc['donem'].apply(turkce_donem_adi)
            df_su_borc['Tutar (TL)'] = df_su_borc['tutar'].apply(para_format)
            
            df_su_goster = df_su_borc[['Sec', 'id', 'daire_kodu', 'Malik / Sakin', 'Dönem', 'Tutar (TL)']]
            df_su_goster.columns = ['Seç', 'ID', 'Daire', 'Malik / Sakin', 'Dönem', 'Tutar (TL)']
            
            edited_su_df = st.data_editor(
                df_su_goster, hide_index=True, use_container_width=True, key="su_tahsil_editor",
                disabled=["ID", "Daire", "Malik / Sakin", "Dönem", "Tutar (TL)"],
                column_config={"ID": None}
            )
            aciklama_toplu_su = st.text_input("Su Ödeme Açıklaması", value="EFT/Nakit Su Ödemesi", key="su_ack_input")
            
            if st.button("Seçilen Su Borçlarını Tahsil Et ve Kasaya İşle"):
                secilenler_su = edited_su_df[edited_su_df['Seç'] == True]
                if not secilenler_su.empty:
                    borc_map_su = {b['id']: b for b in su_borclari}
                    tahsilat_listesi_su = []
                    for _, row in secilenler_su.iterrows():
                        b_item = borc_map_su[row['ID']]
                        supabase.table("borclar").update({"odendi": True}).eq("id", b_item['id']).execute()
                        tahsilat_listesi_su.append({
                            "daire_kodu": b_item["daire_kodu"], "tur": "Su", 
                            "tutar": b_item["tutar"], "tarih": datetime.now().strftime("%Y-%m-%d"), "aciklama": aciklama_toplu_su
                        })
                    if tahsilat_listesi_su:
                        supabase.table("tahsilat").insert(tahsilat_listesi_su).execute()
                    st.success(f"Seçilen {len(secilenler_su)} dairenin su ödemesi başarıyla kasaya işlendi!")
                    st.rerun()
                else:
                    st.warning("Lütfen tablodan en az bir daire seçin.")
        else:
            st.info("Ödenmemiş bekleyen su borcu bulunmuyor.")

    with tab4:
        st.subheader("📜 Eski Borç Tahsil Et")
        eski_borclar = supabase.table("borclar").select("*").eq("odendi", False).eq("tur", "Eski Borç").order("daire_kodu").execute().data
        daireler_map = {d["daire_kodu"]: d["sakin_adi"] for d in supabase.table("daireler").select("daire_kodu, sakin_adi").execute().data}
        
        if eski_borclar:
            secenekler_eski = []
            for b in eski_borclar:
                sakin = daireler_map.get(b["daire_kodu"], "")
                secenekler_eski.append((b["id"], f"{b['daire_kodu']} ({sakin}) - {para_format(b['tutar'])}"))
            
            secilen_id_eski = st.selectbox("Ödeme Yapan Daire", options=[s[0] for s in secenekler_eski], format_func=lambda x: [s[1] for s in secenekler_eski if s[0] == x][0])
            aciklama_eski = st.text_input("Açıklama", value="Temmuz Öncesi Eski Borç Ödemesi")
            
            if st.button("Eski Borç Ödemesini Kasaya Kaydet"):
                borc_item = [b for b in eski_borclar if b["id"] == secilen_id_eski][0]
                supabase.table("borclar").update({"odendi": True}).eq("id", secilen_id_eski).execute()
                supabase.table("tahsilat").insert({
                    "daire_kodu": borc_item["daire_kodu"], "tur": "Eski Borç", 
                    "tutar": borc_item["tutar"], "tarih": datetime.now().strftime("%Y-%m-%d"), "aciklama": aciklama_eski
                }).execute()
                st.success("Eski borç tahsilatı kasaya işlendi!")
                st.rerun()
        else:
            st.info("Ödenmemiş eski borç bulunmuyor.")

    with tab5:
        st.subheader("📂 Akbank Ekstresi İle Otomatik Tahsilat Eşleştirme")
        st.info("Akbank'tan indirdiğiniz Excel veya CSV formatındaki hesap ekstresini buraya yükleyin. Sistem açıklamalardaki daire kodunu ve (Aidat/Su) türünü otomatik tespit edecektir.")
        
        ekstre_dosya = st.file_uploader("Akbank Ekstre Dosyası (Excel veya CSV)", type=["xlsx", "xls", "csv"])
        
        if ekstre_dosya is not None:
            try:
                if ekstre_dosya.name.endswith('.csv'):
                    df_ekstre = pd.read_csv(ekstre_dosya)
                else:
                    df_ekstre = pd.read_excel(ekstre_dosya)
                
                st.markdown("### 📄 Yüklenen Ekstre Önizlemesi (Ham Veri)")
                st.dataframe(df_ekstre.head(5), use_container_width=True)
                
                # Sütun isimleri esnekliği için arama
                kolonlar = df_ekstre.columns.tolist()
                aciklama_kolonu = next((c for c in kolonlar if "açıklama" in c.lower() or "detay" in c.lower() or "aciklama" in c.lower()), kolonlar[1] if len(kolonlar) > 1 else kolonlar[0])
                tutar_kolonu = next((c for c in kolonlar if "tutar" in c.lower() or "alacak" in c.lower() or "tutar(tl)" in c.lower()), kolonlar[-1])
                tarih_kolonu = next((c for c in kolonlar if "tarih" in c.lower()), kolonlar[0])
                
                st.success(f"Sütunlar başarıyla eşleşti -> Tarih: `{tarih_kolonu}`, Açıklama: `{aciklama_kolonu}`, Tutar: `{tutar_kolonu}`")
                
                if st.button("Ekstreyi Analiz Et ve Eşleştir"):
                    islenen_satirlar = []
                    
                    for idx, row in df_ekstre.iterrows():
                        aciklama_metni = str(row[aciklama_kolonu])
                        
                        # Tutarı temizle ve sayıya çevir
                        ham_tutar = row[tutar_kolonu]
                        try:
                            if isinstance(ham_tutar, str):
                                temiz_tutar = float(ham_tutar.replace(".", "").replace(",", ".").replace("TL", "").strip())
                            else:
                                temiz_tutar = float(ham_tutar)
                        except:
                            temiz_tutar = 0.0
                            
                        if temiz_tutar <= 0:
                            continue # Giden paraları veya 0 tutarları atla
                            
                        daire_kodu, tahmin_turu = aciklama_analiz_et(aciklama_metni)
                        
                        if daire_kodu:
                            islenen_satirlar.append({
                                "Seç": True,
                                "Index": idx,
                                "Tarih": str(row[tarih_kolonu])[:10],
                                "Daire": daire_kodu,
                                "Tür": tahmin_turu,
                                "Tutar": temiz_tutar,
                                "Açıklama": aciklama_metni
                            })
                            
                    if islenen_satirlar:
                        st.session_state["islenen_ekstre_df"] = pd.DataFrame(islenen_satirlar)
                    else:
                        st.warning("Ekstrede hiçbir daire kodu (Örn: A-1, B-2) yakalanamadı. Lütfen açıklama sütununu kontrol edin.")
                        
            except Exception as e:
                st.error(f"Dosya okunurken bir hata oluştu: {e}")
                
        if "islenen_ekstre_df" in st.session_state and not st.session_state["islenen_ekstre_df"].empty:
            st.markdown("### 🔍 Tespit Edilen Havaleler ve Eşleşmeler")
            st.info("Aşağıdaki listede sistemin otomatik eşleştirdiği ödemeleri görebilirsiniz. Dilerseniz 'Tür' kısmını (Aidat/Su) değiştirebilir ve ardından onaylayabilirsiniz.")
            
            edited_ekstre_islem = st.data_editor(
                st.session_state["islenen_ekstre_df"],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Seç": st.column_config.CheckboxColumn("İşle?"),
                    "Tür": st.column_config.SelectboxColumn("Borç Türü", options=["Aidat", "Su", "Eski Borç"]),
                    "Tutar": st.column_config.NumberColumn("Tutar (TL)", format="%.2f ₺")
                }
            )
            
            if st.button("✅ Seçilen Ekstre Hareketlerini Borçlardan Düş ve Kasaya İşle"):
                secilen_islem_satirlari = edited_ekstre_islem[edited_ekstre_islem["Seç"] == True]
                
                if not secilen_islem_satirlari.empty:
                    basarili_sayisi = 0
                    
                    for _, row in secilen_islem_satirlari.iterrows():
                        d_kodu = row["Daire"]
                        b_turu = row["Tür"]
                        tutar = row["Tutar"]
                        tarih = row["Tarih"]
                        ack = row["Açıklama"]
                        
                        # Bu dairenin o türdeki ödenmemiş borcunu bul
                        bekleyen_borc = supabase.table("borclar").select("*").eq("daire_kodu", d_kodu).eq("tur", b_turu).eq("odendi", False).limit(1).execute().data
                        
                        if bekleyen_borc:
                            borc_id = bekleyen_borc[0]["id"]
                            supabase.table("borclar").update({"odendi": True}).eq("id", borc_id).execute()
                            
                        # Tahsilat tablosuna işle
                        supabase.table("tahsilat").insert({
                            "daire_kodu": d_kodu,
                            "tur": b_turu,
                            "tutar": tutar,
                            "tarih": tarih if len(tarih) == 10 else datetime.now().strftime("%Y-%m-%d"),
                            "aciklama": f"Akbank Ekstre: {ack}"
                        }).execute()
                        
                        basarili_sayisi += 1
                        
                    st.success(f"Başarıyla {basarili_sayisi} adet banka ödemesi eşleştirildi, ilgili borçlar kapatıldı ve kasaya işlendi!")
                    del st.session_state["islenen_ekstre_df"]
                    st.rerun()
                else:
                    st.warning("Lütfen listeden en az bir işlem seçin.")

# --- 4. SU FATURASI GİRİŞİ ---
elif secim == "💧 Su Faturası Girişi" and yonetici_giris_yapildi:
    st.header("💧 Su Faturası ve Bahçe Sulama Paylaşımı")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        toplam_fatura_tutari = st.number_input("Gelen Toplam Su Fatura Bedeli (TL)", min_value=0.0, value=30206.0, step=100.0)
    with col_f2:
        toplam_ana_sayac_tuketimi = st.number_input("Ana Sayaç Toplam Tüketim (m3)", min_value=0.0, value=487.0, step=1.0)
    with col_f3:
        bahce_tuketimi = st.number_input("Bahçe Sulama Tüketimi (m3)", min_value=0.0, value=95.0, step=1.0)
        
    donem_su = st.text_input("Su Faturası Dönemi", value=f"{simdiki_donem_tr} Su")

    mevcut_su_kayit = supabase.table("borclar").select("id").eq("donem", donem_su).eq("tur", "Su").limit(1).execute().data
    if mevcut_su_kayit:
        st.warning(f"'{donem_su}' dönemi için zaten su borcu oluşturulmuş. Tekrar hesaplarsan mükerrer kayıt oluşur.")
    
    st.markdown("### Daire Su Sayaçları (Yeni Endeksleri Tablodan Giriniz)")
    daireler_data = supabase.table("daireler").select("daire_kodu, sakin_adi, son_su_endeks, bahce_orani").order("daire_kodu").execute().data
    
    df_su = pd.DataFrame(daireler_data)
    df_su.columns = ['Daire', 'Sakin Adı', 'Önceki Endeks', 'Bahçe Oranı']
    df_su['Yeni Endeks'] = df_su['Önceki Endeks']
    
    edited_su_df = st.data_editor(
        df_su[['Daire', 'Sakin Adı', 'Önceki Endeks', 'Yeni Endeks']], 
        hide_index=True, 
        use_container_width=True, 
        disabled=["Daire", "Sakin Adı", "Önceki Endeks"],
        key="su_endeks_editor"
    )
    
    if st.button("Değişiklikleri Kaydet ve Su Borçlarını Hesapla"):
        birim_fiyat = toplam_fatura_tutari / toplam_ana_sayac_tuketimi if toplam_ana_sayac_tuketimi > 0 else 0.0
        toplam_bahce_bedeli = bahce_tuketimi * birim_fiyat
        
        toplam_eklenen = 0
        atlanan_daireler = []
        borc_eklemeleri = []
        
        for idx, row in edited_su_df.iterrows():
            d_kodu = row["Daire"]
            onceki = float(row["Önceki Endeks"])
            try:
                yeni = float(row["Yeni Endeks"])
            except:
                yeni = onceki
                
            b_orani = [d["bahce_orani"] for d in daireler_data if d["daire_kodu"] == d_kodu][0] or 0.0
            
            if yeni >= onceki:
                m3_fark = yeni - onceki
                tuketim_bedeli = m3_fark * birim_fiyat
                bahce_sulama_payi = b_orani * toplam_bahce_bedeli
                toplam_tutar = tuketim_bedeli + bahce_sulama_payi
                
                if toplam_tutar > 0:
                    borc_eklemeleri.append({
                        "daire_kodu": d_kodu, "tur": "Su", "tutar": toplam_tutar, 
                        "donem": donem_su, "odendi": False
                    })
                    toplam_eklenen += 1
                
                supabase.table("daireler").update({"son_su_endeks": yeni}).eq("daire_kodu", d_kodu).execute()
            else:
                atlanan_daireler.append(d_kodu)
                
        if borc_eklemeleri:
            supabase.table("borclar").insert(borc_eklemeleri).execute()
            
        st.success(f"Hesaplama tamamlandı! {toplam_eklenen} daire için su borçlandırması yapıldı.")
        if atlanan_daireler:
            st.warning(f"Şu dairelerde yeni endeks eskisinden düşük görünüyor, atlandı (kontrol et): {', '.join(atlanan_daireler)}")

# --- 5. GİDER EKLE & DEKONT TAKİBİ ---
elif secim == "💸 Gider Ekle & Dekont Takibi":
    st.header("💸 Yönetim Giderleri ve Fatura/Dekont Arşivi")
    
    if yonetici_giris_yapildi:
        st.markdown("### ➕ Yeni Gider ve Dekont Ekle")
        with st.form("gider_formu", clear_on_submit=True):
            cg1, cg2 = st.columns(2)
            with cg1:
                kategori = st.selectbox("Gider Kategorisi", ["Asansör Bakımı", "Temizlik / Personel", "Ortak Elektrik", "Ortak Su", "Bahçe Bakımı", "Havuz Bakımı", "Huzur Hakkı", "Tamirat / Tadilat", "Diğer"])
                tutar = st.number_input("Gider Tutarı (TL)", min_value=0.0, step=100.0)
            with cg2:
                dekont_dosya = st.file_uploader("Dekont / Fatura Dosyası Yükle (Resim veya PDF)", type=["png", "jpg", "jpeg", "pdf"])
            
            aciklama = st.text_area("Gider Açıklaması / Detayı")
            if st.form_submit_button("Gideri ve Dekontu Kaydet"):
                dosya_yolu = None
                if dekont_dosya is not None:
                    try:
                        dosya_adi = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{dekont_dosya.name}"
                        supabase.storage.from_(STORAGE_BUCKET).upload(
                            dosya_adi,
                            dekont_dosya.getvalue(),
                            {"content-type": dekont_dosya.type}
                        )
                        dosya_yolu = dosya_adi
                    except Exception as e:
                        st.error(f"Dekont yüklenirken hata oluştu: {e}")
                
                supabase.table("giderler").insert({
                    "kategori": kategori, "tutar": tutar, "tarih": datetime.now().strftime("%Y-%m-%d"), 
                    "aciklama": aciklama, "dekont_yolu": dosya_yolu
                }).execute()
                st.success("Gider dan dekont başarıyla sisteme kaydedildi!")
                st.rerun()
        st.markdown("---")

    st.subheader("📜 Yapılan Harcamalar Listesi")
    giderler_listesi = supabase.table("giderler").select("*").order("id", desc=True).execute().data
    
    if giderler_listesi:
        for g in giderler_listesi:
            formatted_tutari = para_format(g['tutar'])
            with st.expander(f"📌 [{g['tarih']}] {g['kategori']} - **{formatted_tutari}**"):
                st.write(f"**Açıklama:** {g['aciklama'] if g['aciklama'] else 'Açıklama girilmemiş.'}")
                if g['dekont_yolu']:
                    try:
                        dosya_uzanti = g['dekont_yolu'].split('.')[-1].lower()
                        signed = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(g['dekont_yolu'], 3600)
                        signed_url = signed.get('signedURL') or signed.get('signed_url')
                        if dosya_uzanti in ['png', 'jpg', 'jpeg']:
                            st.image(signed_url, caption="İlgili Harcama Dekontu / Faturası", use_container_width=True)
                        else:
                            st.link_button("📥 Dekontu / Faturayı İndir (PDF)", signed_url)
                    except Exception as e:
                        st.warning(f"Dekont görüntülenemedi: {e}")
                else:
                    st.info("Bu harcama için yüklenmiş bir dosya bulunmuyor.")
    else:
        st.info("Henüz sisteme kaydedilmiş bir gider bulunmuyor.")

# --- 6. DAİRE & MUAFİYET AYARLARI ---
elif secim == "⚙️ Daire & Muafiyet Ayarları" and yonetici_giris_yapildi:
    st.header("Daire, Sakin Bilgileri ve Bahçe Oranları")
    
    daireler_data = supabase.table("daireler").select("*").order("daire_kodu").execute().data
    df_daireler = pd.DataFrame(daireler_data)
    df_daireler.columns = ['Daire', 'Sakin Adı', 'Sabit Aidat (TL)', 'Aidattan Muaf Mı?', 'Son Su Endeksi', 'Bahçe Oranı']

    edited_daireler = st.data_editor(df_daireler, use_container_width=True, key="daire_ayarlar_editor")
    
    if st.button("Bilgileri Güncelle"):
        for idx, row in edited_daireler.iterrows():
            supabase.table("daireler").update({
                "sakin_adi": row["Sakin Adı"], 
                "aidat_tutari": float(row["Sabit Aidat (TL)"]), 
                "aidat_muaf": bool(row["Aidattan Muaf Mı?"]), 
                "son_su_endeks": float(row["Son Su Endeksi"]), 
                "bahce_orani": float(row["Bahçe Oranı"])
            }).eq("daire_kodu", row["Daire"]).execute()
        st.success("Daire bilgileri başarıyla güncellendi!")
