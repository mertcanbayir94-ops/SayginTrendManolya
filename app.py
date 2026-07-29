import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# Page Configuration
st.set_page_config(page_title="Manolya Trend Yönetimi", page_icon="🏢", layout="wide")

DB_NAME = "manolya_site.db"
UPLOAD_FOLDER = "dekontlar"

# Dekontların kaydedileceği klasörü oluşturalım
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Türkçe Para Formatı Yardımcı Fonksiyonu (1.250,50 ₺)
def para_format(deger):
    if deger is None:
        deger = 0.0
    # Önce standart 2 haneli stringe çevir, sonra TR formatına uyarla
    tmp = f"{deger:,.2f}"
    tmp = tmp.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{tmp} ₺"

# Türkçe Ay ve Tarih Sözlüğü için yardımcı fonksiyonlar
TURKCE_AYLAR = {
    "January": "Ocak", "February": "Şubat", "March": "Mart", "April": "Nisan",
    "May": "Mayıs", "June": "Haziran", "July": "Temmuz", "August": "Ağustos",
    "September": "Eylül", "October": "Ekim", "November": "Kasım", "December": "Aralık"
}

def turkce_donem_adi(ingilizce_donem):
    for ing, tr in TURKCE_AYLAR.items():
        ingilizce_donem = ingilizce_donem.replace(ing, tr)
    return ingilizce_donem

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Daireler Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daireler (
            daire_kodu TEXT PRIMARY KEY,
            sakin_adi TEXT DEFAULT '',
            aidat_tutari REAL DEFAULT 0.0,
            aidat_muaf BOOLEAN DEFAULT 0,
            son_su_endeks REAL DEFAULT 0.0,
            bahce_orani REAL DEFAULT 0.0
        )
    ''')
    
    cursor.execute("PRAGMA table_info(daireler)")
    columns = [col[1] for col in cursor.fetchall()]
    if "bahce_orani" not in columns:
        cursor.execute("ALTER TABLE daireler ADD COLUMN bahce_orani REAL DEFAULT 0.0")
    
    # 2. Gelirler/Tahsilatlar Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tahsilat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            daire_kodu TEXT,
            tur TEXT,
            tutar REAL,
            tarih TEXT,
            aciklama TEXT
        )
    ''')
    
    # 3. Giderler Tablosu (dekont_yolu sütunu eklendi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giderler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategori TEXT,
            tutar REAL,
            tarih TEXT,
            aciklama TEXT,
            dekont_yolu TEXT
        )
    ''')
    
    cursor.execute("PRAGMA table_info(giderler)")
    gider_cols = [col[1] for col in cursor.fetchall()]
    if "dekont_yolu" not in gider_cols:
        cursor.execute("ALTER TABLE giderler ADD COLUMN dekont_yolu TEXT")

    # 4. Daire Borçları Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS borclar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            daire_kodu TEXT,
            tur TEXT,
            tutar REAL,
            donem TEXT,
            odendi BOOLEAN DEFAULT 0
        )
    ''')

    # Daire Verileri
    daire_verileri = [
        ("A-1", "EDA BÜYÜKYILDIRIM", 2620.0, 0, 0.05702),
        ("A-2", "FATMA CEYLAN", 2210.0, 0, 0.039439),
        ("A-3", "SEVİL BİNCAN", 2030.0, 0, 0.031403),
        ("A-4", "CEREN ÇINAR", 2410.0, 0, 0.047884),
        ("A-5", "VENÜS PALA", 1300.0, 0, 0.0),
        ("A-6", "ÖZLEM ÖZDİLEK", 1300.0, 0, 0.0),
        ("A-7", "ORHUN SEZGİN", 1300.0, 0, 0.0),
        ("A-8", "SALİH ERGONDU", 1300.0, 0, 0.0),
        ("B-1", "EGE OĞUZ", 3790.0, 0, 0.0),
        ("B-2", "ESRA KOÇ-MURAT GÜRKAN KINA", 3520.0, 0, 0.0),
        ("B-3", "YİĞİT ATİLAY", 3370.0, 0, 0.0),
        ("B-4", "EMİN GENÇPINAR", 3710.0, 0, 0.0),
        ("C-1", "NİHAT KARABULUT", 3700.0, 0, 0.0),
        ("C-2", "NİHAT KARABULUT", 3370.0, 0, 0.0),
        ("C-3", "EGE DOĞAN DURMUŞ", 3560.0, 0, 0.0),
        ("C-4", "ERSİN ALTIN", 3860.0, 0, 0.0),
        ("D-1", "GÜLİSTAN COŞKUN", 2680.0, 0, 0.0),
        ("D-2", "TEVFİK TAMER GÜRDEREOĞLU", 2610.0, 0, 0.0),
        ("D-3", "BANU AYTAÇER", 2290.0, 0, 0.0),
        ("D-4", "ASİME DAĞ", 1300.0, 0, 0.0),
        ("D-5", "?", 1300.0, 0, 0.0),
        ("D-6", "İBRAHİM CERİT", 1300.0, 0, 0.0),
        ("E-1", "MURAT YAMAN", 2650.0, 0, 0.0),
        ("E-2", "MERT RECEP SAYGIN", 2230.0, 0, 0.0),
        ("E-3", "CEREN - EZGİ ŞİMŞİR", 1920.0, 0, 0.0),
        ("E-4", "CELAL DAĞDELEN", 2090.0, 0, 0.0),
        ("E-5", "CANAN TOSBAT/JALE TOSBAT", 1300.0, 0, 0.0),
        ("E-6", "HAKAN NURHAN", 1300.0, 0, 0.0),
        ("E-7", "SERDAL YAZĞAN", 1300.0, 0, 0.0),
        ("E-8", "HURİYE FIRTINA", 1300.0, 0, 0.0),
        ("F-1", "BAHADIR DİNÇER", 1930.0, 0, 0.0),
        ("F-2", "MUKADDER AYHAN", 1900.0, 0, 0.0),
        ("F-3", "MEHMET BAŞEĞMEZ", 2040.0, 0, 0.0),
        ("F-4", "ÜNSAL TERLİKLİ", 2120.0, 0, 0.0),
        ("F-5", "SEVİL BİNCAN", 1300.0, 0, 0.0),
        ("F-6", "HAMİYET YONGA", 1300.0, 0, 0.0),
        ("F-7", "EMEL TURAN", 1300.0, 0, 0.0),
        ("F-8", "NURTAÇ GÜLTEN", 1300.0, 0, 0.0),
        ("G-1", "BETÜL ALTIOK", 0.0, 1, 0.0),
        ("G-2", "ECE TEKTEKİN", 0.0, 1, 0.0),
        ("G-3", "CEM ÜNSAL", 0.0, 1, 0.0),
        ("G-4", "HAKAN BİRLİKER", 0.0, 1, 0.0)
    ]

    cursor.execute('SELECT COUNT(*) FROM daireler')
    if cursor.fetchone()[0] == 0:
        for kod, isim, aidat, muaf, boran in daire_verileri:
            cursor.execute('''
                INSERT INTO daireler (daire_kodu, sakin_adi, aidat_tutari, aidat_muaf, son_su_endeks, bahce_orani) 
                VALUES (?, ?, ?, ?, 0.0, ?)
            ''', (kod, isim, aidat, muaf, boran))

    # Eski Borçlar
    eski_borc_verileri = {
        "A-1": 0.0, "A-2": 0.0, "A-3": 17444.66, "A-4": 0.0, "A-5": 15750.00, "A-6": 5250.00, "A-7": 15665.46, "A-8": 15748.43,
        "B-1": 0.0, "B-2": 0.0, "B-3": 0.0, "B-4": 0.0,
        "C-1": 36067.98, "C-2": 36198.43, "C-3": 19015.56, "C-4": 0.0,
        "D-1": 0.0, "D-2": 0.0, "D-3": 0.0, "D-4": 15750.00, "D-5": 16069.72, "D-6": 0.0,
        "E-1": 0.0, "E-2": 0.0, "E-3": 0.0, "E-4": 739.67, "E-5": 0.0, "E-6": 0.0, "E-7": 8629.29, "E-8": 14000.00,
        "F-1": 10643.24, "F-2": 223.38, "F-3": 7580.67, "F-4": 5248.70, "F-5": 17278.81, "F-6": 4800.00, "F-7": 0.0, "F-8": 0.0,
        "G-1": 0.0, "G-2": 0.0, "G-3": 0.0, "G-4": 0.0
    }

    cursor.execute("SELECT COUNT(*) FROM borclar WHERE tur = 'Eski Borç'")
    if cursor.fetchone()[0] == 0:
        for daire, tutar in eski_borc_verileri.items():
            if tutar > 0:
                cursor.execute("INSERT INTO borclar (daire_kodu, tur, tutar, donem, odendi) VALUES (?, 'Eski Borç', ?, 'Temmuz 2026 Öncesi', 0)", (daire, tutar))

    conn.commit()
    conn.close()

