import sys
from PyQt5.QtWidgets import QApplication
from erpmain import ErpMain
from database import create_database

def main():
    create_database()
    app = QApplication(sys.argv)
    main_window = ErpMain()
    main_window.showMaximized()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()