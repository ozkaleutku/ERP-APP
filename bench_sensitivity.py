# bench_param_sweep.py
# Tek parametre taraması (Sensitivity/Parametric Analysis) — ERP-APP uyumlu
# Her seferde yalnızca bir parametre değişir: {M, Ns, assigns, transfers}
# Çıktılar: sweep_*.csv ve times_*.png, db_*.png grafikleri

import os, csv, time, math, random, string, sqlite3, argparse
import matplotlib
matplotlib.use("Agg")  # GUI olmadan PNG kaydı
import matplotlib.pyplot as plt

HERE = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(HERE, "erp_database.db")

# ÇIKTI DOSYALARI
def csv_path(param): return os.path.join(HERE, f"sweep_{param}.csv")
def png_times(param): return os.path.join(HERE, f"times_{param}.png")
def png_db(param):    return os.path.join(HERE, f"db_{param}.png")

# ------------------- Ayarlar -------------------
BASELINE = dict(M=50, Ns=5000, assigns=2000, transfers=500)

DEFAULT_SWEEPS = {
    "M":         [10, 50, 100, 200],
    "Ns":        [500, 2000, 5000, 10000],
    "assigns":   [500, 2000, 5000, 10000],
    "transfers": [100, 500, 1000, 2000],
}

QUICK_SWEEPS = {
    "M":         [10, 30],
    "Ns":        [300, 1200],
    "assigns":   [200, 800],
    "transfers": [80, 200],
}

# Opsiyonel hız ayarı (yalnızca benchmark için)
PRAGMA_FAST = False

# ------------------- DB hazırlık -------------------
def reset_db(path=DB_PATH):
    if os.path.exists(path):
        os.remove(path)
    from database import create_database
    create_database()

def open_conn():
    conn = sqlite3.connect(DB_PATH)
    if PRAGMA_FAST:
        # Sadece BENCHMARK için: veri güvenliği pahasına hız
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("PRAGMA journal_mode=MEMORY")
        conn.execute("PRAGMA temp_store=MEMORY")
    return conn

def ensure_people(conn, k=100):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kisiler'")
    if not cur.fetchone():
        raise RuntimeError("kisiler tablosu yok. create_database() çalışmadı mı?")
    cur.execute("SELECT COUNT(*) FROM kisiler")
    count = cur.fetchone()[0] or 0
    need = max(0, k - count)
    if need:
        rows = [(f"Person_{i}", random.randint(1,10),
                 random.choice(["ankara merkez","ankara ek","istanbul"])) for i in range(need)]
        cur.executemany(
            "INSERT INTO kisiler(kisiisim, bulunankat, bulunansube) VALUES(?,?,?)", rows
        )
        conn.commit()

def rand_code(prefix="IT", digits=4):
    return f"{prefix}{''.join(random.choices(string.digits, k=digits))}"

# ----------- Repo fonksiyon uyumluluk sarmalayıcıları -----------
def call_add_material_type(stokkodu, isim, kategori="genel", foto=None):
    from database import add_stokkodlu_malzeme_tip
    for args in [
        (stokkodu, isim, kategori, foto),
        (stokkodu, isim, kategori),
        (stokkodu, isim),
        (stokkodu,)
    ]:
        try:
            return add_stokkodlu_malzeme_tip(*args)
        except TypeError:
            continue
    raise

def call_add_sticker_bulk(stokkodu, adet):
    """Önce (stokkodu, adet) hızlı yol; olmazsa adet kez tek tek üret."""
    from database import add_sticker_stokkodlutablo
    try:
        return add_sticker_stokkodlutablo(stokkodu, int(adet))
    except TypeError:
        for _ in range(int(adet)):
            add_sticker_stokkodlutablo(stokkodu)

def call_assign(kisiisim, stickerkod, isim=None):
    from database import add_zimmetle_malzeme
    for args in [
        (kisiisim, stickerkod, isim),
        (kisiisim, stickerkod),
        (stickerkod, kisiisim)  # olası sıra farkı
    ]:
        try:
            return add_zimmetle_malzeme(*args)
        except TypeError:
            continue
    raise

def call_transfer(stickerkod, yeni_kisi):
    from database import update_varolana_yenizimmet
    for args in [
        (stickerkod, yeni_kisi),
        (yeni_kisi, stickerkod)  # olası sıra farkı
    ]:
        try:
            return update_varolana_yenizimmet(*args)
        except TypeError:
            continue
    raise