init_db()

# Application Title
st.title("🏢 Manolya Trend Site Yönetim Paneli")

# Aktif dönemi Türkçe hazırlama
ing_simdiki_ay = datetime.now().strftime("%B %Y")
simdiki_donem_tr = turkce_donem_adi(ing_simdiki_ay)

# --- SIDEBAR: YÖNETİCİ GİRİŞİ & MENÜ ---
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
    st.caption("Kat malikleri bu ekrandan kendi dairelerini seçerek güncel borç durumlarını ve geçmiş ödemelerini inceleyebilirler.")
    
    conn = get_db_connection()
    daire_listesi = conn.execute("SELECT daire_kodu, sakin_adi FROM daireler ORDER BY daire_kodu ASC").fetchall()
    conn.close()
    
    secilen_daire = st.selectbox(
        "Lütfen Dairenizi Seçin", 
        options=[d["daire_kodu"] for d in daire_listesi],
        format_func=lambda x: f"{x} - {[d['sakin_adi'] for d in daire_listesi if d['daire_kodu'] == x][0]}"
    )
    
    if secilen_daire:
        conn = get_db_connection()
        d_info = conn.execute("SELECT * FROM daireler WHERE daire_kodu = ?", (secilen_daire,)).fetchone()
        
        borclar_df = pd.read_sql_query('''
            SELECT donem AS 'Dönem', tur AS 'Borç Türü', tutar, 
            CASE WHEN odendi = 1 THEN 'Ödendi ✅' ELSE 'Ödenmedi ❌' END AS 'Durum'
            FROM borclar WHERE daire_kodu = ? ORDER BY id DESC
        ''', conn, params=(secilen_daire,))
        
        tahsilat_df = pd.read_sql_query('''
            SELECT tarih AS 'Ödeme Tarihi', tur AS 'Ödeme Türü', tutar, aciklama AS 'Açıklama'
            FROM tahsilat WHERE daire_kodu = ? ORDER BY id DESC
        ''', conn, params=(secilen_daire,))
        
        kalan_borc = conn.execute("SELECT SUM(tutar) FROM borclar WHERE daire_kodu = ? AND odendi = 0", (secilen_daire,)).fetchone()[0] or 0.0
        toplam_odenen = conn.execute("SELECT SUM(tutar) FROM tahsilat WHERE daire_kodu = ?", (secilen_daire,)).fetchone()[0] or 0.0
        conn.close()
        
        # Tablolardaki tutar sütunlarına TR formatı uygulama
        if not borclar_df.empty:
            borclar_df['Tutar (TL)'] = borclar_df['tutar'].apply(para_format)
            borclar_df = borclar_df.drop(columns=['tutar'])
            
        if not tahsilat_df.empty:
            tahsilat_df['Ödenen Tutar (TL)'] = tahsilat_df['tutar'].apply(para_format)
            tahsilat_df = tahsilat_df.drop(columns=['tutar'])

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
                borclar_df['Dönem'] = borclar_df['Dönem'].apply(lambda x: turkce_donem_adi(str(x)))
                st.dataframe(borclar_df, use_container_width=True)
            else:
                st.info("Bu daireye ait borç kaydı bulunmuyor.")
                
        with c2:
            st.subheader("💰 Yapılan Geçmiş Ödemeler")
            if not tahsilat_df.empty:
                st.dataframe(tahsilat_df, use_container_width=True)
            else:
                st.info("Bu daireye ait geçmiş ödeme kaydı bulunmuyor.")

