import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime


class FinansUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("Kişisel Finans Takipçisi")
        self.root.geometry("800x600")

        # Veritabanı bağlantısı
        self.veritabani_olustur()

        # Ana sekme widget'ı
        self.tab_control = ttk.Notebook(root)

        # Sekmeler
        self.tab_giris = ttk.Frame(self.tab_control)
        self.tab_raporlar = ttk.Frame(self.tab_control)
        self.tab_kategoriler = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab_giris, text="İşlem Girişi")
        self.tab_control.add(self.tab_raporlar, text="Raporlar")
        self.tab_control.add(self.tab_kategoriler, text="Kategoriler")
        self.tab_control.pack(expand=1, fill="both")

        # İşlem Girişi Sekmesi
        self.islem_girisi_olustur()

        # Raporlar Sekmesi
        self.raporlar_olustur()

        # Kategoriler Sekmesi
        self.kategoriler_olustur()

        # Varsayılan kategorileri ekle
        self.varsayilan_kategorileri_ekle()

        # Kategori listelerini güncelle
        self.kategori_listelerini_guncelle()

    def veritabani_olustur(self):
        """Veritabanını oluşturur ve gerekli tabloları ekler"""
        if not os.path.exists('data'):
            os.makedirs('data')

        self.conn = sqlite3.connect('data/finans.db')
        self.cursor = self.conn.cursor()

        # Kategoriler tablosu
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategoriler (
            id INTEGER PRIMARY KEY,
            ad TEXT NOT NULL,
            tip TEXT NOT NULL
        )
        ''')

        # İşlemler tablosu
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS islemler (
            id INTEGER PRIMARY KEY,
            tarih TEXT NOT NULL,
            miktar REAL NOT NULL,
            aciklama TEXT,
            kategori_id INTEGER,
            tip TEXT NOT NULL,
            FOREIGN KEY (kategori_id) REFERENCES kategoriler (id)
        )
        ''')

        self.conn.commit()

    def varsayilan_kategorileri_ekle(self):
        """Varsayılan kategorileri ekler"""
        gider_kategorileri = ["Market", "Kira", "Faturalar", "Ulaşım", "Eğlence", "Sağlık", "Diğer Giderler"]
        gelir_kategorileri = ["Maaş", "Ek Gelir", "Hediye", "Yatırım", "Diğer Gelirler"]

        # Gider kategorileri ekle
        for kategori in gider_kategorileri:
            self.cursor.execute("SELECT COUNT(*) FROM kategoriler WHERE ad = ? AND tip = ?", (kategori, "Gider"))
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute("INSERT INTO kategoriler (ad, tip) VALUES (?, ?)", (kategori, "Gider"))

        # Gelir kategorileri ekle
        for kategori in gelir_kategorileri:
            self.cursor.execute("SELECT COUNT(*) FROM kategoriler WHERE ad = ? AND tip = ?", (kategori, "Gelir"))
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute("INSERT INTO kategoriler (ad, tip) VALUES (?, ?)", (kategori, "Gelir"))

        self.conn.commit()

    def islem_girisi_olustur(self):
        """İşlem girişi sekmesini oluşturur"""
        frame = ttk.LabelFrame(self.tab_giris, text="Yeni İşlem Ekle")
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        # İşlem tipi
        ttk.Label(frame, text="İşlem Tipi:").grid(column=0, row=0, padx=10, pady=10, sticky=tk.W)
        self.islem_tipi = ttk.Combobox(frame, values=["Gelir", "Gider"], state="readonly", width=15)
        self.islem_tipi.grid(column=1, row=0, padx=10, pady=10, sticky=tk.W)
        self.islem_tipi.current(1)  # Varsayılan olarak "Gider" seçili
        self.islem_tipi.bind("<<ComboboxSelected>>", self.kategori_listesini_guncelle)

        # Miktar
        ttk.Label(frame, text="Miktar (TL):").grid(column=0, row=1, padx=10, pady=10, sticky=tk.W)
        self.miktar_var = tk.StringVar()
        self.miktar_entry = ttk.Entry(frame, textvariable=self.miktar_var, width=15)
        self.miktar_entry.grid(column=1, row=1, padx=10, pady=10, sticky=tk.W)

        # Tarih
        ttk.Label(frame, text="Tarih:").grid(column=0, row=2, padx=10, pady=10, sticky=tk.W)
        self.tarih_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.tarih_entry = ttk.Entry(frame, textvariable=self.tarih_var, width=15)
        self.tarih_entry.grid(column=1, row=2, padx=10, pady=10, sticky=tk.W)

        # Kategori
        ttk.Label(frame, text="Kategori:").grid(column=0, row=3, padx=10, pady=10, sticky=tk.W)
        self.kategori_var = tk.StringVar()
        self.kategori_combo = ttk.Combobox(frame, textvariable=self.kategori_var, state="readonly", width=15)
        self.kategori_combo.grid(column=1, row=3, padx=10, pady=10, sticky=tk.W)

        # Açıklama
        ttk.Label(frame, text="Açıklama:").grid(column=0, row=4, padx=10, pady=10, sticky=tk.W)
        self.aciklama_var = tk.StringVar()
        self.aciklama_entry = ttk.Entry(frame, textvariable=self.aciklama_var, width=30)
        self.aciklama_entry.grid(column=1, row=4, padx=10, pady=10, sticky=tk.W)

        # Ekle butonu
        self.ekle_btn = ttk.Button(frame, text="İşlemi Kaydet", command=self.islem_ekle)
        self.ekle_btn.grid(column=0, row=5, columnspan=2, padx=10, pady=10)

        # Son işlemler listesi
        ttk.Label(frame, text="Son İşlemler:").grid(column=2, row=0, padx=10, pady=10, sticky=tk.W)

        # Treeview widget'ı ile son işlemleri gösterme
        self.islemler_tree = ttk.Treeview(frame, columns=("id", "tarih", "tip", "kategori", "miktar", "aciklama"),
                                          show="headings", height=10)
        self.islemler_tree.grid(column=2, row=1, rowspan=5, padx=10, pady=10, sticky=tk.NSEW)

        # Sütun başlıkları
        self.islemler_tree.heading("id", text="ID")
        self.islemler_tree.heading("tarih", text="Tarih")
        self.islemler_tree.heading("tip", text="Tip")
        self.islemler_tree.heading("kategori", text="Kategori")
        self.islemler_tree.heading("miktar", text="Miktar (TL)")
        self.islemler_tree.heading("aciklama", text="Açıklama")

        # Sütun genişlikleri
        self.islemler_tree.column("id", width=30, stretch=False)
        self.islemler_tree.column("tarih", width=80)
        self.islemler_tree.column("tip", width=60)
        self.islemler_tree.column("kategori", width=100)
        self.islemler_tree.column("miktar", width=80)
        self.islemler_tree.column("aciklama", width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.islemler_tree.yview)
        scrollbar.grid(column=3, row=1, rowspan=5, sticky=tk.NS)
        self.islemler_tree.configure(yscrollcommand=scrollbar.set)

        # İşlem yönetimi butonları
        islem_btn_frame = ttk.Frame(frame)
        islem_btn_frame.grid(column=2, row=6, padx=10, pady=5)

        self.islem_sil_btn = ttk.Button(islem_btn_frame, text="Seçili İşlemi Sil", command=self.islem_sil)
        self.islem_sil_btn.pack(side=tk.LEFT, padx=5)

        self.islem_guncelle_btn = ttk.Button(islem_btn_frame, text="Seçili İşlemi Güncelle",
                                             command=self.islem_guncelle_form)
        self.islem_guncelle_btn.pack(side=tk.LEFT, padx=5)

        # Son işlemleri yükle
        self.son_islemleri_yukle()

    def raporlar_olustur(self):
        """Raporlar sekmesini oluşturur"""
        frame = ttk.LabelFrame(self.tab_raporlar, text="Finansal Raporlar")
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Rapor tipi seçimi
        ttk.Label(frame, text="Rapor Tipi:").grid(column=0, row=0, padx=10, pady=10, sticky=tk.W)
        self.rapor_tipi = ttk.Combobox(frame, values=["Aylık Özet", "Kategori Bazlı Harcamalar", "Gelir-Gider Dengesi"],
                                       state="readonly", width=20)
        self.rapor_tipi.grid(column=1, row=0, padx=10, pady=10, sticky=tk.W)
        self.rapor_tipi.current(0)

        # Rapor oluştur butonu
        self.rapor_btn = ttk.Button(frame, text="Rapor Oluştur", command=self.rapor_olustur)
        self.rapor_btn.grid(column=2, row=0, padx=10, pady=10)

        # Grafik alanı
        self.grafik_frame = ttk.Frame(frame)
        self.grafik_frame.grid(column=0, row=1, columnspan=3, padx=10, pady=10, sticky=tk.NSEW)

    def kategoriler_olustur(self):
        """Kategoriler sekmesini oluşturur"""
        frame = ttk.LabelFrame(self.tab_kategoriler, text="Kategori Yönetimi")
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Yeni kategori ekleme
        ttk.Label(frame, text="Kategori Adı:").grid(column=0, row=0, padx=10, pady=10, sticky=tk.W)
        self.yeni_kategori_var = tk.StringVar()
        self.yeni_kategori_entry = ttk.Entry(frame, textvariable=self.yeni_kategori_var, width=20)
        self.yeni_kategori_entry.grid(column=1, row=0, padx=10, pady=10, sticky=tk.W)

        ttk.Label(frame, text="Kategori Tipi:").grid(column=0, row=1, padx=10, pady=10, sticky=tk.W)
        self.yeni_kategori_tipi = ttk.Combobox(frame, values=["Gelir", "Gider"], state="readonly", width=15)
        self.yeni_kategori_tipi.grid(column=1, row=1, padx=10, pady=10, sticky=tk.W)
        self.yeni_kategori_tipi.current(1)  # Varsayılan olarak "Gider" seçili

        self.kategori_ekle_btn = ttk.Button(frame, text="Kategori Ekle", command=self.kategori_ekle)
        self.kategori_ekle_btn.grid(column=0, row=2, columnspan=2, padx=10, pady=10)

        # Mevcut kategoriler listesi
        ttk.Label(frame, text="Mevcut Kategoriler:").grid(column=2, row=0, padx=10, pady=10, sticky=tk.W)

        # Treeview widget'ı ile kategorileri gösterme
        self.kategoriler_tree = ttk.Treeview(frame, columns=("id", "ad", "tip"), show="headings", height=10)
        self.kategoriler_tree.grid(column=2, row=1, rowspan=3, padx=10, pady=10, sticky=tk.NSEW)

        # Sütun başlıkları
        self.kategoriler_tree.heading("id", text="ID")
        self.kategoriler_tree.heading("ad", text="Kategori Adı")
        self.kategoriler_tree.heading("tip", text="Tipi")

        # Sütun genişlikleri
        self.kategoriler_tree.column("id", width=30)
        self.kategoriler_tree.column("ad", width=150)
        self.kategoriler_tree.column("tip", width=80)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.kategoriler_tree.yview)
        scrollbar.grid(column=3, row=1, rowspan=3, sticky=tk.NS)
        self.kategoriler_tree.configure(yscrollcommand=scrollbar.set)

        # Kategori silme butonu
        self.kategori_sil_btn = ttk.Button(frame, text="Seçili Kategoriyi Sil", command=self.kategori_sil)
        self.kategori_sil_btn.grid(column=2, row=4, padx=10, pady=10)

        # Mevcut kategorileri yükle
        self.kategorileri_yukle()

    def kategori_listelerini_guncelle(self):
        """Kategori listelerini günceller"""
        self.kategori_listesini_guncelle(None)
        self.kategorileri_yukle()

    def kategori_listesini_guncelle(self, event):
        """İşlem tipine göre kategori listesini günceller"""
        selected_tip = self.islem_tipi.get()

        # Seçilen tipe göre kategorileri getir
        self.cursor.execute("SELECT ad FROM kategoriler WHERE tip = ?", (selected_tip,))
        kategoriler = [row[0] for row in self.cursor.fetchall()]

        self.kategori_combo['values'] = kategoriler
        if kategoriler:
            self.kategori_combo.current(0)

    def kategorileri_yukle(self):
        """Kategoriler listesini veritabanından yükler"""
        # Önceki verileri temizle
        for i in self.kategoriler_tree.get_children():
            self.kategoriler_tree.delete(i)

        # Kategorileri veritabanından al
        self.cursor.execute("SELECT id, ad, tip FROM kategoriler ORDER BY tip, ad")

        # Kategorileri listeye ekle
        for row in self.cursor.fetchall():
            self.kategoriler_tree.insert("", tk.END, values=row)

    def son_islemleri_yukle(self):
        """Son işlemleri veritabanından yükler"""
        # Önceki verileri temizle
        for i in self.islemler_tree.get_children():
            self.islemler_tree.delete(i)

        # Son 10 işlemi veritabanından al
        self.cursor.execute("""
        SELECT islemler.id, islemler.tarih, islemler.tip, kategoriler.ad, islemler.miktar, islemler.aciklama
        FROM islemler 
        JOIN kategoriler ON islemler.kategori_id = kategoriler.id 
        ORDER BY islemler.tarih DESC LIMIT 10
        """)

        # İşlemleri listeye ekle
        for row in self.cursor.fetchall():
            self.islemler_tree.insert("", tk.END, values=row)

    def islem_ekle(self):
        """Yeni işlem ekler"""
        try:
            # Form alanlarını doğrula
            if not self.miktar_var.get() or not self.tarih_var.get() or not self.kategori_var.get():
                messagebox.showerror("Hata", "Lütfen tüm zorunlu alanları doldurun")
                return

            miktar = float(self.miktar_var.get())
            if miktar <= 0:
                messagebox.showerror("Hata", "Miktar pozitif bir sayı olmalıdır")
                return

            tarih = self.tarih_var.get()
            # Tarih formatını kontrol et
            try:
                datetime.strptime(tarih, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Hata", "Tarih formatı YYYY-AA-GG şeklinde olmalıdır")
                return

            islem_tipi = self.islem_tipi.get()
            kategori_adi = self.kategori_var.get()
            aciklama = self.aciklama_var.get()

            # Kategori ID'sini bul
            self.cursor.execute("SELECT id FROM kategoriler WHERE ad = ? AND tip = ?", (kategori_adi, islem_tipi))
            kategori_id = self.cursor.fetchone()[0]

            # İşlemi veritabanına ekle
            self.cursor.execute("""
            INSERT INTO islemler (tarih, miktar, aciklama, kategori_id, tip) 
            VALUES (?, ?, ?, ?, ?)
            """, (tarih, miktar, aciklama, kategori_id, islem_tipi))

            self.conn.commit()

            # Form alanlarını temizle
            self.miktar_var.set("")
            self.tarih_var.set(datetime.now().strftime("%Y-%m-%d"))
            self.aciklama_var.set("")

            # İşlemler listesini güncelle
            self.son_islemleri_yukle()

            messagebox.showinfo("Başarılı", "İşlem başarıyla kaydedildi")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen miktar için geçerli bir sayı girin")
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem kaydedilirken bir hata oluştu: {str(e)}")

    def kategori_ekle(self):
        """Yeni kategori ekler"""
        try:
            # Form alanlarını doğrula
            kategori_adi = self.yeni_kategori_var.get()
            if not kategori_adi:
                messagebox.showerror("Hata", "Lütfen bir kategori adı girin")
                return

            kategori_tipi = self.yeni_kategori_tipi.get()

            # Kategorinin zaten var olup olmadığını kontrol et
            self.cursor.execute("SELECT COUNT(*) FROM kategoriler WHERE ad = ? AND tip = ?",
                                (kategori_adi, kategori_tipi))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showerror("Hata", "Bu kategori zaten mevcut")
                return

            # Kategoriyi veritabanına ekle
            self.cursor.execute("INSERT INTO kategoriler (ad, tip) VALUES (?, ?)", (kategori_adi, kategori_tipi))
            self.conn.commit()

            # Form alanını temizle
            self.yeni_kategori_var.set("")

            # Kategori listelerini güncelle
            self.kategori_listelerini_guncelle()

            messagebox.showinfo("Başarılı", "Kategori başarıyla eklendi")

        except Exception as e:
            messagebox.showerror("Hata", f"Kategori eklenirken bir hata oluştu: {str(e)}")

    def kategori_sil(self):
        """Seçili kategoriyi siler"""
        # Seçili kategoriyi al
        selected_item = self.kategoriler_tree.selection()
        if not selected_item:
            messagebox.showerror("Hata", "Lütfen silmek için bir kategori seçin")
            return

        kategori_id = self.kategoriler_tree.item(selected_item[0], "values")[0]

        # Bu kategoriye bağlı işlem var mı kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM islemler WHERE kategori_id = ?", (kategori_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror("Hata", "Bu kategoriye bağlı işlemler var. Önce bu işlemleri silmeniz gerekiyor.")
            return

        # Kullanıcıya onay sor
        if messagebox.askyesno("Onay", "Bu kategoriyi silmek istediğinizden emin misiniz?"):
            try:
                self.cursor.execute("DELETE FROM kategoriler WHERE id = ?", (kategori_id,))
                self.conn.commit()

                # Kategori listelerini güncelle
                self.kategori_listelerini_guncelle()

                messagebox.showinfo("Başarılı", "Kategori başarıyla silindi")

            except Exception as e:
                messagebox.showerror("Hata", f"Kategori silinirken bir hata oluştu: {str(e)}")

    def islem_sil(self):
        """Seçili işlemi siler"""
        # Seçili işlemi al
        selected_item = self.islemler_tree.selection()
        if not selected_item:
            messagebox.showerror("Hata", "Lütfen silmek için bir işlem seçin")
            return

        islem_id = self.islemler_tree.item(selected_item[0], "values")[0]

        # Kullanıcıya onay sor
        if messagebox.askyesno("Onay", "Bu işlemi silmek istediğinizden emin misiniz?"):
            try:
                self.cursor.execute("DELETE FROM islemler WHERE id = ?", (islem_id,))
                self.conn.commit()

                # İşlemler listesini güncelle
                self.son_islemleri_yukle()

                messagebox.showinfo("Başarılı", "İşlem başarıyla silindi")

            except Exception as e:
                messagebox.showerror("Hata", f"İşlem silinirken bir hata oluştu: {str(e)}")

    def islem_guncelle_form(self):
        """Seçili işlemi güncellemek için form açar"""
        # Seçili işlemi al
        selected_item = self.islemler_tree.selection()
        if not selected_item:
            messagebox.showerror("Hata", "Lütfen güncellemek için bir işlem seçin")
            return

        islem_values = self.islemler_tree.item(selected_item[0], "values")
        islem_id = islem_values[0]

        # İşlem detaylarını veritabanından al
        self.cursor.execute("""
        SELECT islemler.tarih, islemler.miktar, islemler.aciklama, islemler.tip, kategoriler.ad
        FROM islemler 
        JOIN kategoriler ON islemler.kategori_id = kategoriler.id 
        WHERE islemler.id = ?
        """, (islem_id,))

        islem = self.cursor.fetchone()
        if not islem:
            messagebox.showerror("Hata", "İşlem bulunamadı")
            return

        # Güncelleme penceresini oluştur
        guncelleme_penceresi = tk.Toplevel(self.root)
        guncelleme_penceresi.title("İşlemi Güncelle")
        guncelleme_penceresi.geometry("400x300")
        guncelleme_penceresi.transient(self.root)
        guncelleme_penceresi.grab_set()

        frame = ttk.Frame(guncelleme_penceresi, padding="10")
        frame.pack(fill="both", expand=True)

        # İşlem ID
        ttk.Label(frame, text="İşlem ID:").grid(column=0, row=0, padx=10, pady=5, sticky=tk.W)
        id_var = tk.StringVar(value=islem_id)
        id_entry = ttk.Entry(frame, textvariable=id_var, state="readonly", width=10)
        id_entry.grid(column=1, row=0, padx=10, pady=5, sticky=tk.W)

        # İşlem tipi
        ttk.Label(frame, text="İşlem Tipi:").grid(column=0, row=1, padx=10, pady=5, sticky=tk.W)
        tip_var = tk.StringVar(value=islem[3])
        tip_combo = ttk.Combobox(frame, textvariable=tip_var, values=["Gelir", "Gider"], state="readonly", width=15)
        tip_combo.grid(column=1, row=1, padx=10, pady=5, sticky=tk.W)

        # Miktar
        ttk.Label(frame, text="Miktar (TL):").grid(column=0, row=2, padx=10, pady=5, sticky=tk.W)
        miktar_var = tk.StringVar(value=islem[1])
        miktar_entry = ttk.Entry(frame, textvariable=miktar_var, width=15)
        miktar_entry.grid(column=1, row=2, padx=10, pady=5, sticky=tk.W)

        # Tarih
        ttk.Label(frame, text="Tarih:").grid(column=0, row=3, padx=10, pady=5, sticky=tk.W)
        tarih_var = tk.StringVar(value=islem[0])
        tarih_entry = ttk.Entry(frame, textvariable=tarih_var, width=15)
        tarih_entry.grid(column=1, row=3, padx=10, pady=5, sticky=tk.W)

        # Kategori
        ttk.Label(frame, text="Kategori:").grid(column=0, row=4, padx=10, pady=5, sticky=tk.W)
        kategori_var = tk.StringVar(value=islem[4])

        # İşlem tipine göre kategorileri getir
        self.cursor.execute("SELECT ad FROM kategoriler WHERE tip = ?", (islem[3],))
        kategoriler = [row[0] for row in self.cursor.fetchall()]

        kategori_combo = ttk.Combobox(frame, textvariable=kategori_var, values=kategoriler, state="readonly", width=15)
        kategori_combo.grid(column=1, row=4, padx=10, pady=5, sticky=tk.W)

        # İşlem tipi değiştiğinde kategori listesini güncelle
        def tip_degistiginde(event=None):
            kategori_combo['values'] = []
            selected_tip = tip_var.get()
            self.cursor.execute("SELECT ad FROM kategoriler WHERE tip = ?", (selected_tip,))
            kategoriler = [row[0] for row in self.cursor.fetchall()]
            kategori_combo['values'] = kategoriler
            if kategoriler:
                kategori_combo.current(0)

        tip_combo.bind("<<ComboboxSelected>>", tip_degistiginde)

        # Açıklama
        ttk.Label(frame, text="Açıklama:").grid(column=0, row=5, padx=10, pady=5, sticky=tk.W)
        aciklama_var = tk.StringVar(value=islem[2] if islem[2] else "")
        aciklama_entry = ttk.Entry(frame, textvariable=aciklama_var, width=30)
        aciklama_entry.grid(column=1, row=5, padx=10, pady=5, sticky=tk.W)

        # Güncelleme fonksiyonu
        def guncelle_kaydet():
            try:
                miktar = float(miktar_var.get())
                if miktar <= 0:
                    messagebox.showerror("Hata", "Miktar pozitif bir sayı olmalıdır")
                    return

                tarih = tarih_var.get()
                try:
                    datetime.strptime(tarih, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Hata", "Tarih formatı YYYY-AA-GG şeklinde olmalıdır")
                    return

                yeni_tip = tip_var.get()
                yeni_kategori = kategori_var.get()
                yeni_aciklama = aciklama_var.get()

                # Kategori ID'sini bul
                self.cursor.execute("SELECT id FROM kategoriler WHERE ad = ? AND tip = ?", (yeni_kategori, yeni_tip))
                kategori_id = self.cursor.fetchone()[0]

                # İşlemi güncelle
                self.cursor.execute("""
                UPDATE islemler 
                SET tarih = ?, miktar = ?, aciklama = ?, kategori_id = ?, tip = ?
                WHERE id = ?
                """, (tarih, miktar, yeni_aciklama, kategori_id, yeni_tip, islem_id))

                self.conn.commit()

                # İşlemler listesini güncelle
                self.son_islemleri_yukle()

                messagebox.showinfo("Başarılı", "İşlem başarıyla güncellendi")
                guncelleme_penceresi.destroy()

            except ValueError:
                messagebox.showerror("Hata", "Lütfen miktar için geçerli bir sayı girin")
            except Exception as e:
                messagebox.showerror("Hata", f"İşlem güncellenirken bir hata oluştu: {str(e)}")

        # Butonlar
        buton_frame = ttk.Frame(frame)
        buton_frame.grid(column=0, row=6, columnspan=2, pady=10)

        guncelle_btn = ttk.Button(buton_frame, text="Güncelle", command=guncelle_kaydet)
        guncelle_btn.pack(side=tk.LEFT, padx=5)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=guncelleme_penceresi.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=5)

    def rapor_olustur(self):
        """Seçilen rapor tipine göre grafik oluşturur"""
        # Grafik alanını temizle
        for widget in self.grafik_frame.winfo_children():
            widget.destroy()

        rapor_tipi = self.rapor_tipi.get()

        if rapor_tipi == "Aylık Özet":
            self.aylik_ozet_raporu()
        elif rapor_tipi == "Kategori Bazlı Harcamalar":
            self.kategori_bazli_harcamalar_raporu()
        elif rapor_tipi == "Gelir-Gider Dengesi":
            self.gelir_gider_dengesi_raporu()

    def aylik_ozet_raporu(self):
        """Aylık özet raporu oluşturur"""
        # Verileri al (son 6 ay)
        self.cursor.execute("""
        SELECT strftime('%Y-%m', tarih) as ay, tip, SUM(miktar) as toplam
        FROM islemler
        WHERE tarih >= date('now', '-6 months')
        GROUP BY ay, tip
        ORDER BY ay
        """)

        sonuclar = self.cursor.fetchall()

        if not sonuclar:
            messagebox.showinfo("Bilgi", "Rapor için yeterli veri bulunamadı.")
            return

        # Verileri pandas dataframe'e çevir
        df = pd.DataFrame(sonuclar, columns=['ay', 'tip', 'toplam'])
        pivot_df = df.pivot(index='ay', columns='tip', values='toplam').fillna(0)

        # Grafik oluştur
        fig, ax = plt.subplots(figsize=(8, 4))
        pivot_df.plot(kind='bar', ax=ax)
        ax.set_title('Aylık Gelir-Gider Özeti')
        ax.set_xlabel('Ay')
        ax.set_ylabel('Miktar (TL)')
        plt.tight_layout()

        # Grafik widget'ını oluştur
        canvas = FigureCanvasTkAgg(fig, master=self.grafik_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def kategori_bazli_harcamalar_raporu(self):
        """Kategori bazlı harcamalar raporu oluşturur"""
        # Verileri al
        self.cursor.execute("""
        SELECT k.ad, SUM(i.miktar) as toplam
        FROM islemler i
        JOIN kategoriler k ON i.kategori_id = k.id
        WHERE i.tip = 'Gider' AND i.tarih >= date('now', '-30 days')
        GROUP BY k.ad
        ORDER BY toplam DESC
        """)

        sonuclar = self.cursor.fetchall()

        if not sonuclar:
            messagebox.showinfo("Bilgi", "Rapor için yeterli veri bulunamadı.")
            return

        # Verileri ayır
        kategoriler = [row[0] for row in sonuclar]
        miktarlar = [row[1] for row in sonuclar]

        # Grafik oluştur
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.pie(miktarlar, labels=kategoriler, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Dairenin daire olarak görünmesini sağlar
        ax.set_title('Kategori Bazlı Harcamalar (Son 30 Gün)')
        plt.tight_layout()

        # Grafik widget'ını oluştur
        canvas = FigureCanvasTkAgg(fig, master=self.grafik_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def gelir_gider_dengesi_raporu(self):
        """Gelir-gider dengesi raporu oluşturur"""
        # Verileri al (toplam gelir ve gider)
        self.cursor.execute("""
        SELECT tip, SUM(miktar) as toplam
        FROM islemler
        GROUP BY tip
        """)

        sonuclar = dict(self.cursor.fetchall())

        if not sonuclar or 'Gelir' not in sonuclar or 'Gider' not in sonuclar:
            messagebox.showinfo("Bilgi", "Rapor için yeterli veri bulunamadı.")
            return

        gelir = sonuclar.get('Gelir', 0)
        gider = sonuclar.get('Gider', 0)
        denge = gelir - gider

        # Bilgi etiketi
        bilgi_frame = ttk.Frame(self.grafik_frame)
        bilgi_frame.pack(pady=10)

        ttk.Label(bilgi_frame, text=f"Toplam Gelir: {gelir:.2f} TL", font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(bilgi_frame, text=f"Toplam Gider: {gider:.2f} TL", font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(bilgi_frame, text=f"Denge: {denge:.2f} TL", font=("Arial", 14, "bold"),
                  foreground="green" if denge >= 0 else "red").pack(anchor="w", pady=5)

        # Grafik oluştur
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(['Gelir', 'Gider'], [gelir, gider], color=['green', 'red'])
        ax.set_title('Toplam Gelir-Gider Dengesi')
        ax.set_ylabel('Miktar (TL)')

        # Grafik widget'ını oluştur
        canvas = FigureCanvasTkAgg(fig, master=self.grafik_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# Ana uygulama başlatma
if __name__ == "__main__":
    root = tk.Tk()
    app = FinansUygulamasi(root)
    root.mainloop()