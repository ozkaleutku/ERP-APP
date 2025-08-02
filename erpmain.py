import sys
import os
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem
from database import get_all_malzeme_types, search_malzeme_types, delete_malzeme_type_complete
from erpmain_UI import Ui_MainWindow
from ekle_duzenle import EkleDuzenleWindow
from zimmetle import ZimmetleWindow
from io import BytesIO
from PIL import Image

UserRole = 256

class ErpMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.selected_product = None
    
        self.table_model = QStandardItemModel(0, 3)
        self.table_model.setHorizontalHeaderLabels(["Stok Kodu", "Kategori", "İsim"])
        self.ui.malzemelist.setModel(self.table_model)
        
        self.ui.malzemelist.setColumnWidth(0, 150) 
        self.ui.malzemelist.setColumnWidth(1, 150)
        self.ui.malzemelist.setColumnWidth(2, 250) 
        
        self.load_malzeme_types()
        self.ui.arabutton.clicked.connect(self.search_products)
        self.ui.eklebutton.clicked.connect(self.open_ekle_duzenle)
        self.ui.duzenlebutton.clicked.connect(self.open_ekle_duzenle)
        self.ui.silbutton.clicked.connect(self.delete_product)
        self.ui.stickerolustur_button.clicked.connect(self.open_zimmetle)
        self.ui.malzemelist.clicked.connect(self.on_list_click)
        self.ui.yenilebutton.clicked.connect(self.refresh_ui)
        
        self.ui.searchbox.returnPressed.connect(self.search_products)


    def load_malzeme_types(self):
        items = get_all_malzeme_types()
        self.table_model.setRowCount(0)
        
        for row, item in enumerate(items):
            stok_kodu = QStandardItem(item['stokkodu'])
            isim = QStandardItem(item['isim'])
            kategori = QStandardItem(item['kategori'] if 'kategori' in item else "")
            
            self.table_model.setItem(row, 0, stok_kodu)
            self.table_model.setItem(row, 1, kategori)
            self.table_model.setItem(row, 2, isim)
            
            stok_kodu.setData(item, UserRole) 


    def search_products(self):
        text = self.ui.searchbox.text().strip()
        if not text:
            self.load_malzeme_types()
            return
            
        results = search_malzeme_types(text)
        
        if results:
            self.table_model.setRowCount(0)
    
            for row, item in enumerate(results):
                stok_kodu = QStandardItem(item['stokkodu'])
                isim = QStandardItem(item['isim'])
                kategori = QStandardItem(item['kategori'] if item['kategori'] else "")
                
                self.table_model.setItem(row, 0, stok_kodu)
                self.table_model.setItem(row, 1, kategori)
                self.table_model.setItem(row, 2, isim)
                
                
                stok_kodu.setData(item, UserRole)
            
            if self.table_model.rowCount() > 0:
                index = self.table_model.index(0, 0)
                self.ui.malzemelist.setCurrentIndex(index)
                self.on_list_click(index)
            
            print(f"Arama sonucu: {len(results)} ürün bulundu.")
        else:
            self.table_model.setRowCount(0)
            self.ui.chosenmalzeme_label.setText("Sonuç bulunamadı")
            self.ui.urunfotograf_display.setScene(QGraphicsScene())
            print(f"Arama sonucu: '{text}' için ürün bulunamadı.")
            
    def on_list_click(self, index):
        if index.isValid():
            item = self.table_model.itemFromIndex(index.siblingAtColumn(0))
            
            if item:
                self.selected_product = item.data(UserRole)
                if self.selected_product:
                    self.ui.chosenmalzeme_label.setText(self.selected_product['isim'])
                    
                    if self.selected_product.get('fotograf_var', 0) == 1:
                        conn = sqlite3.connect('erp_database.db')
                        cursor = conn.cursor()
                        cursor.execute('SELECT fotograf FROM malzemetypes WHERE stokkodu = ?', (self.selected_product['stokkodu'],))
                        fotograf_data = cursor.fetchone()
                        if fotograf_data:
                            fotograf_data = fotograf_data[0]
                            temp_path = os.path.join(os.getcwd(), "temp_product.jpg")
                            with open(temp_path, 'wb') as f:
                                f.write(fotograf_data)
                            pixmap = QPixmap(temp_path)
                        else:
                            pixmap = QPixmap()
                        conn.close()
                    else:
                        pixmap = QPixmap()
                        
                    
                    scene = QGraphicsScene()
                    scene.addPixmap(pixmap.scaled(1000, 1000, Qt.AspectRatioMode.KeepAspectRatio))
                    self.ui.urunfotograf_display.setScene(scene)

    def select_product(self):
        if self.selected_product:
            self.ui.chosenmalzeme_label.setText(self.selected_product['isim'])

    def open_ekle_duzenle(self):
        self.edit_window = EkleDuzenleWindow(self, self.selected_product)
        self.edit_window.show()
        self.hide()

    def open_zimmetle(self):
        if not self.selected_product:
            return
        self.zimmet_window = ZimmetleWindow(self, self.selected_product)
        self.zimmet_window.show()
        self.hide()

    def delete_product(self):
        if not self.selected_product:
            return
        result = delete_malzeme_type_complete(self.selected_product['stokkodu'])
        if result:
            self.refresh_ui()

    def refresh_ui(self):
        self.ui.searchbox.clear()
        self.ui.chosenmalzeme_label.setText("")
        
        
        self.ui.urunfotograf_display.setScene(QGraphicsScene())
        
        self.selected_product = None
        self.load_malzeme_types()
        
        temp_path = os.path.join(os.getcwd(), "temp_product.jpg")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ErpMain()
    window.showMaximized()
    sys.exit(app.exec_())