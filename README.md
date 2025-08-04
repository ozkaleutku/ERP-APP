# ERP Stock Material Management and Assignment Tracking System

## 📋 Project Description

This project is a comprehensive desktop application that enables companies or organizations to track stock materials, assign them to employees, and manage these processes. Developed using PyQt5 and performs data management with SQLite database.

## ✨ Features

### 🏭 Material Management
- **Add/Edit Materials**: Define materials with stock code, name, category, and photo
- **Category Management**: Dynamic category addition and management
- **Search and Filtering**: Advanced search capabilities
- **Photo Support**: Ability to add visuals to materials

### 👥 Personnel Management  
- **Add/Edit Person**: Full name, floor location, and branch information
- **Automatic Table Creation**: Automatic assignment table for each personnel

### 🏷️ Sticker and Assignment System
- **Automatic Sticker Generation**: Unique identifiers in YEAR_StockCode_SerialNo format
- **Assignment Tracking**: Detailed tracking of which material is with whom
- **Transfer Operations**: Transfer materials between personnel
- **Rollback**: Undo last assignment operations

### 📊 Database Management
- **SQLite Integration**: Lightweight and reliable data storage
- **Automatic Table Creation**: Automatically creates required tables
- **BLOB Support**: Secure storage of photos in database

## 🛠️ Technologies

- **Python 3.x**
- **PyQt5** - GUI framework
- **SQLite3** - Database
- **Pillow (PIL)** - Image processing
- **datetime** - Date/time operations

## 🚀 Installation

### Requirements
```bash
# Python 3.7+ required
python --version
```

### Step 1: Download the Project
```bash
git clone <repo-url>
cd ERP-APP
```

### Step 2: Create Virtual Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac  
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Start the Application
```bash
python main.py
```

## 📖 User Guide

### First Launch
- When the application is run for the first time, `erp_database.db` file is automatically created
- All required tables are automatically set up

### Adding Materials
1. Click the **"ADD"** button from the main screen
2. Enter stock code (must be unique), name, and category information
3. Optionally add a photo
4. Click the **"SAVE"** button

### Adding Personnel
1. Enter personnel information from the assignment screen:
   - Full name
   - Floor location (1-10)
   - Location (Ankara Main, Ankara Ext, Istanbul)
2. Click the **"Add Person"** button

### Assignment Process
1. Select a material from the main screen
2. Click the **"Create sticker and assign"** button
3. Select personnel
4. Click the **"Create sticker and assign"** button
5. System automatically generates unique sticker code

### Transfer Process
1. Click the **"Edit Assigned"** button from the assignment screen
2. Select the sticker ID to be transferred
3. Select new personnel
4. Click the **"Assign"** button

## 🗄️ Database Structure

### Main Tables

#### `malzemetypes`
- `stokkodu` (TEXT, PRIMARY KEY): Unique stock code
- `isim` (TEXT): Material name
- `kategori` (TEXT): Material category  
- `fotograf` (BLOB): Material photo

#### `kisiler`
- `id` (INTEGER, PRIMARY KEY): Unique person ID
- `kisiisim` (TEXT): Person's full name
- `bulunankat` (INTEGER): Floor location (1-10)
- `bulunansube` (TEXT): Branch location

#### `kategoriler`
- `id` (INTEGER, PRIMARY KEY): Category ID
- `kategori_adi` (TEXT, UNIQUE): Category name

### Dynamic Tables

#### `stok_{stokkodu}` Tables
Automatically created for each stock code:
- `id` (INTEGER, PRIMARY KEY): Serial number
- `stickerkod` (TEXT, UNIQUE): Unique sticker code
- `isim` (TEXT): Material name
- `kategori` (TEXT): Material category
- `olusturma_tarihi` (TIMESTAMP): Creation date

#### `{kisiisim}_malzemeleri` Tables  
Automatically created for each personnel:
- `id` (INTEGER, PRIMARY KEY): Serial number
- `stickerid` (TEXT, UNIQUE): Assigned sticker code
- `isim` (TEXT): Material name
- `olusturmatarihi` (TIMESTAMP): Assignment date

## 🔧 Important Functions

### Database Operations (`database.py`)
- `create_database()`: Creates database and main tables
- `add_stokkodlu_malzeme_tip()`: Adds new material type
- `add_sticker_stokkodlutablo()`: Creates sticker
- `add_zimmetle_malzeme()`: Performs assignment operation
- `update_varolana_yenizimmet()`: Performs transfer operation

### Sticker Code Format
- Format: `{YEAR}_{STOCKCODE}_{6_DIGIT_SERIAL_NO}`
- Example: `2025_LAPTOP001_000001`

## ⚙️ Configuration

### Database Path
```python
DB_PATH = 'erp_database.db'  # in database.py file
```

### Customizing Branch and Floor Options

#### 🏢 Changing Floor Options
**File:** `zimmetle.py` - `__init__` method (line ~25)
```python
# Default: Floors 1-10
for i in range(1, 11):
    self.ui.bulundugukat_combobox.addItem(str(i))

# Customization example: Floors 1-15
for i in range(1, 16):
    self.ui.bulundugukat_combobox.addItem(str(i))

# Or custom floor names
floors = ["Basement", "Ground", "1st Floor", "2nd Floor", "Roof"]
for floor in floors:
    self.ui.bulundugukat_combobox.addItem(floor)
```

#### 🏪 Changing Branch Options
**Changes needed in two places:**

1. **File:** `zimmetle.py` - `__init__` method (lines ~28-30)
```python
# Default branches
self.ui.bulundugusube_combobox.addItem("ankara merkez")
self.ui.bulundugusube_combobox.addItem("ankara ek")
self.ui.bulundugusube_combobox.addItem("istanbul")

# Adding new branches
self.ui.bulundugusube_combobox.addItem("izmir")
self.ui.bulundugusube_combobox.addItem("bursa")
```

2. **File:** `zimmetle.py` - `on_kisi_selected` method (line ~52)
```python
# Update branch list (must match the above)
branch_list = ["ankara merkez", "ankara ek", "istanbul", "izmir", "bursa"]
```

### Current Branch Options
- Ankara Merkez
- Ankara Ek
- Istanbul

### Current Floor Options
- Floors 1-10

## 🐛 Known Issues and Solutions

### Photo Display Issue
- Photos are stored in `images/` folder
- Temporary files are automatically cleaned up

### Database Locking
- SQLite connections are closed after each operation
- Error management provided with try-except blocks

### UI Files
- `.ui` files created with PyQt Designer
- Python converted versions are in `*_UI.py` files

## 🔄 Updates and Development

### Adding New Features
1. First add required functions in `database.py`
2. Update UI files
3. Update related window logic files

### Backup Recommendation
- Regularly backup the `erp_database.db` file
- Don't forget to backup the `images/` folder as well

**Note**: This system is designed for small and medium-scale organizations. For large-scale usage, migration to more powerful databases like PostgreSQL or MySQL is recommended.
