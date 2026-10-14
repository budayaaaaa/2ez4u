# ---------- frontend/ui.py ----------
# Satu jendela Tkinter: daftar menu di kiri, form + hasil di kanan,
# panel COMMAND di bawah (perintah, modul, waktu).
#
# Frontend ini HANYA memanggil backend. Seluruh struktur data ada di
# backend/M1_pesanan.py dan backend/M2_antrean.py.
#
# Fitur M2 yang belum ada di backend akan tampil sebagai "belum tersedia",
# bukan crash. Begitu fungsinya kamu tulis, menunya otomatis hidup:
#   - ke_postfix(ekspresi) dan hitung(postfix)      -> STACK - POSTFIX
#   - class Riwayat dengan method:                  -> STACK - UNDO / REDO
#         catat(aksi)                     aksi = ("ENQUEUE", pesanan)
#                                              atau ("DEQUEUE", "naif"/"circular", Array pesanan)
#         undo_last(q_naif, q_circular)  -> teks keterangan, atau None bila kosong
#         redo_last(q_naif, q_circular)  -> teks keterangan, atau None bila kosong

import csv
import os
import sys
import time
import traceback
import tkinter as tk
from tkinter import ttk, messagebox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
CSV_DEFAULT = os.path.join(ROOT, "data", "pesanan.csv")

# ROOT (folder repo) di sys.path  -> supaya "from backend import ..." ketemu,
#                                    di mana pun program dijalankan.
# BACKEND di sys.path             -> HANYA karena baris pertama M2_antrean.py
#                                    adalah "from M1_pesanan import Array".
for _p in (ROOT, BACKEND):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from backend import M1_pesanan as m1
from backend import M2_antrean as m2
from backend import M3_laporan as m3

NAMA_KOLOM = ["oid", "pelanggan", "resto", "menu", "harga", "prioritas",
              "masuk", "selesai", "status"]
KOLOM_TABEL = [("#", 60), ("oid", 90), ("pelanggan", 190), ("resto", 110),
               ("menu", 120), ("harga", 70), ("prio", 40), ("masuk", 70),
               ("selesai", 70), ("status", 70)]
JENIS = {3: "REGULER", 2: "PRIORITAS", 1: "VIP"}   # hanya label UI, bukan struktur backend

WARNA_HEADER = "#2c3e57"
WARNA_AKTIF = "#dfe7f1"