# --- 2. DASHBOARD / KASA (HERKES GÖREBİLİR) ---
elif secim == "📊 Dashboard / Kasa":
    st.header("🏢 Kasa ve Genel Site Durumu")
    st.caption("Sitenin güncel kasa durumunu, toplam gelir-gider dengesini ve bekleyen alacakları şeffaf bir şekilde inceleyebilirsiniz.")
    
    conn = get_db_connection()
    toplam_gelir = conn.execute("SELECT SUM(tutar) FROM tahsilat").fetchone()[0] or 0.0
    toplam_gider = conn.execute("SELECT SUM(tutar) FROM giderler").fetchone()[0] or 0.0
    kasa = toplam_gelir - toplam_gider
    
    toplam_alacak = conn.execute("SELECT SUM(tutar) FROM borclar WHERE odendi = 0").fetchone()[0] or 0.0
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Mevcut Kasa Bakiye", para_format(kasa))
    col2.metric("📈 Toplam Tahsilat", para_format(toplam_gelir))
    col3.metric("📉 Toplam Gider", para_format(toplam_gider))
    col4.metric("⚠️ Bekleyen Toplam Alacak", para_format(toplam_alacak))

    st.markdown("---")
    st.subheader("📋 Ödenmeyen Borçlar Listesi (Eski Borç, Aidat ve Su)")
    conn = get_db_connection()
    bekleyen_df = pd.read_sql_query('''
        SELECT b.daire_kodu AS 'Daire', d.sakin_adi AS 'Malik/Sakin', b.tur AS 'Borç Türü', b.tutar, b.donem AS 'Dönem' 
        FROM borclar b
        LEFT JOIN daireler d ON b.daire_kodu = d.daire_kodu
        WHERE b.odendi = 0 
        ORDER BY b.daire_kodu ASC
    ''', conn)
    conn.close()
    
    if not bekleyen_df.empty:
        bekleyen_df['Tutar (TL)'] = bekleyen_df['tutar'].apply(para_format)
        bekleyen_df = bekleyen_df.drop(columns=['tutar'])
        bekleyen_df['Dönem'] = bekleyen_df['Dönem'].apply(lambda x: turkce_donem_adi(str(x)))
        st.dataframe(bekleyen_df, use_container_width=True)
    else:
        st.success("Tüm borçlar ödenmiş, harika!")