# ------------------- Tek koşu -------------------
def bench_case(M, Ns, assigns, transfers):
    """
    M: malzeme tipi sayısı
    Ns: stok kodu başına sticker adedi (bulk)
    assigns: toplam zimmet sayısı (toplam sticker ile sınırlandırılır)
    transfers: toplam transfer sayısı (assigns ile sınırlandırılır)
    """
    reset_db()
    conn = open_conn()
    ensure_people(conn, k=100)

    # 1) Malzeme tipleri
    materials = [rand_code("IT", 4) for _ in range(M)]
    for code in materials:
        call_add_material_type(code, f"Name_{code}", "genel", None)

    # 2) Sticker üretimi — hızlı yol
    t0 = time.perf_counter()
    for code in materials:
        call_add_sticker_bulk(code, Ns)
    t1 = time.perf_counter()

    total_stickers = M * Ns
    assigns_eff = min(assigns, total_stickers)  # aşımı engelle
    transfers_eff = min(transfers, assigns_eff)

    # 3) Kişiler + sticker örnekle
    cur = conn.cursor()
    cur.execute("SELECT kisiisim FROM kisiler")
    people = [r[0] for r in cur.fetchall()]
    if not people:
        raise RuntimeError("Kayıtlı kişi yok.")

    # Assigns'e göre ihtiyacımız kadar sticker çekelim
    per_code_need = max(1, math.ceil(assigns_eff / max(1, M)))
    stickers = []
    for code in materials:
        cur.execute(f"SELECT stickerkod FROM stok_{code} ORDER BY id LIMIT ?", (per_code_need + 10,))
        stickers.extend([r[0] for r in cur.fetchall()])
    random.shuffle(stickers)
    stickers = stickers[:assigns_eff]

    # 4) Zimmet
    t2 = time.perf_counter()
    for s in stickers:
        kisi = random.choice(people)
        try:
            stock_from_code = s.split('_')[1]
            call_assign(kisi, s, f"Name_{stock_from_code}")
        except Exception:
            call_assign(kisi, s)
    t3 = time.perf_counter()

    # 5) Transfer
    t4 = time.perf_counter()
    for s in random.sample(stickers, min(transfers_eff, len(stickers))):
        call_transfer(s, random.choice(people))
    t5 = time.perf_counter()

    conn.close()
    return {
        "M": M, "Ns": Ns, "assigns": assigns_eff, "transfers": transfers_eff,
        "t_create_stickers_s": round(t1 - t0, 4),
        "t_assign_s": round(t3 - t2, 4),
        "t_transfer_s": round(t5 - t4, 4),
        "db_mb": round(os.path.getsize(DB_PATH)/1_000_000, 3),
        "total_stickers": total_stickers
    }

# ------------------- Tarama & Grafik -------------------
def write_csv(rows, path):
    if not rows: return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

def read_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def plot_from_csv(path, param):
    rows = read_csv(path)
    if not rows: print("CSV boş:", path); return

    # tip dönüşümleri
    for r in rows:
        for k in ["M","Ns","assigns","transfers","t_create_stickers_s","t_assign_s","t_transfer_s","db_mb","total_stickers"]:
            r[k] = float(r[k])

    xs = [r[param] for r in rows]
    t_create = [r["t_create_stickers_s"] for r in rows]
    t_assign = [r["t_assign_s"] for r in rows]
    t_transfer = [r["t_transfer_s"] for r in rows]
    db_mb = [r["db_mb"] for r in rows]

    # Zaman grafiği
    plt.figure(figsize=(9,5.5))
    plt.plot(xs, t_create, marker="o", label="Stickering")
    plt.plot(xs, t_assign, marker="o", label="Assign")
    plt.plot(xs, t_transfer, marker="o", label="Transfer")
    plt.xlabel(param); plt.ylabel("Time (s)")
    plt.title(f"{param}")
    plt.legend(); plt.grid(True, alpha=.3); plt.tight_layout()
    out1 = png_times(param); plt.savefig(out1, dpi=170)

    # DB boyutu grafiği
    plt.figure(figsize=(9,5.5))
    plt.plot(xs, db_mb, marker="o")
    plt.xlabel(param); plt.ylabel("DB boyutu (MB)")
    plt.title(f"DB Boyutu vs {param}")
    plt.grid(True, alpha=.3); plt.tight_layout()
    out2 = png_db(param); plt.savefig(out2, dpi=170)
    print(f"[{param}] Grafikler yazıldı:\n - {out1}\n - {out2}")

def sweep(param, values, baseline):
    print(f"\n=== {param} taraması: {values} (diğerleri sabit: {baseline}) ===")
    rows = []
    for v in values:
        cfg = baseline.copy()
        cfg[param] = v
        print(f"  -> {cfg}")
        res = bench_case(**cfg)
        rows.append({"vary": param, "value": v, **res})
        print(f"     {res}")
    out_csv = csv_path(param)
    write_csv(rows, out_csv)
    print(f"[{param}] CSV: {out_csv}")
    plot_from_csv(out_csv, param)

# ------------------- CLI -------------------
def main():
    global PRAGMA_FAST
    ap = argparse.ArgumentParser(description="ERP-APP Tek Parametre Duyarlılık Analizi")
    ap.add_argument("--quick", action="store_true", help="Küçük hızlı taramalar")
    ap.add_argument("--fast-pragma", action="store_true", help="Benchmark hız PRAGMA'ları (yalnızca test)")
    ap.add_argument("--only", nargs="*", choices=["M","Ns","assigns","transfers"],
                    help="Sadece bu parametre(ler)i tara")
    args = ap.parse_args()

    PRAGMA_FAST = bool(args.fast_pragma)
    sweeps = QUICK_SWEEPS if args.quick else DEFAULT_SWEEPS

    todo = args.only if args.only else ["M","Ns","assigns","transfers"]
    for p in todo:
        sweep(p, sweeps[p], BASELINE)

if __name__ == "__main__":
    main()