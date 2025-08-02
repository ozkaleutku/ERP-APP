import sqlite3
import os
import datetime

DB_PATH = 'erp_database.db'

def create_database():
    try:
        if not os.path.exists(DB_PATH):
            open(DB_PATH, 'w').close()
            print(f"Veritabanı oluşturuldu: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS malzemetypes (
            stokkodu TEXT PRIMARY KEY,
            isim TEXT NOT NULL,
            kategori TEXT,
            fotograf BLOB
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS kisiler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kisiisim TEXT NOT NULL,
            bulunankat INTEGER,
            bulunansube TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategoriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategori_adi TEXT UNIQUE NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        print("Veritabanı ve tablolar hazır.")
        return True
    except Exception as e:
        print(f"Veritabanı oluşturma hatası: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def create_stokkodu_table(stokkodu):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        table_name = f"stok_{stokkodu.replace(' ', '').replace('-', '_')}"
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stickerkod TEXT UNIQUE NOT NULL,
                isim TEXT NOT NULL,
                kategori TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        conn.commit()
        conn.close()
        print(f"'{stokkodu}' için stok tablosu oluşturuldu: {table_name}")
        return True
    except Exception as e:
        print(f"Stok tablosu oluşturma hatası: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def create_kisi_malzemeleri_table(kisiisim):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        table_name = f"{kisiisim}_malzemeleri".replace(' ', '').lower()
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stickerid TEXT UNIQUE NOT NULL,
            isim TEXT NOT NULL,
            olusturmatarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        conn.close()
        print(f"'{kisiisim}' için malzemeler tablosu oluşturuldu: {table_name}")
        return True
    except Exception as e:
        print(f"Kişi malzemeleri tablosu oluşturma hatası: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def add_kisi(kisiisim, bulunankat, bulunansube):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM kisiler WHERE kisiisim = ?', (kisiisim,))
        if cursor.fetchone():
            print(f"'{kisiisim}' zaten veritabanında mevcut!")
            conn.close()
            return -1
        cursor.execute('INSERT INTO kisiler (kisiisim, bulunankat, bulunansube) VALUES (?, ?, ?)', 
                       (kisiisim, bulunankat, bulunansube))
        kisi_id = cursor.lastrowid
        conn.commit()
        conn.close()
        create_kisi_malzemeleri_table(kisiisim)
        print(f"'{kisiisim}' kişisi başarıyla eklendi. ID: {kisi_id}")
        return kisi_id
    except Exception as e:
        print(f"Kişi ekleme hatası: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return -1

def get_all_kisiler():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM kisiler ORDER BY kisiisim')
        kisiler = cursor.fetchall()
        conn.close()
        return [dict(row) for row in kisiler]
    except Exception as e:
        print(f"Kişileri getirme hatası: {e}")
        return []

def delete_kisi_by_id(kisi_id, kisiisim):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kisiler WHERE id = ?", (kisi_id,))
        table_name = f"{kisiisim}_malzemeleri".replace(' ', '').lower()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone():
            cursor.execute(f"DROP TABLE IF EXISTS \"{table_name}\"")
        conn.commit()
        conn.close()
        print(f"'{kisiisim}' kişisi ve malzemeler tablosu silindi.")
        return True
    except Exception as e:
        print(f"Kişi silme hatası: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

def create_sticker_id(stokkodu, numara):
    yil = datetime.datetime.now().year
    return f"{yil}_{stokkodu}_{numara:06d}"

def add_stokkodlu_malzeme_tip(stokkodu, isim, kategori, fotograf_yolu=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT stokkodu FROM malzemetypes WHERE stokkodu = ?', (stokkodu,))
        if cursor.fetchone():
            print(f"Hata: '{stokkodu}' stok kodlu malzeme zaten var! Farklı bir stok kodu kullanın.")
            conn.close()
            return False
        fotograf_blob = None
        if fotograf_yolu and os.path.exists(fotograf_yolu):
            with open(fotograf_yolu, 'rb') as f:
                fotograf_blob = f.read()
        cursor.execute('INSERT INTO malzemetypes (stokkodu, isim, kategori, fotograf) VALUES (?, ?, ?, ?)',
                       (stokkodu, isim, kategori, fotograf_blob))
        conn.commit()
        conn.close()
        conn = None
        if not create_stokkodu_table(stokkodu):
            print(f"Uyarı: Malzeme eklendi ancak stok kodu tablosu oluşturulamadı!")
        print(f"Malzeme tipi '{isim}' başarıyla eklendi.")
        return True
    except sqlite3.IntegrityError:
        print(f"Hata: '{stokkodu}' stok kodlu malzeme zaten var!")
        if conn:
            conn.close()
        return False
    except Exception as e:
        print(f"Hata: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def add_sticker_stokkodlutablo(stokkodu, adet=1):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT isim, kategori FROM malzemetypes WHERE stokkodu = ?', (stokkodu,))
        malzeme = cursor.fetchone()
        if not malzeme:
            print(f"Hata: '{stokkodu}' stok kodlu malzeme bulunamadı!")
            conn.close()
            return []
        table_name = f"stok_{stokkodu.replace(' ', '').replace('-', '_')}"
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', (table_name,))
        if not cursor.fetchone():
            print(f"'{stokkodu}' için tablo bulunamadı, oluşturuyor")
            create_stokkodu_table(stokkodu)
            conn.close()
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        cursor.execute(f'SELECT id FROM {table_name} ORDER BY id DESC LIMIT 1')
        son_kayit = cursor.fetchone()
        son_id = son_kayit['id'] if son_kayit else 0
        eklenen_stickerlar = []
        for i in range(adet):
            yeni_id = son_id + i + 1
            stickerkod = create_sticker_id(stokkodu, yeni_id)
            cursor.execute(f'INSERT INTO {table_name} (stickerkod, isim, kategori) VALUES (?, ?, ?)',
                           (stickerkod, malzeme['isim'], malzeme['kategori']))
            eklenen_stickerlar.append(stickerkod)
        conn.commit()
        conn.close()
        conn = None
        print(f"{adet} adet sticker başarıyla eklendi.")
        return eklenen_stickerlar
    except Exception as e:
        print(f"Hata: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return []

def add_zimmetle_malzeme(kisiisim, stickerid, isim):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM kisiler WHERE kisiisim = ?', (kisiisim,))
        if not cursor.fetchone():
            print(f"Hata: '{kisiisim}' isimli kişi bulunamadı!")
            conn.close()
            return False
        table_name = f"{kisiisim}_malzemeleri".replace(' ', '').lower()
        cursor.execute(f'INSERT INTO "{table_name}" (stickerid, isim) VALUES (?, ?)', (stickerid, isim))
        conn.commit()
        conn.close()
        print(f"'{stickerid}' kodlu malzeme '{kisiisim}' kişisine zimmetlendi.")
        return True
    except Exception as e:
        print(f"Zimmetleme hatası: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

def delete_last_sticker_stokkodlutablo(stokkodu):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        table_name = f"stok_{stokkodu.replace(' ', '').replace('-', '_')}"
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', (table_name,))
        if not cursor.fetchone():
            print(f"Hata: '{stokkodu}' stok kodlu malzeme için tablo bulunamadı!")
            conn.close()
            return None
        cursor.execute(f'SELECT id, stickerkod FROM {table_name} ORDER BY id DESC LIMIT 1')
        son_kayit = cursor.fetchone()
        if not son_kayit:
            print(f"Hata: '{stokkodu}' stok kodlu malzeme için silinecek sticker bulunamadı!")
            conn.close()
            return None
        cursor.execute(f'DELETE FROM {table_name} WHERE id = ?', (son_kayit['id'],))
        conn.commit()
        conn.close()
        conn = None
        print(f"Son sticker başarıyla silindi: {son_kayit['stickerkod']}")
        return son_kayit['stickerkod']
    except Exception as e:
        print(f"Son sticker silme hatası: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None

def delete_malzeme_type_complete(stokkodu):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT stokkodu FROM malzemetypes WHERE stokkodu = ?', (stokkodu,))
        if not cursor.fetchone():
            print(f"Hata: '{stokkodu}' stok kodlu malzeme bulunamadı!")
            conn.close()
            return False
        table_name = f"stok_{stokkodu.replace(' ', '').replace('-', '_')}"
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', (table_name,))
        if cursor.fetchone():
            cursor.execute(f'DROP TABLE {table_name}')
            print(f"Stok tablosu silindi: {table_name}")
        cursor.execute('DELETE FROM malzemetypes WHERE stokkodu = ?', (stokkodu,))
        conn.commit()
        conn.close()
        conn = None
        print(f"Malzeme tipi başarıyla silindi: {stokkodu}")
        return True
    except Exception as e:
        print(f"Malzeme tipi silme hatası: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def delete_last_zimmet(kisiisim):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        table_name = f"{kisiisim}_malzemeleri".replace(' ', '').lower() 
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', (table_name,))
        if not cursor.fetchone():
            print(f"Hata: '{kisiisim}' kişisine ait malzeme tablosu bulunamadı!")
            conn.close()
            return None
        cursor.execute(f'SELECT id, stickerid FROM "{table_name}" ORDER BY id DESC LIMIT 1')
        son_kayit = cursor.fetchone()
        if not son_kayit:
            print(f"Hata: '{kisiisim}' kişisine ait silinecek zimmet bulunamadı!")
            conn.close()
            return None
        sticker_id = son_kayit['stickerid']
        cursor.execute(f'DELETE FROM "{table_name}" WHERE id = ?', (son_kayit['id'],))
        conn.commit()
        conn.close()
        print(f"Son zimmetlenen malzeme başarıyla silindi: {sticker_id}")
        return sticker_id
    except Exception as e:
        print(f"Son zimmet silme hatası: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return None

def update_malzeme_type(eski_stokkodu, yeni_stokkodu=None, isim=None, kategori=None, fotograf_yolu=None):
    conn = None
    try:
        update_fields = []
        params = []
        if yeni_stokkodu is not None:
            update_fields.append("stokkodu = ?")
            params.append(yeni_stokkodu)
        if isim is not None:
            update_fields.append("isim = ?")
            params.append(isim)
        if kategori is not None:
            update_fields.append("kategori = ?")
            params.append(kategori)
        if fotograf_yolu is not None: 
            if fotograf_yolu == "":
                update_fields.append("fotograf = ?")
                params.append(None)
                print(f"Malzeme '{eski_stokkodu}' fotoğrafı silindi.")
            elif os.path.exists(fotograf_yolu):
                with open(fotograf_yolu, 'rb') as f:
                    fotograf_blob = f.read()
                update_fields.append("fotograf = ?")
                params.append(fotograf_blob)
                print(f"Yeni fotoğraf yüklendi: {fotograf_yolu}")
            else:
                print(f"Uyarı: Fotoğraf dosyası bulunamadı: {fotograf_yolu}")
        if not update_fields:
            print("Hata: Güncellenecek alan belirtilmedi!")
            return False
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = f"UPDATE malzemetypes SET {', '.join(update_fields)} WHERE stokkodu = ?"
        params.append(eski_stokkodu)
        cursor.execute(query, params)
        if cursor.rowcount == 0:
            print(f"Hata: '{eski_stokkodu}' stok kodlu malzeme bulunamadı!")
            conn.close()
            return False
        if yeni_stokkodu is not None and yeni_stokkodu != eski_stokkodu:
            eski_table_name = f"stok_{eski_stokkodu.replace(' ', '').replace('-', '_')}"
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (eski_table_name,))
            if cursor.fetchone():
                cursor.execute(f"DROP TABLE {eski_table_name}")
                print(f"Eski stok tablosu silindi: {eski_table_name}")
            create_stokkodu_table(yeni_stokkodu) 
        kullanilacak_stokkodu = yeni_stokkodu if (yeni_stokkodu and yeni_stokkodu != eski_stokkodu) else eski_stokkodu
        if isim is not None or kategori is not None:
            table_name = f"stok_{kullanilacak_stokkodu.replace(' ', '').replace('-', '_')}"
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if cursor.fetchone():
                update_sticker_fields = []
                sticker_params = []
                if isim is not None:
                    update_sticker_fields.append("isim = ?")
                    sticker_params.append(isim)
                if kategori is not None:
                    update_sticker_fields.append("kategori = ?")
                    sticker_params.append(kategori)
                if update_sticker_fields:
                     sticker_query = f"UPDATE {table_name} SET {', '.join(update_sticker_fields)}"
                     cursor.execute(sticker_query, sticker_params)
                     print(f"İlgili stok tablosu ({table_name}) güncellendi.")
        conn.commit()
        conn.close()
        print(f"Malzeme '{eski_stokkodu}' başarıyla güncellendi.")
        return True
    except Exception as e:
        print(f"Malzeme güncelleme hatası: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def update_kisi(kisi_id, yeni_kisiisim=None, yeni_bulunankat=None, yeni_bulunansube=None):
    conn = None
    try:
        update_fields = []
        params = []
        if yeni_kisiisim is not None:
            conn_temp = sqlite3.connect(DB_PATH)
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute('SELECT id FROM kisiler WHERE kisiisim = ? AND id != ?', (yeni_kisiisim, kisi_id))
            if cursor_temp.fetchone():
                print(f"Hata: '{yeni_kisiisim}' isimli başka bir kişi zaten var!")
                conn_temp.close()
                return False
            conn_temp.close()
            update_fields.append("kisiisim = ?")
            params.append(yeni_kisiisim)
        if yeni_bulunankat is not None:
            update_fields.append("bulunankat = ?")
            params.append(yeni_bulunankat)
        if yeni_bulunansube is not None:
            update_fields.append("bulunansube = ?")
            params.append(yeni_bulunansube)
        if not update_fields:
            print("Hata: Güncellenecek alan belirtilmedi!")
            return False
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT kisiisim FROM kisiler WHERE id = ?", (kisi_id,))
        eski_kayit = cursor.fetchone()
        if not eski_kayit:
             print(f"Hata: ID'si {kisi_id} olan kişi bulunamadı!")
             conn.close()
             return False
        eski_kisiisim = eski_kayit[0]
        query = f"UPDATE kisiler SET {', '.join(update_fields)} WHERE id = ?"
        params.append(kisi_id)
        cursor.execute(query, params)
        if yeni_kisiisim is not None and yeni_kisiisim != eski_kisiisim:
            eski_table_name = f"{eski_kisiisim}_malzemeleri".replace(' ', '').lower()
            yeni_table_name = f"{yeni_kisiisim}_malzemeleri".replace(' ', '').lower()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (eski_table_name,))
            if cursor.fetchone():
                try:
                    cursor.execute(f'ALTER TABLE "{eski_table_name}" RENAME TO "{yeni_table_name}"')
                    print(f"Kişi malzemeleri tablosu adı değiştirildi: '{eski_table_name}' -> '{yeni_table_name}'")
                except sqlite3.Error as e:
                    print(f"Kişi malzemeleri tablosu adı değiştirilirken hata: {e}")
                    conn.rollback()
                    conn.close()
                    return False
            else:
                 print(f"Uyarı: '{eski_kisiisim}' için malzeme tablosu bulunamadı, adı değiştirilemedi.")
        conn.commit()
        conn.close()
        print(f"Kişi (ID: {kisi_id}) başarıyla güncellendi.")
        return True
    except Exception as e:
        print(f"Kişi güncelleme hatası: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def get_stickers(stokkodu):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        table_name = f"stok_{stokkodu.replace(' ', '').replace('-', '_')}"
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"Hata: '{stokkodu}' stok kodlu malzeme için tablo bulunamadı!")
            conn.close()
            return []
        cursor.execute(f'SELECT id, stickerkod, isim, kategori, olusturma_tarihi FROM {table_name} ORDER BY olusturma_tarihi DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Sticker listesi getirme hatası: {e}")
        return []

def update_varolana_yenizimmet(stickerid, kisiisimyeni):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        tum_kisiler = get_all_kisiler() 
        eski_sahip_isim = None
        eski_sahip_tablo = None
        stok_tablo_adi = None
        malzeme_ismi = None

        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "stok_%"')
        stok_tablolari = cursor.fetchall()
        for stok_tablo in stok_tablolari:
            tablo_adi = stok_tablo[0]
            cursor.execute(f'SELECT isim FROM "{tablo_adi}" WHERE stickerkod = ?', (stickerid,))
            sonuc = cursor.fetchone()
            if sonuc:
                stok_tablo_adi = tablo_adi
                malzeme_ismi = sonuc['isim']
                break
        
        if not stok_tablo_adi:
            print(f"Hata: '{stickerid}' sticker ID'si hiçbir stok tablosunda bulunamadı!")
            conn.close()
            return False

        for kisi in tum_kisiler:
            kisi_tablo_adi = f"{kisi['kisiisim']}_malzemeleri".replace(' ', '').lower()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (kisi_tablo_adi,))
            if cursor.fetchone():
                 cursor.execute(f'SELECT stickerid FROM "{kisi_tablo_adi}" WHERE stickerid = ?', (stickerid,))
                 sonuc = cursor.fetchone()
                 if sonuc:
                     eski_sahip_isim = kisi['kisiisim']
                     eski_sahip_tablo = kisi_tablo_adi
                     break 

        if eski_sahip_isim:
            cursor.execute(f'DELETE FROM "{eski_sahip_tablo}" WHERE stickerid = ?', (stickerid,))
            print(f"'{stickerid}' sticker ID'si '{eski_sahip_isim}' kişisinden silindi.")
        else:
            print(f"Bilgi: '{stickerid}' sticker ID'si hiçbir kişide bulunamadı, doğrudan zimmetleniyor.")

        yeni_kisi_tablo = f"{kisiisimyeni}_malzemeleri".replace(' ', '').lower()
        cursor.execute(f'INSERT INTO "{yeni_kisi_tablo}" (stickerid, isim) VALUES (?, ?)', (stickerid, malzeme_ismi))
        
        conn.commit()
        conn.close()
        
        if eski_sahip_isim:
            print(f"'{stickerid}' sticker ID'si '{eski_sahip_isim}' kişisinden '{kisiisimyeni}' kişisine transfer edildi.")
        else:
            print(f"'{stickerid}' sticker ID'si '{kisiisimyeni}' kişisine zimmetlendi.")
            
        return True 
    except Exception as e:
        print(f"Sticker transfer hatası: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def save_image_to_file(malzeme_data, output_path):
    try:
        if malzeme_data and 'fotograf' in malzeme_data and malzeme_data['fotograf']:
            with open(output_path, 'wb') as f:
                f.write(malzeme_data['fotograf'])
            print(f"Fotoğraf '{output_path}' dosyasına kaydedildi.")
            return True
        else:
            print("Hata: Fotoğraf verisi bulunamadı!")
            return False
    except Exception as e:
        print(f"Fotoğraf kaydetme hatası: {e}")
        return False

def search_malzeme_types(arama_metni):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        arama_metni_kucuk = arama_metni.lower()
        cursor.execute('''
            SELECT stokkodu, isim, kategori, fotograf,
                   CASE WHEN fotograf IS NULL THEN 0 ELSE 1 END as fotograf_var
            FROM malzemetypes
            WHERE LOWER(stokkodu) LIKE ? OR LOWER(isim) LIKE ? OR LOWER(kategori) LIKE ?
            ORDER BY isim
        ''', (f'%{arama_metni_kucuk}%', f'%{arama_metni_kucuk}%', f'%{arama_metni_kucuk}%'))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Malzeme tipi arama hatası: {e}")
        return []

def add_kategori(kategori_adi):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM kategoriler WHERE kategori_adi = ?', (kategori_adi,))
        if cursor.fetchone():
            print(f"'{kategori_adi}' kategorisi zaten mevcut!")
            conn.close()
            return False
        cursor.execute('INSERT INTO kategoriler (kategori_adi) VALUES (?)', (kategori_adi,))
        conn.commit()
        conn.close()
        print(f"'{kategori_adi}' kategorisi başarıyla eklendi.")
        return True
    except Exception as e:
        print(f"Kategori ekleme hatası: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

def get_all_kategoriler():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT kategori_adi FROM kategoriler ORDER BY kategori_adi')
        rows = cursor.fetchall()
        conn.close()
        return [row['kategori_adi'] for row in rows]
    except Exception as e:
        print(f"Kategori listesi getirme hatası: {e}")
        return []

def get_all_malzeme_types():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute('''
            SELECT stokkodu, isim, kategori,
                   CASE WHEN fotograf IS NULL THEN 0 ELSE 1 END as fotograf_var
            FROM malzemetypes
            ORDER BY isim
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Malzeme tipleri getirme hatası: {e}")
        return []

def get_kisi(kisiisim):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute('SELECT id, kisiisim, bulunankat, bulunansube FROM kisiler WHERE kisiisim = ?', (kisiisim,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        else:
            return None
    except Exception as e:
        print(f"Kişi bilgisi getirme hatası: {e}")
        return None

def get_zimmetli_malzemeler(kisiisim):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        table_name = f"{kisiisim}_malzemeleri".replace(' ', '').lower()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"Hata: '{kisiisim}' kişisine ait malzeme tablosu bulunamadı!")
            conn.close()
            return []
        cursor.execute(f'SELECT id, stickerid, isim, olusturmatarihi FROM "{table_name}" ORDER BY olusturmatarihi DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Zimmetli malzeme listesi getirme hatası: {e}")
        return []

if __name__ == "__main__":
    create_database()