# --- 3. TAHSİLAT YÖNETİMİ ---
elif secim == "💳 Tahsilat Yönetimi (Aidat / Su / Eski Borç)" and yonetici_giris_yapildi:
    st.header("Tahsilat Yönetimi")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📌 Toplu Aidat Borçlandır", "💳 Aidat Tahsil Et", "💧 Su Tahsil Et", "📜 Eski Borç Tahsil Et"])
    
    with tab1:
        st.subheader("Tüm Dairelere Özel Aidat Borcu Yansıt")
        donem = st.text_input("Dönem / Ay", value=simdiki_donem_tr)
        
        if st.button("Toplu Aidat Yansıt"):
            conn = get_db_connection()
            daireler = conn.execute("SELECT daire_kodu, aidat_tutari FROM daireler WHERE aidat_muaf = 0").fetchall()
            for d in daireler:
                conn.execute("INSERT INTO borclar (daire_kodu, tur, tutar, donem, odendi) VALUES (?, 'Aidat', ?, ?, 0)",
                             (d['daire_kodu'], d['aidat_tutari'], donem))
            conn.commit()
            conn.close()
            st.success(f"{len(daireler)} daireye özel aidat borçları başarıyla eklendi!")

    with tab2:
        st.subheader("💳 Aidat Ödemesi Tahsil Et")
        secim_sekli_aidat = st.radio("İşlem Modu", ["Tekli İşlem", "⚡ Toplu Tablodan Çoklu Seçim"], key="aidat_mod")
        
        conn = get_db_connection()
        aidat_borclari_df = pd.read_sql_query('''
            SELECT b.id, b.daire_kodu AS 'Daire', d.sakin_adi AS 'Sakin Adı', b.tutar, b.donem AS 'Dönem'
            FROM borclar b
            LEFT JOIN daireler d ON b.daire_kodu = d.daire_kodu
            WHERE b.odendi = 0 AND b.tur = 'Aidat'
            ORDER BY b.daire_kodu ASC
        ''', conn)
        conn.close()
        
        if not aidat_borclari_df.empty:
            aidat_borclari_df['Dönem'] = aidat_borclari_df['Dönem'].apply(lambda x: turkce_donem_adi(str(x)))
            if secim_sekli_aidat == "Tekli İşlem":
                borc_secimi = st.selectbox(
                    "Ödeme Yapan Daire (Aidat)", 
                    options=aidat_borclari_df['id'], 
                    format_func=lambda x: f"{aidat_borclari_df[aidat_borclari_df['id']==x]['Daire'].values[0]} ({aidat_borclari_df[aidat_borclari_df['id']==x]['Sakin Adı'].values[0]}) - {aidat_borclari_df[aidat_borclari_df['id']==x]['Dönem'].values[0]} - {para_format(aidat_borclari_df[aidat_borclari_df['id']==x]['tutar'].values[0])}"
                )
                aciklama_tek = st.text_input("Açıklama", value="EFT/Nakit Aidat Ödemesi", key="tek_aidat_ack")
                
                if st.button("Aidat Ödemesini Kasaya Kaydet"):
                    conn = get_db_connection()
                    row = aidat_borclari_df[aidat_borclari_df['id'] == borc_secimi].iloc[0]
                    conn.execute("UPDATE borclar SET odendi = 1 WHERE id = ?", (borc_secimi,))
                    conn.execute("INSERT INTO tahsilat (daire_kodu, tur, tutar, tarih, aciklama) VALUES (?, 'Aidat', ?, ?, ?)",
                                 (row['Daire'], row['tutar'], datetime.now().strftime("%Y-%m-%d"), aciklama_tek))
                    conn.commit()
                    conn.close()
                    st.success("Aidat tahsilatı başarıyla kasaya işlendi!")
                    st.rerun()
            else:
                aidat_borclari_df['Tutar (TL)'] = aidat_borclari_df['tutar'].apply(para_format)
                display_aidat = aidat_borclari_df[['id', 'Daire', 'Sakin Adı', 'Tutar (TL)', 'Dönem']].copy()
                display_aidat.insert(0, "Seç", False)
                edited_aidat = st.data_editor(display_aidat, hide_index=True, use_container_width=True, disabled=["id", "Daire", "Sakin Adı", "Tutar (TL)", "Dönem"])
                aciklama_toplu_aidat = st.text_input("Toplu Açıklama", value="Toplu Aidat Tahsilatı", key="toplu_aidat_ack")
                
                if st.button("Seçilen Aidatları Tahsil Et ve Kasaya Ekle"):
                    secilenler = edited_aidat[edited_aidat["Seç"] == True]
                    if not secilenler.empty:
                        conn = get_db_connection()
                        bugun = datetime.now().strftime("%Y-%m-%d")
                        for idx, row in secilenler.iterrows():
                            orijinal_tutar = aidat_borclari_df[aidat_borclari_df['id'] == row['id']]['tutar'].values[0]
                            conn.execute("UPDATE borclar SET odendi = 1 WHERE id = ?", (row["id"],))
                            conn.execute("INSERT INTO tahsilat (daire_kodu, tur, tutar, tarih, aciklama) VALUES (?, 'Aidat', ?, ?, ?)",
                                         (row["Daire"], orijinal_tutar, bugun, aciklama_toplu_aidat))
                        conn.commit()
                        conn.close()
                        st.success(f"Seçilen {len(secilenler)} adet aidat ödemesi kasaya işlendi!")
                        st.rerun()
        else:
            st.info("Ödenmemiş bekleyen aidat borcu bulunmuyor.")

    with tab3:
        st.subheader("💧 Su Ödemesi Tahsil Et")
        secim_sekli_su = st.radio("İşlem Modu", ["Tekli İşlem", "⚡ Toplu Tablodan Çoklu Seçim"], key="su_mod")
        
        conn = get_db_connection()
        su_borclari_df = pd.read_sql_query('''
            SELECT b.id, b.daire_kodu AS 'Daire', d.sakin_adi AS 'Sakin Adı', b.tutar, b.donem AS 'Dönem'
            FROM borclar b
            LEFT JOIN daireler d ON b.daire_kodu = d.daire_kodu
            WHERE b.odendi = 0 AND b.tur = 'Su'
            ORDER BY b.daire_kodu ASC
        ''', conn)
        conn.close()
        
        if not su_borclari_df.empty:
            su_borclari_df['Dönem'] = su_borclari_df['Dönem'].apply(lambda x: turkce_donem_adi(str(x)))
            if secim_sekli_su == "Tekli İşlem":
                borc_secimi_su = st.selectbox(
                    "Ödeme Yapan Daire (Su)", 
                    options=su_borclari_df['id'], 
                    format_func=lambda x: f"{su_borclari_df[su_borclari_df['id']==x]['Daire'].values[0]} ({su_borclari_df[su_borclari_df['id']==x]['Sakin Adı'].values[0]}) - {su_borclari_df[su_borclari_df['id']==x]['Dönem'].values[0]} - {para_format(su_borclari_df[su_borclari_df['id']==x]['tutar'].values[0])}"
                )
                aciklama_tek_su = st.text_input("Açıklama", value="EFT/Nakit Su Faturası Ödemesi", key="tek_su_ack")
                
                if st.button("Su Ödemesini Kasaya Kaydet"):
                    conn = get_db_connection()
                    row = su_borclari_df[su_borclari_df['id'] == borc_secimi_su].iloc[0]
                    conn.execute("UPDATE borclar SET odendi = 1 WHERE id = ?", (borc_secimi_su,))
                    conn.execute("INSERT INTO tahsilat (daire_kodu, tur, tutar, tarih, aciklama) VALUES (?, 'Su', ?, ?, ?)",
                                 (row['Daire'], row['tutar'], datetime.now().strftime("%Y-%m-%d"), aciklama_tek_su))
                    conn.commit()
                    conn.close()
                    st.success("Su tahsilatı başarıyla kasaya işlendi!")
                    st.rerun()
            else:
                su_borclari_df['Tutar (TL)'] = su_borclari_df['tutar'].apply(para_format)
                display_su = su_borclari_df[['id', 'Daire', 'Sakin Adı', 'Tutar (TL)', 'Dönem']].copy()
                display_su.insert(0, "Seç", False)
                edited_su_tahsil = st.data_editor(display_su, hide_index=True, use_container_width=True, disabled=["id", "Daire", "Sakin Adı", "Tutar (TL)", "Dönem"])
                aciklama_toplu_su = st.text_input("Toplu Açıklama", value="Toplu Su Tahsilatı", key="toplu_su_ack")
                
                if st.button("Seçilen Su Borçlarını Tahsil Et ve Kasaya Ekle"):
                    secilenler_su = edited_su_tahsil[edited_su_tahsil["Seç"] == True]
                    if not secilenler_su.empty:
                        conn = get_db_connection()
                        bugun = datetime.now().strftime("%Y-%m-%d")
                        for idx, row in secilenler_su.iterrows():
                            orijinal_tutar = su_borclari_df[su_borclari_df['id'] == row['id']]['tutar'].values[0]
                            conn.execute("UPDATE borclar SET odendi = 1 WHERE id = ?", (row["id"],))
                            conn.execute("INSERT INTO tahsilat (daire_kodu, tur, tutar, tarih, aciklama) VALUES (?, 'Su', ?, ?, ?)",
                                         (row["Daire"], orijinal_tutar, bugun, aciklama_toplu_su))
                        conn.commit()
                        conn.close()
                        st.success(f"Seçilen {len(secilenler_su)} adet su ödemesi kasaya işlendi!")
                        st.rerun()
        else:
            st.info("Ödenmemiş bekleyen su borcu bulunmuyor.")

    with tab4:
        st.subheader("📜 Eski Borç (Devir) Tahsil Et")
        conn = get_db_connection()
        eski_borclar_df = pd.read_sql_query('''
            SELECT b.id, b.daire_kodu AS 'Daire', d.sakin_adi AS 'Sakin Adı', b.tutar, b.donem AS 'Dönem'
            FROM borclar b
            LEFT JOIN daireler d ON b.daire_kodu = d.daire_kodu
            WHERE b.odendi = 0 AND b.tur = 'Eski Borç'
            ORDER BY b.daire_kodu ASC
        ''', conn)
        conn.close()
        
        if not eski_borclar_df.empty:
            secilen_eski_borc = st.selectbox(
                "Ödeme Yapan Daire (Eski Borç)", 
                options=eski_borclar_df['id'], 
                format_func=lambda x: f"{eski_borclar_df[eski_borclar_df['id']==x]['Daire'].values[0]} ({eski_borclar_df[eski_borclar_df['id']==x]['Sakin Adı'].values[0]}) - {para_format(eski_borclar_df[eski_borclar_df['id']==x]['tutar'].values[0])}"
            )
            aciklama_eski = st.text_input("Açıklama", value="Temmuz Öncesi Eski Borç Ödemesi", key="eski_ack")
            
            if st.button("Eski Borç Ödemesini Kasaya Kaydet"):
                conn = get_db_connection()
                row = eski_borclar_df[eski_borclar_df['id'] == secilen_eski_borc].iloc[0]
                conn.execute("UPDATE borclar SET odendi = 1 WHERE id = ?", (secilen_eski_borc,))
                conn.execute("INSERT INTO tahsilat (daire_kodu, tur, tutar, tarih, aciklama) VALUES (?, 'Eski Borç', ?, ?, ?)",
                             (row['Daire'], row['tutar'], datetime.now().strftime("%Y-%m-%d"), aciklama_eski))
                conn.commit()
                conn.close()
                st.success("Eski borç tahsilatı başarıyla kasaya işlendi!")
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
    
    conn = get_db_connection()
    df_su = pd.read_sql_query('''
        SELECT daire_kodu AS 'Daire', sakin_adi AS 'Sakin Adı', son_su_endeks AS 'Önceki Endeks', son_su_endeks AS 'Yeni Endeks'
        FROM daireler ORDER BY daire_kodu ASC
    ''', conn)
    conn.close()
    
    edited_su_df = st.data_editor(df_su, hide_index=True, use_container_width=True, disabled=["Daire", "Sakin Adı", "Önceki Endeks"])
    
    if st.button("Değişiklikleri Kaydet ve Su Borçlarını Hesapla"):
        birim_fiyat = toplam_fatura_tutari / toplam_ana_sayac_tuketimi if toplam_ana_sayac_tuketimi > 0 else 0.0
        toplam_bahce_bedeli = bahce_tuketimi * birim_fiyat
        
        conn = get_db_connection()
        toplam_eklenen = 0
        
        for idx, row in edited_su_df.iterrows():
            d_kodu = row["Daire"]
            onceki = float(row["Önceki Endeks"])
            try:
                yeni = float(row["Yeni Endeks"])
            except ValueError:
                yeni = onceki
                
            b_orani = conn.execute("SELECT bahce_orani FROM daireler WHERE daire_kodu = ?", (d_kodu,)).fetchone()[0] or 0.0
            
            if yeni >= onceki:
                m3_fark = yeni - onceki
                tuketim_bedeli = m3_fark * birim_fiyat
                bahce_sulama_payi = b_orani * toplam_bahce_bedeli
                toplam_tutar = tuketim_bedeli + bahce_sulama_payi
                
                if toplam_tutar > 0:
                    conn.execute("INSERT INTO borclar (daire_kodu, tur, tutar, donem, odendi) VALUES (?, 'Su', ?, ?, 0)",
                                 (d_kodu, toplam_tutar, donem_su))
                    toplam_eklenen += 1
                conn.execute("UPDATE daireler SET son_su_endeks = ? WHERE daire_kodu = ?", (yeni, d_kodu))
                
        conn.commit()
        conn.close()
        st.success(f"Hesaplama tamamlandı! {toplam_eklenen} daire için su borçlandırması yapıldı.")