# ------------------------------------------------------------------ util
def jam(detik):
    if detik is None or detik == "":
        return "-"
    s = int(detik)
    return "%02d:%02d:%02d" % (s // 3600, (s % 3600) // 60, s % 60)


def rupiah(x):
    return "{:,}".format(int(x)).replace(",", ".")


def baris_tabel(no, p):
    return (no, p[0], p[1], p[2], p[3], rupiah(p[4]), p[5],
            jam(p[6]), jam(p[7]), p[8])


def baris_detail(p):
    isi = [p[0], p[1], p[2], p[3], rupiah(p[4]),
           p[5] + " (" + JENIS.get(int(p[5]), "?") + ")",
           jam(p[6]), jam(p[7]), p[8]]
    hasil = []
    for k in range(len(NAMA_KOLOM)):
        hasil.append((NAMA_KOLOM[k], isi[k]))
    return hasil


def ke_angka(teks, nama, minimum=None, maksimum=None):
    try:
        v = int(teks.strip())
    except ValueError:
        raise ValueError(nama + " harus berupa angka bulat.")
    if minimum is not None and v < minimum:
        raise ValueError(nama + " minimal " + str(minimum) + ".")
    if maksimum is not None and v > maksimum:
        raise ValueError(nama + " maksimal " + str(maksimum) + ".")
    return v


def lokasi_error(e):
    """Cari frame terakhir yang berada di dalam folder backend/."""
    for fr in reversed(traceback.extract_tb(e.__traceback__)):
        if os.path.abspath(fr.filename).startswith(BACKEND):
            return (os.path.basename(fr.filename) + " baris " + str(fr.lineno) +
                    ", fungsi " + fr.name + "():\n    " + (fr.line or "").strip())
    return ""


def ringkas_error(e):
    teks = type(e).__name__ + ": " + str(e)
    lok = lokasi_error(e)
    if lok:
        teks = teks + "\n" + lok
    return teks


def teks_postfix(pf):
    """Backend boleh mengembalikan str, Array M1, atau list."""
    if isinstance(pf, str):
        return pf
    if hasattr(pf, "len") and hasattr(pf, "get"):
        bagian = []
        for k in range(pf.len()):
            bagian.append(str(pf.get(k)))
        return " ".join(bagian)
    return " ".join(str(t) for t in pf)


# ------------------------------------------------------------------ app
class App:
    def __init__(self, root):
        self.root = root
        root.title("2EZ4U Food Delivery")
        root.geometry("1280x800")
        root.minsize(1000, 640)

        self.loaded = False
        self.arr = None
        self.ll = None
        self.q_naif = None
        self.q_circ = None
        self.err_naif = None
        self.err_circ = None
        self.riwayat = None
        self.daftar_oid = None
        self.ms_terakhir = 0
        self.oid_terakhir = 0
        self.tombol_aktif = None

        self._gaya()
        self._bangun_layout()
        self._bangun_menu()
        self.menu_load()

    # ---------------------------------------------------------- layout
    def _gaya(self):
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("Treeview", font=("Courier", 10), rowheight=20)
        st.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        st.configure("Aksi.TButton", font=("Helvetica", 10, "bold"),
                     foreground="white", background=WARNA_HEADER, padding=(18, 6))
        st.map("Aksi.TButton", background=[("active", "#3d5675")])

    def _bangun_layout(self):
        header = tk.Frame(self.root, bg=WARNA_HEADER, height=44)
        header.pack(side="top", fill="x")
        tk.Label(header, text="2EZ4U Food Delivery", bg=WARNA_HEADER, fg="white",
                 font=("Helvetica", 15, "bold")).pack(side="left", padx=14, pady=8)

        self.status = tk.Label(self.root, text="siap", anchor="w", bg=WARNA_HEADER,
                               fg="white", font=("Courier", 10), padx=10)
        self.status.pack(side="bottom", fill="x")

        badan = tk.PanedWindow(self.root, orient="horizontal", sashwidth=4)
        badan.pack(fill="both", expand=True)

        # kiri: menu yang bisa di-scroll
        kiri = tk.Frame(badan, width=300)
        self.kanvas = tk.Canvas(kiri, width=290, highlightthickness=0)
        sb = ttk.Scrollbar(kiri, orient="vertical", command=self.kanvas.yview)
        self.menu_frame = tk.Frame(self.kanvas)
        self.menu_frame.bind("<Configure>", lambda e: self.kanvas.configure(
            scrollregion=self.kanvas.bbox("all")))
        self.kanvas.create_window((0, 0), window=self.menu_frame, anchor="nw")
        self.kanvas.configure(yscrollcommand=sb.set)
        self.kanvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.kanvas.bind_all("<MouseWheel>", lambda e: self.kanvas.yview_scroll(
            int(-e.delta / 120) if abs(e.delta) >= 120 else -e.delta, "units"))
        badan.add(kiri, minsize=260)

        # kanan
        kanan = tk.Frame(badan, padx=14, pady=10)
        badan.add(kanan, minsize=600)

        self.judul = tk.Label(kanan, font=("Helvetica", 13, "bold"), anchor="w")
        self.judul.pack(fill="x")
        self.deskripsi = tk.Label(kanan, font=("Helvetica", 9), fg="#555",
                                  anchor="w", justify="left", wraplength=900)
        self.deskripsi.pack(fill="x", pady=(0, 6))

        self.form = tk.Frame(kanan)
        self.form.pack(fill="x")

        ttk.Separator(kanan).pack(fill="x", pady=8)
        self.info = tk.Label(kanan, font=("Helvetica", 10), anchor="w",
                             justify="left", wraplength=900)
        self.info.pack(fill="x")

        tabel_frame = tk.Frame(kanan)
        tabel_frame.pack(fill="both", expand=True, pady=(6, 6))
        self.tabel = ttk.Treeview(tabel_frame, show="headings")
        vs = ttk.Scrollbar(tabel_frame, orient="vertical", command=self.tabel.yview)
        hs = ttk.Scrollbar(tabel_frame, orient="horizontal", command=self.tabel.xview)
        self.tabel.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tabel.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        tabel_frame.rowconfigure(0, weight=1)
        tabel_frame.columnconfigure(0, weight=1)

        tk.Label(kanan, text="COMMAND", font=("Helvetica", 9, "bold"),
                 anchor="w").pack(fill="x")
        self.command = tk.Text(kanan, height=6, font=("Courier", 10),
                               bg="#f6f6f6", state="disabled")
        self.command.pack(fill="x")

    def _bangun_menu(self):
        grup = [
            ("DATA", [("Load", self.menu_load)]),
            ("M1 - DATA PESANAN", [
                ("ARRAY - LIHAT PESANAN", lambda: self.menu_lihat("array")),
                ("ARRAY - TAMBAH PESANAN REGULER", lambda: self.menu_tambah("array", 3)),
                ("ARRAY - TAMBAH PESANAN PRIORITAS", lambda: self.menu_tambah("array", 2)),
                ("ARRAY - TAMBAH PESANAN VIP", lambda: self.menu_tambah("array", 1)),
                ("ARRAY - HAPUS PESANAN", lambda: self.menu_hapus("array")),
                ("LINKEDLIST - LIHAT PESANAN", lambda: self.menu_lihat("linkedlist")),
                ("LINKEDLIST - TAMBAH PESANAN REGULER", lambda: self.menu_tambah("linkedlist", 3)),
                ("LINKEDLIST - TAMBAH PESANAN PRIORITAS", lambda: self.menu_tambah("linkedlist", 2)),
                ("LINKEDLIST - TAMBAH PESANAN VIP", lambda: self.menu_tambah("linkedlist", 1)),
                ("LINKEDLIST - HAPUS PESANAN", lambda: self.menu_hapus("linkedlist")),
            ]),
            ("M2 - STACK DAN QUEUE", [
                ("STACK - POSTFIX (MESIN KASIR)", self.menu_postfix),
                ("STACK - UNDO", lambda: self.menu_undo_redo("undo")),
                ("STACK - REDO", lambda: self.menu_undo_redo("redo")),
                ("QUEUE - ENQUEUE", self.menu_enqueue),
                ("QUEUE - DEQUEUE NAIF", lambda: self.menu_dequeue("naif")),
                ("QUEUE - DEQUEUE CIRCULAR", lambda: self.menu_dequeue("circular")),
                ("QUEUE - LIHAT ANTREAN", self.menu_lihat_antrean),
            ]),
            ("M3 - SORT DAN SEARCH", [
                ("SORT - INSERTION SORT", lambda: self.menu_sort("insertion")),
                ("SORT - MERGE SORT", lambda: self.menu_sort("merge")),
                ("SEARCH - LINEAR SEARCH", lambda: self.menu_search("linear")),
                ("SEARCH - BINARY SEARCH", lambda: self.menu_search("binary")),
            ]),
        ]
        for nama_grup, items in grup:
            tk.Label(self.menu_frame, text=nama_grup, font=("Helvetica", 8, "bold"),
                     fg="#666", anchor="w").pack(fill="x", padx=8, pady=(10, 2))
            for label, fungsi in items:
                b = tk.Button(self.menu_frame, text=label, anchor="w", relief="groove",
                              font=("Helvetica", 9), bg="white", padx=6)
                b.configure(command=lambda b=b, f=fungsi: self._pilih(b, f))
                b.pack(fill="x", padx=8, pady=1)
                if label == "Load":
                    self.tombol_aktif = b
                    b.configure(bg=WARNA_AKTIF)

    def _pilih(self, tombol, fungsi):
        if self.tombol_aktif is not None:
            self.tombol_aktif.configure(bg="white")
        tombol.configure(bg=WARNA_AKTIF)
        self.tombol_aktif = tombol
        fungsi()

    # ---------------------------------------------------------- helper
    def halaman(self, judul, deskripsi, fields, label_tombol, aksi, perlu_data=True):
        """Kosongkan form, buat field baru, sambungkan tombol ke aksi."""
        self.judul.configure(text=judul)
        self.deskripsi.configure(text=deskripsi)
        for w in self.form.winfo_children():
            w.destroy()
        entries = []
        for k in range(len(fields)):
            label, default, petunjuk = fields[k]
            kolom = tk.Frame(self.form)
            kolom.grid(row=0, column=k, sticky="w", padx=(0, 16))
            tk.Label(kolom, text=label, font=("Helvetica", 9, "bold"), anchor="w").pack(fill="x")
            if isinstance(default, (list, tuple)):
                e = ttk.Combobox(kolom, values=list(default), state="readonly", width=16)
                e.set(default[0])
            else:
                e = ttk.Entry(kolom, width=34 if len(fields) == 1 else 18)
                e.insert(0, default)
            e.pack(fill="x")
            if petunjuk:
                tk.Label(kolom, text=petunjuk, font=("Helvetica", 8), fg="#888",
                         anchor="w").pack(fill="x")
            entries.append(e)

        def jalan(_=None):
            self.aman(lambda: aksi([e.get() for e in entries]), perlu_data)

        b = ttk.Button(self.form, text=label_tombol, style="Aksi.TButton", command=jalan)
        b.grid(row=0, column=len(fields), sticky="w", padx=(10, 0))
        for e in entries:
            e.bind("<Return>", jalan)
        self.info.configure(text="")
        self.tabel_kosong()

    def aman(self, fungsi, perlu_data=True):
        if perlu_data and not self.loaded:
            messagebox.showinfo("Data belum dimuat", "Buka menu Load lalu tekan MUAT dulu.")
            return
        try:
            fungsi()
        except ValueError as e:
            messagebox.showwarning("Input tidak valid", str(e))
        except Exception as e:
            traceback.print_exc()
            teks = ringkas_error(e)
            self.info.configure(text="ERROR dari backend: " + teks, fg="#b00020")
            messagebox.showerror("Error di backend",
                                 teks + "\n\nDetail lengkap ada di terminal.")

    def ukur(self, perintah, modul, fungsi):
        t0 = time.perf_counter()
        hasil = fungsi()
        ms = (time.perf_counter() - t0) * 1000
        self.ms_terakhir = ms
        self.log(perintah, modul, ms)
        return hasil

    def log(self, perintah, modul, ms):
        if ms >= 1000:
            waktu = "%.2f s" % (ms / 1000)
        else:
            waktu = "%.2f ms" % ms
        baris = "%-24s -> %-22s %10s\n" % (perintah, modul, waktu)
        self.command.configure(state="normal")
        self.command.insert("1.0", baris)
        self.command.configure(state="disabled")
        self.status.configure(text="[" + modul + "]  " + waktu)

    def tampil(self, teks):
        self.info.configure(text=teks, fg="black")

    def tabel_kosong(self):
        self.tabel.delete(*self.tabel.get_children())
        self.tabel["columns"] = ()

    def tabel_isi(self, kolom, baris):
        self.tabel_kosong()
        nama = [k for k, _ in kolom]
        self.tabel["columns"] = nama
        for k, w in kolom:
            self.tabel.heading(k, text=k)
            self.tabel.column(k, width=w, anchor="w", stretch=(k != "#"))
        for b in baris:
            self.tabel.insert("", "end", values=b)

    def tabel_detail(self, p):
        self.tabel_isi([("kolom", 160), ("isi", 420)], baris_detail(p))

    def pesanan_baru(self, nama, prioritas):
        self.oid_terakhir = self.oid_terakhir + 1
        oid = "O-" + str(self.oid_terakhir).zfill(6)
        lt = time.localtime()
        detik = lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec
        return [oid, nama, "kafe-teknik", "roti-bakar", "12000",
                str(prioritas), str(detik), "", "ANTRE"]

    # ---------------------------------------------------------- DATA
    def menu_load(self):
        self.halaman("Load: muat pesanan.csv",
                     "Membaca CSV lalu mengisi Array dan LinkedList (M1) dengan data yang sama, "
                     "serta kedua antrean (M2) dengan pesanan berstatus ANTRE.",
                     [("Lokasi CSV", CSV_DEFAULT, "default: data/pesanan.csv")],
                     "MUAT", self.aksi_load, perlu_data=False)

    def aksi_load(self, v):
        path = v[0].strip()
        if not os.path.exists(path):
            raise ValueError("File tidak ditemukan:\n" + path)
        self.root.configure(cursor="watch")
        self.status.configure(text="memuat...")
        self.root.update_idletasks()
        try:
            t0 = time.perf_counter()
            rows = []
            with open(path, newline="", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r)                                   # lewati header
                for row in r:
                    rows.append(row)
            self.log("baca_csv", "I/O", (time.perf_counter() - t0) * 1000)

            terbesar = 0
            for row in rows:
                no = int(row[0][2:])
                if no > terbesar:
                    terbesar = no
            self.oid_terakhir = terbesar

            arr = m1.Array()
            ll = m1.LinkList()

            def isi_array():
                for row in rows:
                    arr.append(row)

            def isi_ll():
                for row in rows:
                    ll.append(row)

            self.ukur("load_array", "M1 - array", isi_array)
            self.ukur("load_linkedlist", "M1 - linked list", isi_ll)

            self.arr, self.ll = arr, ll
            self.daftar_oid = None

            # Kedua antrean dimuat TERPISAH: kalau satu gagal di backend,
            # M1 dan antrean satunya tetap bisa dipakai.
            antre = []
            for row in rows:
                if row[8] == "ANTRE":
                    antre.append(row)

            self.q_naif, self.err_naif = self._muat_antrean(
                "naif", lambda: m2.Queue(), antre, "M2 - queue naif")
            self.q_circ, self.err_circ = self._muat_antrean(
                "circular", lambda: m2.CircularQueue(), antre, "M2 - queue circular")

            self.riwayat = m2.Riwayat() if hasattr(m2, "Riwayat") else None
            self.loaded = True
        finally:
            self.root.configure(cursor="")

        teks = (rupiah(len(rows)) + " pesanan dimuat (" + rupiah(len(antre)) + " berstatus ANTRE).\n"
                "Array: " + rupiah(self.arr.len()) + " (kapasitas " + rupiah(self.arr.cap) + ")   "
                "LinkedList: " + rupiah(self.ll.len()))
        teks = teks + "\nAntrean naif: " + self._ringkas_antrean(self.q_naif, self.err_naif)
        teks = teks + "\nAntrean circular: " + self._ringkas_antrean(self.q_circ, self.err_circ)
        self.tampil(teks)
        if self.err_naif or self.err_circ:
            self.info.configure(fg="#b00020")
        baris = []
        for k in range(10):
            baris.append(baris_tabel(k + 1, self.arr.get(k)))
        self.tabel_isi(KOLOM_TABEL, baris)

    def _muat_antrean(self, nama, buat, antre, modul):
        """-> (antrean, None) bila berhasil, atau (None, teks_error) bila backend gagal."""
        try:
            q = buat()

            def isi():
                for row in antre:
                    q.enqueue(row)
            self.ukur("load_queue_" + nama, modul, isi)
            return q, None
        except Exception as e:
            traceback.print_exc()
            self.command.configure(state="normal")
            self.command.insert("1.0", "%-24s -> %-22s %10s\n" % ("load_queue_" + nama, modul, "GAGAL"))
            self.command.configure(state="disabled")
            return None, ringkas_error(e)

    def _ringkas_antrean(self, q, err):
        if q is None:
            return "GAGAL dimuat -> " + err
        try:
            return rupiah(q.len()) + " pesanan"
        except Exception as e:
            return "dimuat, tetapi len() error -> " + ringkas_error(e)

    def _antrean(self, versi):
        q = self.q_naif if versi == "naif" else self.q_circ
        err = self.err_naif if versi == "naif" else self.err_circ
        if q is None:
            raise ValueError("Antrean " + versi + " tidak tersedia karena gagal dimuat dari backend:\n\n" +
                             str(err) + "\n\nPerbaiki di M2_antrean.py lalu tekan Load lagi.")
        return q

    # ---------------------------------------------------------- M1
    def _struktur(self, s):
        if s == "array":
            return self.arr, "M1 - array", "ARRAY"
        return self.ll, "M1 - linked list", "LINKEDLIST"

    def menu_lihat(self, s):
        _, _, nama = self._struktur(s)
        desk = ("Array: tiap pesanan dibaca langsung lewat indeks, O(1)."
                if s == "array" else
                "Linked list: untuk sampai ke posisi ke-i harus menelusuri dari head, O(n). "
                "Coba mulai dari 199990 lalu bandingkan langkahnya dengan menu Array.")
        self.halaman(nama + ": lihat pesanan", desk,
                     [("Mulai dari pesanan ke-", "1", "1 = paling depan"),
                      ("Jumlah", "20", "maksimal 200")],
                     "LIHAT", lambda v: self.aksi_lihat(s, v))

    def aksi_lihat(self, s, v):
        st, modul, nama = self._struktur(s)
        n = st.len()
        if n == 0:
            raise ValueError("Struktur kosong.")
        mulai = ke_angka(v[0], "Mulai", 1, n)
        jumlah = ke_angka(v[1], "Jumlah", 1, 200)
        akhir = mulai - 1 + jumlah
        if akhir > n:
            akhir = n
        hasil = []

        if s == "array":
            def op():
                for i in range(mulai - 1, akhir):
                    hasil.append(st.get(i))
            self.ukur("array_get", modul, op)
            ket = ("Dibaca langsung lewat indeks: " + str(len(hasil)) +
                   " kali get, tanpa penelusuran.")
        else:
            s0 = st.steps
            if hasattr(st, "ambil_rentang"):
                def op():
                    r = st.ambil_rentang(mulai - 1, akhir - mulai + 1)
                    for k in range(r.len()):
                        hasil.append(r.get(k))
                cara = "ambil_rentang (sekali telusur)"
            else:
                def op():
                    for i in range(mulai - 1, akhir):
                        hasil.append(st.get(i))
                cara = "get(i) berulang (tiap get menelusur ulang dari head)"
            self.ukur("linkedlist_get", modul, op)
            ket = ("Penelusuran: " + rupiah(st.steps - s0) + " langkah lewat " + cara + ".")

        self.tampil("Pesanan ke-" + rupiah(mulai) + " s.d. " + rupiah(akhir) +
                    " dari " + rupiah(n) + ".\n" + ket)
        baris = []
        for k in range(len(hasil)):
            baris.append(baris_tabel(mulai + k, hasil[k]))
        self.tabel_isi(KOLOM_TABEL, baris)

    def menu_tambah(self, s, prioritas):
        _, _, nama = self._struktur(s)
        letak = {3: "masuk di barisan paling belakang",
                 2: "menyerobot ke tengah barisan (posisi n/2)",
                 1: "langsung ke urutan pertama"}[prioritas]
        self.halaman(nama + ": pesanan " + JENIS[prioritas] + ", " + letak,
                     "Pesanan baru diberi oid berikutnya. Bandingkan waktu dan geseran/langkahnya "
                     "dengan menu yang sama pada struktur satunya.",
                     [("Nama pelanggan", "Pelanggan Baru", "nama untuk pesanan yang akan dibuat")],
                     "TAMBAH", lambda v: self.aksi_tambah(s, prioritas, v))

    def aksi_tambah(self, s, prioritas, v):
        st, modul, nama = self._struktur(s)
        nama_p = v[0].strip() or "Pelanggan Baru"
        p = self.pesanan_baru(nama_p, prioritas)
        if s == "array":
            self.daftar_oid = None
        n = st.len()
        if prioritas == 3:
            posisi = n
        elif prioritas == 2:
            posisi = n // 2
        else:
            posisi = 0
        perintah = s + "_tambah_" + JENIS[prioritas].lower()

        if s == "array":
            s0 = st.shift
            if prioritas == 3:
                self.ukur(perintah, modul, lambda: st.append(p))
            else:
                self.ukur(perintah, modul, lambda: st.insert(posisi, p))
            biaya = rupiah(st.shift - s0) + " elemen digeser."
        else:
            s0 = st.steps
            if prioritas == 3:
                self.ukur(perintah, modul, lambda: st.append(p))
            elif prioritas == 1:
                self.ukur(perintah, modul, lambda: st.prepend(p))
            else:
                self.ukur(perintah, modul, lambda: st.insert(posisi, p))
            biaya = rupiah(st.steps - s0) + " langkah telusur."

        self.tampil(p[0] + " (" + JENIS[prioritas] + ") masuk di posisi ke-" +
                    rupiah(posisi + 1) + " dari " + rupiah(st.len()) + ". " + biaya)
        self.tabel_detail(p)

    def menu_hapus(self, s):
        _, _, nama = self._struktur(s)
        self.halaman(nama + ": hapus pesanan ke-i",
                     "Pesanan dicabut dari barisan. Array menggeser sisa isinya; "
                     "linked list menelusur sampai simpul sebelumnya lalu menyambung ulang.",
                     [("Pesanan ke-", "1", "1 = paling depan")],
                     "HAPUS", lambda v: self.aksi_hapus(s, v))

    def aksi_hapus(self, s, v):
        st, modul, nama = self._struktur(s)
        n = st.len()
        if n == 0:
            raise ValueError("Struktur kosong, tidak ada yang bisa dihapus.")
        i = ke_angka(v[0], "Pesanan ke-", 1, n)
        if s == "array":
            self.daftar_oid = None
            s0 = st.shift
            p = self.ukur(s + "_hapus", modul, lambda: st.delete(i - 1))
            biaya = rupiah(st.shift - s0) + " elemen digeser."
        else:
            s0 = st.steps
            p = self.ukur(s + "_hapus", modul, lambda: st.delete(i - 1))
            biaya = rupiah(st.steps - s0) + " langkah telusur."
        self.tampil(p[0] + " dihapus dari posisi ke-" + rupiah(i) + ". Sisa " +
                    rupiah(st.len()) + " pesanan. " + biaya)
        self.tabel_detail(p)

    # ---------------------------------------------------------- M2
    def menu_postfix(self):
        self.halaman("Stack: hitung struk lewat postfix",
                     "Tahap 1: infix -> postfix memakai stack operator. "
                     "Tahap 2: postfix dievaluasi memakai stack angka.",
                     [("Struk belanja (infix)", "( 3 * 12000 ) + ( 2 * 8500 ) - 5000",
                       "angka, + - * / dan tanda kurung")],
                     "HITUNG", self.aksi_postfix, perlu_data=False)

    def aksi_postfix(self, v):
        if not (hasattr(m2, "ke_postfix") and hasattr(m2, "hitung")):
            self.tampil("Belum tersedia di backend.\n"
                        "Tambahkan ke M2_antrean.py:  ke_postfix(ekspresi)  dan  hitung(postfix).")
            return
        e = v[0]
        pf = self.ukur("stack_postfix", "M2 - stack", lambda: m2.ke_postfix(e))
        total = self.ukur("stack_hitung", "M2 - stack", lambda: m2.hitung(pf))
        self.tampil("Struk   : " + e + "\nPostfix : " + teks_postfix(pf) +
                    "\nTOTAL   : Rp " + rupiah(total))
        self.tabel_isi([("tahap", 120), ("hasil", 500)],
                       [("infix", e), ("postfix", teks_postfix(pf)),
                        ("total", "Rp " + rupiah(total))])

    def menu_undo_redo(self, jenis):
        if jenis == "undo":
            judul = "Stack: batalkan aksi antrean terakhir"
            desk = "Mengambil catatan teratas tumpukan undo, lalu menjalankan kebalikannya."
        else:
            judul = "Stack: kerjakan lagi aksi yang dibatalkan"
            desk = "Mengambil catatan teratas tumpukan redo, lalu mengerjakan ulang aksi aslinya."
        self.halaman(judul, desk, [], jenis.upper(), lambda v: self.aksi_undo_redo(jenis))

    def aksi_undo_redo(self, jenis):
        if self.riwayat is None:
            self.tampil("Belum tersedia di backend.\n"
                        "Tambahkan class Riwayat di M2_antrean.py dengan method "
                        "catat(aksi), undo_last(q_naif, q_circular), redo_last(q_naif, q_circular).\n"
                        "Kontrak lengkapnya ada di komentar paling atas frontend/ui.py.")
            return
        if jenis == "undo":
            ket = self.ukur("stack_undo", "M2 - stack",
                            lambda: self.riwayat.undo_last(self.q_naif, self.q_circ))
        else:
            ket = self.ukur("stack_redo", "M2 - stack",
                            lambda: self.riwayat.redo_last(self.q_naif, self.q_circ))
        if ket is None:
            ket = "Tumpukan " + jenis + " kosong, tidak ada yang bisa di" + jenis + "."
        self.tampil(str(ket) + "\nAntrean naif: " + self._ringkas_antrean(self.q_naif, self.err_naif) +
                    "\nAntrean circular: " + self._ringkas_antrean(self.q_circ, self.err_circ))
        self.tabel_kosong()

    def menu_enqueue(self):
        self.halaman("Queue: pesanan baru masuk ke belakang",
                     "Menambah pesanan di ujung belakang KEDUA antrean sekaligus. "
                     "O(1) pada kedua versi; perbedaannya baru muncul saat dequeue.",
                     [("Nama pelanggan", "Pelanggan Baru", "untuk pesanan yang akan dibuat")],
                     "ENQUEUE", self.aksi_enqueue)

    def aksi_enqueue(self, v):
        qn = self._antrean("naif")
        qc = self._antrean("circular")
        p = self.pesanan_baru(v[0].strip() or "Pelanggan Baru", 3)

        def op():
            qn.enqueue(p)
            qc.enqueue(p)
        self.ukur("queue_enqueue", "M2 - queue", op)
        if self.riwayat is not None:
            self.riwayat.catat(("ENQUEUE", p))
        self.tampil(p[0] + " masuk ke barisan paling belakang pada KEDUA antrean.\n"
                    "Antrean naif: " + self._ringkas_antrean(qn, None) +
                    "\nAntrean circular: " + self._ringkas_antrean(qc, None))
        self.tabel_detail(p)

    def menu_dequeue(self, versi):
        if versi == "naif":
            judul = "Queue naif: ambil dari depan dengan menggeser isi"
            desk = "Mengambil indeks 0 lalu menggeser seluruh sisa isi satu petak ke kiri. O(n) setiap kali."
        else:
            judul = "Queue circular: ambil dari depan dengan memajukan penunjuk"
            desk = "Hanya penunjuk front yang maju, memakai sisa bagi terhadap kapasitas. O(1)."
        self.halaman(judul, desk,
                     [("Berapa kali dequeue", "1", "coba 1 lalu 100 untuk melihat bedanya")],
                     "DEQUEUE", lambda v: self.aksi_dequeue(versi, v))

    def aksi_dequeue(self, versi, v):
        jumlah = ke_angka(v[0], "Jumlah", 1, 100000)
        q = self._antrean(versi)
        if q.len() == 0:
            raise ValueError("Antrean " + versi + " kosong.")
        keluar = m1.Array()

        def op():
            for k in range(jumlah):
                if q.len() == 0:
                    break
                keluar.append(q.dequeue())

        if versi == "naif":
            s0 = q.items.shift
            self.ukur("queue_dequeue_naive", "M2 - queue naif", op)
            geser = q.items.shift - s0
            rata = geser // keluar.len() if keluar.len() > 0 else 0
            ket = (rupiah(keluar.len()) + " pesanan keluar dari depan antrean naif.\n"
                   "Total " + rupiah(geser) + " elemen digeser, rata-rata " + rupiah(rata) +
                   " geseran per dequeue.\nSisa antrean naif " + rupiah(q.len()) + ".")
        else:
            self.ukur("queue_dequeue_circular", "M2 - queue circular", op)
            ket = (rupiah(keluar.len()) + " pesanan keluar dari depan antrean circular.\n"
                   "Tidak ada elemen yang digeser. front sekarang " + rupiah(q.front) +
                   ", rear " + rupiah(q.rear) + ", kapasitas " + rupiah(q.capacity) + ".\n"
                   "Sisa antrean circular " + rupiah(q.len()) + ".")

        if self.riwayat is not None and keluar.len() > 0:
            self.riwayat.catat(("DEQUEUE", versi, keluar))
        self.tampil(ket)
        baris = []
        for k in range(keluar.len()):
            baris.append(baris_tabel(k + 1, keluar.get(k)))
        self.tabel_isi(KOLOM_TABEL, baris)

    def menu_lihat_antrean(self):
        self.halaman("Queue: lihat isi depan kedua antrean",
                     "Menampilkan N pesanan terdepan dari antrean naif dan circular berdampingan. "
                     "Kalau kamu melakukan dequeue yang sama pada keduanya, kolom 'sama' harus OK semua.",
                     [("Jumlah", "20", "maksimal 200")],
                     "LIHAT", self.aksi_lihat_antrean)

    def aksi_lihat_antrean(self, v):
        n = ke_angka(v[0], "Jumlah", 1, 200)
        qn = self._antrean("naif")
        qc = self._antrean("circular")
        baris = []
        batas = max(qn.len(), qc.len())
        if n < batas:
            batas = n
        for k in range(batas):
            a = qn.items.get(k) if k < qn.len() else None
            b = qc.ambil(k) if k < qc.len() else None
            oid_a = a[0] if a else "-"
            oid_b = b[0] if b else "-"
            nama_b = b[1] if b else "-"
            baris.append((k + 1, oid_a, oid_b, nama_b, "OK" if oid_a == oid_b else "BEDA"))
        self.tampil("Antrean naif " + rupiah(qn.len()) + " (total geseran " + rupiah(qn.items.shift) +
                    ")   |   circular " + rupiah(qc.len()) + ", front " + rupiah(qc.front) +
                    ", rear " + rupiah(qc.rear) + ", kapasitas " + rupiah(qc.capacity) +
                    ", salinan saat grow " + rupiah(qc.salin))
        self.tabel_isi([("#", 60), ("oid naif", 110), ("oid circular", 110),
                        ("pelanggan", 220), ("sama", 60)], baris)

    # ---------------------------------------------------------- M3
    def salin_awal(self, jumlah):
        hasil = []
        for i in range(jumlah):
            hasil.append(self.arr.get(i))
        return hasil

    def menu_sort(self, jenis):
        if jenis == "insertion":
            judul = "Sort: insertion sort, O(n\u00b2)"
            desk = ("Setiap elemen digeser mundur sampai menemukan tempatnya. Sederhana, tetapi "
                    "kerjanya tumbuh kuadratik: n dua kali lipat, perbandingan kira-kira empat kali lipat. "
                    "Dibatasi " + rupiah(m3.BATAS_INSERTION) + " baris.")
        else:
            judul = "Sort: merge sort, O(n log n)"
            desk = ("Larik dibelah terus sampai satu elemen, lalu potongan yang sudah terurut "
                    "digabung kembali. Sanggup mengurutkan seluruh data.")
        self.halaman(judul, desk,
                     [("Jumlah baris diurutkan", "1000", "diambil dari awal data; coba 1000, 2000, 4000"),
                      ("Diurutkan menurut", ["harga", "oid", "selesai"], "selesai kosong ditaruh paling akhir")],
                     "URUTKAN", lambda v: self.aksi_sort(jenis, v))

    def aksi_sort(self, jenis, v):
        n = ke_angka(v[0], "Jumlah baris", 1, self.arr.len())
        kunci = v[1]
        if jenis == "insertion" and n > m3.BATAS_INSERTION:
            raise ValueError("DITOLAK: insertion sort dibatasi " + rupiah(m3.BATAS_INSERTION) +
                             " baris.\nPakai SORT - MERGE SORT untuk data sebesar ini.")
        daftar = self.salin_awal(n)
        if jenis == "insertion":
            hitung = self.ukur("insertion_sort", "M3 - insertion sort",
                               lambda: m3.insertion_sort(daftar, kunci))
        else:
            hitung = self.ukur("merge_sort", "M3 - merge sort",
                               lambda: m3.merge_sort(daftar, kunci))
        tampil = n
        if tampil > 200:
            tampil = 200
        self.tampil(rupiah(n) + " pesanan diurutkan menurut " + kunci + ".\n" +
                    rupiah(hitung.perbandingan) + " perbandingan, " +
                    rupiah(hitung.pemindahan) + " pemindahan.\n"
                    "Ditampilkan " + rupiah(tampil) + " baris pertama.")
        baris = []
        for i in range(tampil):
            baris.append(baris_tabel(i + 1, daftar[i]))
        self.tabel_isi(KOLOM_TABEL, baris)

    def menu_search(self, jenis):
        if jenis == "linear":
            judul = "Search: linear search, O(n)"
            desk = ("Memeriksa pesanan satu per satu dari depan. Tidak menuntut data terurut. "
                    "Kasus terburuk menyentuh seluruh data.")
        else:
            judul = "Search: binary search, O(log n)"
            desk = ("Membuang separuh sisa daftar pada setiap perbandingan. Syaratnya daftar SUDAH "
                    "terurut menurut oid; daftar itu dibangun sekali dengan merge sort lalu dipakai ulang.")
        self.halaman(judul, desk,
                     [("Nomor pesanan (oid)", "O-137442", "format O-000001 sampai O-200000")],
                     "CARI", lambda v: self.aksi_search(jenis, v))

    def aksi_search(self, jenis, v):
        target = v[0].strip().upper()
        if target == "":
            raise ValueError("oid belum diisi.")
        n = self.arr.len()

        if jenis == "linear":
            daftar = self.salin_awal(n)
            idx, banding = self.ukur("linear_search", "M3 - linear search",
                                     lambda: m3.linear_search(daftar, target))
            ket_awal = ""
        else:
            if self.daftar_oid is None:
                daftar_baru = self.salin_awal(n)
                self.ukur("bangun_daftar_oid", "M3 - merge sort",
                          lambda: m3.merge_sort(daftar_baru, "oid"))
                self.daftar_oid = daftar_baru
                ket_awal = ("Daftar terurut oid dibangun sekali dengan merge sort, " +
                            ("%.2f ms" % self.ms_terakhir) + ".\n")
            else:
                ket_awal = "Memakai daftar terurut oid yang sudah dibangun sebelumnya.\n"
            daftar = self.daftar_oid
            idx, banding = self.ukur("binary_search", "M3 - binary search",
                                     lambda: m3.binary_search(daftar, target))

        if idx == -1:
            self.tampil(ket_awal + target + " tidak ditemukan di antara " + rupiah(n) + " baris. " +
                        rupiah(banding) + " perbandingan.")
            self.tabel_kosong()
            return
        self.tampil(ket_awal + "Ditemukan pada indeks " + rupiah(idx) + " (baris ke-" + rupiah(idx + 1) +
                    " dari " + rupiah(n) + ").\n" + rupiah(banding) + " perbandingan.")
        self.tabel_detail(daftar[idx])


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
