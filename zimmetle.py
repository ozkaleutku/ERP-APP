import os
import sys
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene,  QGraphicsTextItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
from database import get_all_kisiler, add_sticker_stokkodlutablo, add_zimmetle_malzeme, get_kisi, get_stickers, delete_last_sticker_stokkodlutablo, update_kisi, delete_kisi_by_id, delete_last_zimmet
from zimmetle_UI import Ui_MainWindow
from zimmetleyeni import ZimmetleYeniWindow
from database import add_kisi

class ZimmetleWindow(QMainWindow):
    def __init__(self, main_window, product):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.main_window = main_window
        self.product = product
        self.current_sticker_id = None
        self.selected_kisi_index = -1
        self.kisiler = []
        
        if product:
            self.ui.secilmismalzeme_bilgiler.setText(f"Stok Kodu: {product['stokkodu']}\nİsim: {product['isim']}")
        
        self.load_kisiler()
        
        for i in range(1, 11):
            self.ui.bulundugukat_combobox.addItem(str(i))
        
        self.ui.bulundugusube_combobox.addItem("ankara merkez")
        self.ui.bulundugusube_combobox.addItem("ankara ek")
        self.ui.bulundugusube_combobox.addItem("istanbul")
        
        self.ui.sahisekle_button.clicked.connect(self.add_or_update_person)
        self.ui.sahissil_button.clicked.connect(self.delete_person)
        self.ui.zimmetlebutton.clicked.connect(self.zimmetle)
        self.ui.zimmetlesil_button.clicked.connect(self.delete_last_zimmet_clicked)
        self.ui.zimmetduzenle_button.clicked.connect(self.open_zimmetleyeni)
        self.ui.geri_button.clicked.connect(self.go_back)

        
        self.ui.kisi_combobox.currentIndexChanged.connect(self.on_kisi_selected)

    def load_kisiler(self):
        self.ui.kisi_combobox.clear()
        self.kisiler = get_all_kisiler()
        for kisi in self.kisiler:
            display_name = kisi['kisiisim']
            self.ui.kisi_combobox.addItem(display_name)
            self.ui.kisi_combobox.setItemData(self.ui.kisi_combobox.count()-1, kisi['id'])

    def on_kisi_selected(self, index):
        if index < 0 or not self.kisiler or index >= len(self.kisiler):
            return
            
        self.selected_kisi_index = index
        selected_kisi = self.kisiler[index]
        self.ui.sahisisim_text.setText(selected_kisi['kisiisim'])
        
        kat_index = int(selected_kisi['bulunankat']) - 1 if selected_kisi['bulunankat'] is not None else 0
        if 0 <= kat_index < self.ui.bulundugukat_combobox.count():
            self.ui.bulundugukat_combobox.setCurrentIndex(kat_index)
            
        sube_list = ["ankara merkez", "ankara ek", "istanbul"]
        sube_index = sube_list.index(selected_kisi['bulunansube']) if selected_kisi['bulunansube'] in sube_list else 0
        self.ui.bulundugusube_combobox.setCurrentIndex(sube_index)
    
    def add_or_update_person(self):
        yeni_isim = self.ui.sahisisim_text.text().strip()
        yeni_kat = self.ui.bulundugukat_combobox.currentText()
        yeni_sube = self.ui.bulundugusube_combobox.currentText()

        if not yeni_isim:
            return

        if (self.selected_kisi_index >= 0 and 
            self.selected_kisi_index < len(self.kisiler)):
            
            selected_kisi = self.kisiler[self.selected_kisi_index]
            
            result = update_kisi(selected_kisi['id'], yeni_isim, int(yeni_kat), yeni_sube)
            if result:
                print(f"Kişi bilgileri güncellendi: {yeni_isim}")
            else:
                print(f"Kişi bilgileri güncellenemedi: {yeni_isim}")
        else:
            kisi_id = add_kisi(yeni_isim, int(yeni_kat), yeni_sube)
            if kisi_id != -1:
                print(f"Yeni kişi eklendi: {yeni_isim}")
            else:
                print(f"Kişi eklenemedi: {yeni_isim}")
        
        self.load_kisiler()
        self.ui.sahisisim_text.clear()
        self.selected_kisi_index = -1
        
    def delete_person(self):
        if (self.selected_kisi_index < 0 or 
            not self.kisiler or 
            self.selected_kisi_index >= len(self.kisiler)):
            return
            
        selected_kisi = self.kisiler[self.selected_kisi_index]

        print(f"Kişi siliniyor: ID={selected_kisi['id']}, İsim={selected_kisi['kisiisim']}")
        result = delete_kisi_by_id(selected_kisi['id'], selected_kisi['kisiisim'])
        
        if result:
            print(f"Kişi başarıyla silindi: {selected_kisi['kisiisim']}")
            self.load_kisiler()
            self.ui.sahisisim_text.clear()
            self.selected_kisi_index = -1
        else:
            print(f"Kişi silme işlemi başarısız: {selected_kisi['kisiisim']}")
            
        self.refresh_ui()

    def zimmetle(self):
        selected_index = self.ui.kisi_combobox.currentIndex()
        if selected_index < 0:
            return
            


        selected_kisi_id = self.ui.kisi_combobox.itemData(selected_index)
        selected_kisi_name = self.ui.kisi_combobox.currentText()
        selected_kisi = None
        
        for kisi in self.kisiler:
            if kisi['id'] == selected_kisi_id:
                selected_kisi = kisi
                break
                
        if not selected_kisi:
            return
            
        stickers = add_sticker_stokkodlutablo(self.product['stokkodu'], 1)
        if not stickers:
            return
            
        sticker_id = stickers[0]
        result = add_zimmetle_malzeme(selected_kisi['kisiisim'], sticker_id, self.product['isim'])
        
        if result:
            self.current_sticker_id = sticker_id
            
            scene = QGraphicsScene()
            text_item = QGraphicsTextItem(f"Sticker ID: {sticker_id}\nStok Kodu: {self.product['stokkodu']}\nKategori: {self.product.get('kategori', '')}\nÜrün: {self.product['isim']}\nKişi: {selected_kisi_name}")
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            text_item.setFont(font)
            scene.addItem(text_item)
            self.ui.stickerview.setScene(scene)
            
            print(f"Zimmetleme başarılı: {sticker_id} -> {selected_kisi_name}")
        else:
            print(f"Zimmetleme başarısız: {sticker_id} -> {selected_kisi_name}")

    def delete_last_zimmet_clicked(self):
        selected_index = self.ui.kisi_combobox.currentIndex()
        if selected_index < 0:
            return
            
        selected_kisi_id = self.ui.kisi_combobox.itemData(selected_index)
        selected_kisi_name = self.ui.kisi_combobox.currentText()
        selected_kisi = None
        
        for kisi in self.kisiler:
            if kisi['id'] == selected_kisi_id:
                selected_kisi = kisi
                break
                
        if not selected_kisi:
            return
            
        result = delete_last_zimmet(selected_kisi['kisiisim'])
        if result:

            sticker_id = delete_last_sticker_stokkodlutablo(self.product['stokkodu'])
            
            self.ui.stickerview.setScene(None)
            self.current_sticker_id = result
            scene = QGraphicsScene()
            text_item = QGraphicsTextItem(f"Sticker ID: {result}\nStok Kodu: {self.product['stokkodu']}\nKategori: {self.product.get('kategori', '')}\nÜrün: {self.product['isim']}\nKişi: {selected_kisi_name}\nDurumu: Zimmet silindi\nID tekrar kullanılabilir")
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            text_item.setFont(font)
            scene.addItem(text_item)
            self.ui.stickerview.setScene(scene)
            
            print(f"Son zimmet silindi: {result}, ID tekrar kullanılabilir")
        else:
            print(f"Son zimmet silme başarısız: {selected_kisi_name}")

    def open_zimmetleyeni(self):
        if not self.product:
            return
            
        sticker_id = self.current_sticker_id
        
        self.yeni_window = ZimmetleYeniWindow(self, sticker_id, self.product['isim'], self.product['stokkodu'])
        self.yeni_window.show()
        self.hide()

    def go_back(self):
        self.main_window.show()
        self.close()

    def refresh_ui(self):
        self.ui.sahisisim_text.clear()
        self.ui.bulundugukat_combobox.setCurrentIndex(0)
        self.ui.bulundugusube_combobox.setCurrentIndex(0)
        self.load_kisiler()
        self.ui.stickerview.setScene(QGraphicsScene())
        
        self.selected_kisi_index = -1