# --- 5. GİDER EKLE & DEKONT TAKİBİ ---
elif secim == "💸 Gider Ekle & Dekont Takibi":
    st.header("💸 Yönetim Giderleri ve Fatura/Dekont Arşivi")
    st.caption("Yapılan tüm harcamaları, açıklamalarını ve harcamaya ait resmi dekont/faturaları buradan şeffaf bir şekilde inceleyebilirsiniz.")
    
    if yonetici_giris_yapildi:
        st.markdown("### ➕ Yeni Gider ve Dekont Ekle (Yönetici Paneli)")
        with st.form("gider_formu", clear_on_submit=True):
            cg1, cg2 = st.columns(2)
            with cg1:
                kategori = st.selectbox("Gider Kategorisi", ["Asansör Bakımı", "Temizlik / Personel", "Ortak Elektrik", "Ortak Su", "Bahçe Bakımı", "Tamirat / Tadilat", "Diğer"])
                tutar = st.number_input("Gider Tutarı (TL)", min_value=0.0, step=100.0)
            with cg2:
                dekont_dosya = st.file_uploader("Dekont / Fatura Dosyası Yükle (Resim veya PDF)", type=["png", "jpg", "jpeg", "pdf"])
            
            aciklama = st.text_area("Gider Açıklaması / Detayı")
            gider_kaydet_btn = st.form_submit_button("Gideri ve Dekontu Kaydet")
            
            if gider_kaydet_btn:
                dosya_yolu = None
                if dekont_dosya is not None:
                    dosya_adi = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{dekont_dosya.name}"
                    dosya_yolu = os.path.join(UPLOAD_FOLDER, dosya_adi)
                    with open(dosya_yolu, "wb") as f:
                        f.write(dekont_dosya.getbuffer())
                
                conn = get_db_connection()
                conn.execute("INSERT INTO giderler (kategori, tutar, tarih, aciklama, dekont_yolu) VALUES (?, ?, ?, ?, ?)",
                             (kategori, tutar, datetime.now().strftime("%Y-%m-%d"), aciklama, dosya_yolu))
                conn.commit()
                conn.close()
                st.success("Gider ve dekont başarıyla sisteme kaydedildi!")
                st.rerun()
        st.markdown("---")

    st.subheader("📜 Yapılan Harcamalar Listesi ve Dekontlar")
    conn = get_db_connection()
    giderler_listesi = conn.execute("SELECT * FROM giderler ORDER BY id DESC").fetchall()
    conn.close()
    
    if giderler_listesi:
        for g in giderler_listesi:
            formatted_gider_tutari = para_format(g['tutar'])
            with st.expander(f"📌 [{g['tarih']}] {g['kategori']} - **{formatted_gider_tutari}**"):
                st.write(f"**Açıklama:** {g['aciklama'] if g['aciklama'] else 'Açıklama girilmemiş.'}")
                
                if g['dekont_yolu'] and os.path.exists(g['dekont_yolu']):
                    dosya_uzanti = g['dekont_yolu'].split('.')[-1].lower()
                    if dosya_uzanti in ['png', 'jpg', 'jpeg']:
                        st.image(g['dekont_yolu'], caption="İlgili Harcama Dekontu / Faturası", use_container_width=True)
                    else:
                        with open(g['dekont_yolu'], "rb") as f:
                            st.download_button(
                                label="📥 Dekontu / Faturayı İndir (PDF)",
                                data=f,
                                file_name=os.path.basename(g['dekont_yolu']),
                                mime="application/pdf",
                                key=f"pdf_down_{g['id']}"
                            )
                else:
                    st.info("Bu harcama için yüklenmiş bir dekont/fatura bulunmuyor.")
    else:
        st.info("Henüz sisteme kaydedilmiş bir gider bulunmuyor.")

