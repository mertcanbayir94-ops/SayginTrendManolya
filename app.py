import streamlit as st
import pandas as pd
from datetime import datetime
import os
from supabase import create_client, Client

# Page Configuration
st.set_page_config(page_title="Manolya Trend Yönetimi", page_icon="🏢", layout="wide")

UPLOAD_FOLDER = "dekontlar"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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

# İlk Kurulum / Tablo Kontrolü ve Varsayılan Veriler
def init_db():
    try:
        res = supabase.table("daireler").select("*", count="exact").execute()
        if res.count == 0 or not res.data:
            daire_verileri = [
                {"daire_kodu": "A-1", "sakin_adi": "EDA BÜYÜKYILDIRIM", "aidat_tutari": 2620.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.05702},
                {"daire_kodu": "A-2", "sakin_adi": "FATMA CEYLAN", "aidat_tutari": 2210.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.039439},
                {"daire_kodu": "A-3", "sakin_adi": "SEVİL BİNCAN", "aidat_tutari": 2030.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.031403},
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
                {"daire_kodu": "D-5", "sakin_adi": "?", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
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
                {"daire_kodu": "F-5", "sakin_adi": "SEVİL BİNCAN", "aidat_tutari": 1300.0, "aidat_muaf": False, "son_su_endeks": 0.0, "bahce_orani": 0.0},
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
yonetici_giris_yapildi = (yonetici_sifresi == "1234")

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

# --- 3. TAHSİLAT YÖNETİMİ ---
elif secim == "💳 Tahsilat Yönetimi (Aidat / Su / Eski Borç)" and yonetici_giris_yapildi:
    st.header("💳 Tahsilat Yönetimi")
    tab1, tab2, tab3, tab4 = st.tabs(["📌 Toplu Aidat Borçlandır", "💳 Aidat Tahsil Et", "💧 Su Tahsil Et", "📜 Eski Borç Tahsil Et"])
    
    with tab1:
        st.subheader("Tüm Dairelere Özel Aidat Borcu Yansıt")
        donem = st.text_input("Dönem / Ay", value=simdiki_donem_tr)
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

    with tab2:
        st.subheader("💳 Aidat Ödemesi Tahsil Et (Tekli & Toplu)")
        aidat_borclari = supabase.table("borclar").select("*").eq("odendi", False).eq("tur", "Aidat").order("daire_kodu").execute().data
        daireler_map = {d["daire_kodu"]: d["sakin_adi"] for d in supabase.table("daireler").select("daire_kodu, sakin_adi").execute().data}
        
        if aidat_borclari:
            secenekler = []
            for b in aidat_borclari:
                sakin = daireler_map.get(b["daire_kodu"], "")
                secenekler.append((b["id"], f"{b['daire_kodu']} ({sakin}) - {turkce_donem_adi(b['donem'])} - {para_format(b['tutar'])}"))
            
            secilen_id = st.selectbox("Ödeme Yapan Daire (Tekli Aidat)", options=[s[0] for s in secenekler], format_func=lambda x: [s[1] for s in secenekler if s[0] == x][0])
            aciklama_tek = st.text_input("Açıklama", value="EFT/Nakit Aidat Ödemesi")
            
            if st.button("Aidat Ödemesini Kasaya Kaydet"):
                borc_item = [b for b in aidat_borclari if b["id"] == secilen_id][0]
                supabase.table("borclar").update({"odendi": True}).eq("id", secilen_id).execute()
                supabase.table("tahsilat").insert({
                    "daire_kodu": borc_item["daire_kodu"], "tur": "Aidat", 
                    "tutar": borc_item["tutar"], "tarih": datetime.now().strftime("%Y-%m-%d"), "aciklama": aciklama_tek
                }).execute()
                st.success("Aidat tahsilatı başarıyla kasaya işlendi!")
                st.rerun()

            st.markdown("---")
            st.subheader("⚡ Toplu Aidat Tahsil Et (Birden Fazla Daire)")
            secilen_coklu_aidat = st.multiselect("Tahsil Edilecek Aidat Borçları", options=[s[0] for s in secenekler], format_func=lambda x: [s[1] for s in secenekler if s[0] == x][0])
            aciklama_toplu = st.text_input("Toplu Ödeme Açıklaması", value="Toplu Aidat Tahsilatı")
            
            if st.button("Seçilen Tüm Aidatları Tahsil Et ve Kasaya Ekle"):
                if secilen_coklu_aidat:
                    tahsilat_listesi = []
                    for sid in secilen_coklu_aidat:
                        b_item = [b for b in aidat_borclari if b["id"] == sid][0]
                        supabase.table("borclar").update({"odendi": True}).eq("id", sid).execute()
                        tahsilat_listesi.append({
                            "daire_kodu": b_item["daire_kodu"], "tur": "Aidat", 
                            "tutar": b_item["tutar"], "tarih": datetime.now().strftime("%Y-%m-%d"), "aciklama": aciklama_toplu
                        })
                    if tahsilat_listesi:
                        supabase.table("tahsilat").insert(tahsilat_listesi).execute()
                    st.success(f"Seçilen {len(secilen_coklu_aidat)} dairenin aidat ödemesi başarıyla kasaya işlendi!")
                    st.rerun()
                else:
                    st.warning("Lütfen en az bir daire seçin.")
        else:
            st.info("Ödenmemiş bekleyen aidat borcu bulunmuyor.")

    with tab3:
        st.subheader("💧 Su Ödemesi Tahsil Et (Tekli & Toplu)")
        su_borclari = supabase.table("borclar").select("*").eq("odendi", False).eq("tur", "Su").order("daire_kodu").execute().data
        daireler_map = {d["daire_kodu"]: d["sakin_adi"] for d in supabase.table("daireler").select("daire_kodu, sakin_adi").execute().data}
        
        if su_borclari:
            secenekler_su = []
            for b in su_borclari:
                sakin = daireler_map.get(b["daire_kodu"], "")
                secenekler_su.append((b["id"], f"{b['daire_kodu']} ({sakin}) - {turkce_donem_adi(b['donem'])} - {para_format(b['tutar'])}"))
            
            secilen_id_su = st.selectbox("Ödeme Yapan Daire (Tekli Su)", options=[s[0] for s in secenekler_su], format_func=lambda x: [s[1] for s in secenekler_su if s[0] == x][0], key="su_sec")
            aciklama_tek_su = st.text_input("Açıklama", value="EFT/Nakit Su Ödemesi", key="su_ack")
            
            if st.button("Su Ödemesini Kasaya Kaydet"):
                borc_item = [b for b in su_borclari if b["id"] == secilen_id_su][0]
                supabase.table("borclar").update({"odendi": True}).eq("id", secilen_id_su).execute()
                supabase.table("tahsilat").insert({
                    "daire_kodu": borc_item["daire_kodu"], "tur": "Su", 
                    "tutar": borc_item["tutar"], "tarih": datetime.now().strftime("%Y-%m-%d"), "aciklama": aciklama_tek_su
                }).execute()
                st.success("Su tahsilatı başarıyla kasaya işlendi!")
                st.rerun()

            st.markdown("---")
            st.subheader("⚡ Toplu Su Tahsil Et (Birden Fazla Daire)")
            secilen_coklu_su = st.multiselect("Tahsil Edilecek Su Borçları", options=[s[0] for s in secenekler_su], format_func=lambda x: [s[1] for s in secenekler_su if s[0] == x][0], key="su_coklu_sec")
            aciklama_toplu_su = st.text_input("Toplu Su Ödeme Açıklaması", value="Toplu Su Tahsilatı", key="su_coklu_ack")
            
            if st.button("Seçilen Tüm Su Borçlarını Tahsil Et ve Kasaya Ekle"):
                if secilen_coklu_su:
                    tahsilat_listesi_su = []
                    for sid in secilen_coklu_su:
                        b_item = [b for b in su_borclari if b["id"] == sid][0]
                        supabase.table("borclar").update({"odendi": True}).eq("id", sid).execute()
                        tahsilat_listesi_su.append({
                            "daire_kodu": b_item["daire_kodu"], "tur": "Su", 
                            "tutar": b_item["tutar"], "tarih": datetime.now().strftime("%Y-%m-%d"), "aciklama": aciklama_toplu_su
                        })
                    if tahsilat_listesi_su:
                        supabase.table("tahsilat").insert(tahsilat_listesi_su).execute()
                    st.success(f"Seçilen {len(secilen_coklu_su)} dairenin su ödemesi başarıyla kasaya işlendi!")
                    st.rerun()
                else:
                    st.warning("Lütfen en az bir daire seçin.")
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
    
    st.markdown("### Daire Su Sayaçları (Yeni Endeksleri Tablodan Giriniz)")
    daireler_data = supabase.table("daireler").select("daire_kodu, sakin_adi, son_su_endeks, bahce_orani").order("daire_kodu").execute().data
    
    df_su = pd.DataFrame(daireler_data)
    df_su.columns = ['Daire', 'Sakin Adı', 'Önceki Endeks', 'Bahçe Oranı']
    df_su['Yeni Endeks'] = df_su['Önceki Endeks']
    
    # Tablo üzerinden doğrudan düzenlenebilir alan (İstediğiniz gibi tablodan seçim yapılıyor)
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
                
        if borc_eklemeleri:
            supabase.table("borclar").insert(borc_eklemeleri).execute()
            
        st.success(f"Hesaplama tamamlandı! {toplam_eklenen} daire için su borçlandırması yapıldı.")

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
                    dosya_adi = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{dekont_dosya.name}"
                    dosya_yolu = os.path.join(UPLOAD_FOLDER, dosya_adi)
                    with open(dosya_yolu, "wb") as f:
                        f.write(dekont_dosya.getbuffer())
                
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
                if g['dekont_yolu'] and os.path.exists(g['dekont_yolu']):
                    dosya_uzanti = g['dekont_yolu'].split('.')[-1].lower()
                    if dosya_uzanti in ['png', 'jpg', 'jpeg']:
                        st.image(g['dekont_yolu'], caption="İlgili Harcama Dekontu / Faturası", use_container_width=True)
                    else:
                        with open(g['dekont_yolu'], "rb") as f:
                            st.download_button(
                                label="📥 Dekontu / Faturayı İndir (PDF)",
                                data=f, file_name=os.path.basename(g['dekont_yolu']),
                                mime="application/pdf", key=f"pdf_down_{g['id']}"
                            )
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
