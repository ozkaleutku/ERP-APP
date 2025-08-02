import sys
import os  
from shutil import copy2
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QStringListModel
from database import add_stokkodlu_malzeme_tip, update_malzeme_type, get_all_malzeme_types, get_all_kategoriler, add_kategori
from ekle_duzenle_UI import Ui_kategori_combobox

class EkleDuzenleWindow(QMainWindow):
    def __init__(self, main_window, product=None):
        super().__init__()
        self.ui = Ui_kategori_combobox()
        self.ui.setupUi(self)
        self.main_window = main_window
        self.product = product
        self.secilen_resim_yolu = None
        
        self.load_categories()
        
        if product:
            self.ui.stokkoduekle_text.setText(product['stokkodu'])
            self.ui.stokkoduekle_text.setReadOnly(True)
            self.ui.isimtext.setText(product['isim'])
            self.ui.kategori_combobox_2.setCurrentText(product['kategori'])
            if product.get('fotograf_var', 0) == 1:
                import sqlite3
                conn = sqlite3.connect('erp_database.db')
                cursor = conn.cursor()
                cursor.execute('SELECT fotograf FROM malzemetypes WHERE stokkodu = ?', (product['stokkodu'],))
                fotograf_data = cursor.fetchone()
                if fotograf_data:
                    fotograf_data = fotograf_data[0]
                    temp_path = os.path.join(os.getcwd(), "temp_edit.jpg")
                    with open(temp_path, 'wb') as f:
                        f.write(fotograf_data)
                    pixmap = QPixmap(temp_path)
                    self.ui.resim_label.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
                conn.close()
        
        self.ui.geributton.clicked.connect(self.go_back)
        self.ui.yenilebutton.clicked.connect(self.refresh_ui)
        self.ui.kaydetbutton.clicked.connect(self.save_product)
        self.ui.resimsecbutton.clicked.connect(self.select_image)
        self.ui.farkli_kategori_button.clicked.connect(self.add_category)

    def load_categories(self):
        kategoriler = get_all_kategoriler()
        
        items = get_all_malzeme_types()
        malzeme_kategorileri = list(set(item['kategori'] for item in items if item['kategori']))
        
        tum_kategoriler = list(set(kategoriler + malzeme_kategorileri))
        tum_kategoriler.sort()
        
        self.ui.kategori_combobox_2.clear()
        self.ui.kategori_combobox_2.addItems(tum_kategoriler)

    def add_category(self):
        yeni_kategori = self.ui.farkli_kategori_text.text().strip()
        if not yeni_kategori:
            return
            
        mevcut_kategoriler = [self.ui.kategori_combobox_2.itemText(i) for i in range(self.ui.kategori_combobox_2.count())]
        if yeni_kategori in mevcut_kategoriler:
            QMessageBox.information(self, "Bilgi", f"'{yeni_kategori}' kategorisi zaten mevcut!")
            return
            
        if add_kategori(yeni_kategori):
            self.ui.kategori_combobox_2.addItem(yeni_kategori)
            self.ui.kategori_combobox_2.setCurrentText(yeni_kategori)
            self.ui.farkli_kategori_text.clear()
        else:
            QMessageBox.warning(self, "Hata", f"'{yeni_kategori}' kategorisi eklenirken bir hata oluştu!")

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Resim Seç", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        
        if not file_path:
            return
        
        hedef_klasor = "images"
        if not os.path.exists(hedef_klasor):
            os.makedirs(hedef_klasor)
        dosya_adi = os.path.basename(file_path)
        hedef_yol = os.path.join(hedef_klasor, dosya_adi)
        sayac = 1
        ad, uzanti = os.path.splitext(dosya_adi)
        while os.path.exists(hedef_yol):
            yeni_dosya_adi = f"{ad}_{sayac}{uzanti}"
            hedef_yol = os.path.join(hedef_klasor, yeni_dosya_adi)
            sayac += 1
        
        try:
            copy2(file_path, hedef_yol)
            print(f"Resim başarıyla kopyalandı: {hedef_yol}")
        except Exception as e:
            print(f"Resim kopyalama hatası: {e}")
            return
        
        self.ui.resim_label.setPixmap(QPixmap(hedef_yol).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        self.secilen_resim_yolu = hedef_yol

    def save_product(self):
        stokkodu = self.ui.stokkoduekle_text.text().strip()
        isim = self.ui.isimtext.text().strip()
        kategori = self.ui.kategori_combobox_2.currentText()
        resim_yolu = self.secilen_resim_yolu
        
        if not stokkodu or not isim:
            QMessageBox.warning(self, "Hata", "Stok kodu ve isim alanları boş bırakılamaz!")
            return

        success = False
        if self.product:
            success = update_malzeme_type(
                eski_stokkodu=self.product['stokkodu'],
                isim=isim,
                kategori=kategori,
                fotograf_yolu=resim_yolu
            )
            kayit_mesaji = f"Güncellendi: {stokkodu} - {isim}"
        else:
            success = add_stokkodlu_malzeme_tip(stokkodu, isim, kategori, resim_yolu)
            if not success:
                QMessageBox.warning(self, "Hata", f"'{stokkodu}' stok kodlu malzeme zaten var! Farklı bir stok kodu kullanın.")
                return
            kayit_mesaji = f"Eklendi: {stokkodu} - {isim}"

        if success:
            model = self.ui.kaydetme_listbox.model()
            
            if not isinstance(model, QStringListModel):
                model = QStringListModel()
                self.ui.kaydetme_listbox.setModel(model)
            
            current_list = model.stringList()
            current_list.insert(0, kayit_mesaji) 
            model.setStringList(current_list)
            
            self.refresh_ui()
            
        self.main_window.refresh_ui()

    def go_back(self):
        self.main_window.show()
        self.close()

    def refresh_ui(self):
        self.ui.stokkoduekle_text.clear()
        self.ui.isimtext.clear()
        self.ui.kategori_combobox_2.clear()
        self.ui.farkli_kategori_text.clear()
        self.ui.resim_label.clear()
        self.load_categories()
        self.secilen_resim_yolu = None
        
        temp_path = os.path.join(os.getcwd(), "temp_edit.jpg")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        if self.product:
            self.ui.stokkoduekle_text.setReadOnly(False)
            self.product = None