# --- 6. DAİRE & MUAFİYET AYARLARI ---
elif secim == "⚙️ Daire & Muafiyet Ayarları" and yonetici_giris_yapildi:
    st.header("Daire, Sakin Bilgileri ve Bahçe Oranları")
    
    conn = get_db_connection()
    df_daireler = pd.read_sql_query('''
        SELECT daire_kodu AS 'Daire', sakin_adi AS 'Sakin Adı', aidat_tutari AS 'Sabit Aidat (TL)', aidat_muaf AS 'Aidattan Muaf Mı?', son_su_endeks AS 'Son Su Endeksi', bahce_orani AS 'Bahçe Oranı' 
        FROM daireler
    ''', conn)
    conn.close()

    edited_daireler = st.data_editor(df_daireler, use_container_width=True)
    
    if st.button("Bilgileri Güncelle"):
        conn = get_db_connection()
        for idx, row in edited_daireler.iterrows():
            conn.execute('''
                UPDATE daireler 
                SET sakin_adi = ?, aidat_tutari = ?, aidat_muaf = ?, son_su_endeks = ?, bahce_orani = ? 
                WHERE daire_kodu = ?
            ''', (row["Sakin Adı"], float(row["Sabit Aidat (TL)"]), int(row["Aidattan Muaf Mı?"]), float(row["Son Su Endeksi"]), float(row["Bahçe Oranı"]), row["Daire"]))
        conn.commit()
        conn.close()
        st.success("Daire bilgileri güncellendi!")
