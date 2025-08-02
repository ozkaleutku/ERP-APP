import os
import sqlite3
import sys
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsTextItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
from database import get_all_kisiler, get_stickers, update_varolana_yenizimmet
from zimmetleyeni_UI import Ui_MainWindow

class ZimmetleYeniWindow(QMainWindow):
    def __init__(self, zimmetle_window, sticker_id=None, urun_isim=None, stokkodu=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.zimmetle_window = zimmetle_window
        self.sticker_id = sticker_id
        self.urun_isim = urun_isim
        self.stokkodu = stokkodu
        
        if urun_isim and stokkodu:
            self.ui.urunbilgilerduzenle.setText(f"Stok Kodu: {stokkodu}\nİsim: {urun_isim}")
        
        if sticker_id:
            self.ui.yenizimmetbilgi_text.setText(f"Sticker ID: {sticker_id}")
        
        self.load_kisiler()
        self.load_sticker_ids()
        
        self.ui.geributtonyenizimmet.clicked.connect(self.go_back)
        self.ui.yenileyenizimmetbutton.clicked.connect(self.refresh_ui)
        self.ui.zimmetlekaydetyeni_button.clicked.connect(self.transfer_zimmet)

    def load_kisiler(self):
        self.ui.yenizimmetle.clear()
        kisiler = get_all_kisiler()
        for kisi in kisiler:
            display_name = kisi['kisiisim']
            self.ui.yenizimmetle.addItem(display_name)
            self.ui.yenizimmetle.setItemData(self.ui.yenizimmetle.count()-1, kisi['id'])

    def load_sticker_ids(self):
        self.ui.stickerid_combobox.setEditable(True)
        if self.stokkodu:
            stickers = get_stickers(self.stokkodu)
            sticker_ids = [s['stickerkod'] for s in stickers]
            self.ui.stickerid_combobox.clear()
            self.ui.stickerid_combobox.addItems(sticker_ids)
            
            if self.sticker_id and self.sticker_id in sticker_ids:
                index = sticker_ids.index(self.sticker_id)
                self.ui.stickerid_combobox.setCurrentIndex(index)

    def transfer_zimmet(self):
        selected_index = self.ui.yenizimmetle.currentIndex()
        if selected_index < 0:
            return
            
        selected_kisi_id = self.ui.yenizimmetle.itemData(selected_index)
        selected_kisi_name = self.ui.yenizimmetle.currentText()
        kisiler = get_all_kisiler()
        selected_kisi = None
        for kisi in kisiler:
            if kisi['id'] == selected_kisi_id:
                selected_kisi = kisi
                break
                
        if not selected_kisi:
            return
            
        sticker_id = self.ui.stickerid_combobox.currentText()
        
        if not sticker_id:
            return
        
        
        conn = sqlite3.connect('erp_database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        tum_kisiler = get_all_kisiler()
        sticker_bulundu = False
        mevcut_kisi = None
        mevcut_kisi_display = None
        
        for kisi in tum_kisiler:
            kisi_tablo_adi = f"{kisi['kisiisim']}_malzemeleri".replace(' ', '').lower()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (kisi_tablo_adi,))
            if cursor.fetchone():
                cursor.execute(f'SELECT stickerid FROM "{kisi_tablo_adi}" WHERE stickerid = ?', (sticker_id,))
                if cursor.fetchone():
                    sticker_bulundu = True
                    mevcut_kisi = kisi['kisiisim']
                    mevcut_kisi_display = kisi['kisiisim']
                    break
        
        conn.close()
        if sticker_bulundu and mevcut_kisi:
            result = update_varolana_yenizimmet(sticker_id, selected_kisi['kisiisim'])
            if result:
                self.ui.yenizimmetbilgi_text.setText(f"Transfer: {sticker_id}\n{mevcut_kisi_display} -> {selected_kisi_name}")
                print(f"Sticker {sticker_id} {mevcut_kisi}'den {selected_kisi['kisiisim']}'e transfer edildi.")
        else:
            result = update_varolana_yenizimmet(sticker_id, selected_kisi['kisiisim'])
            if result:
                self.ui.yenizimmetbilgi_text.setText(f"Zimmetlendi: {sticker_id}\n-> {selected_kisi_name}")
                print(f"Boşta olan sticker {sticker_id} {selected_kisi['kisiisim']}'e zimmetlendi.")
        

    def go_back(self):
        self.zimmetle_window.show()
        self.close()

    def refresh_ui(self):
        self.ui.yenizimmetle.clear()
        self.ui.stickerid_combobox.clear()
        self.ui.yenizimmetbilgi_text.setText("")
        
        self.load_kisiler()
        self.load_sticker_ids()