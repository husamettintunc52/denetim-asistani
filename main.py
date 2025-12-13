import flet as ft
import pandas as pd
import urllib.parse 

def main(page: ft.Page):
    # --- AYARLAR ---
    page.title = "İşletme Denetim Sistemi V2"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    # Global değişkenler
    df_global = None 

    # --- YARDIMCI FONKSİYON: TÜRKÇE KARAKTER NORMALİZASYONU ---
    def tr_normalize(text):
        if text is None: return ""
        text = str(text)
        # Karakter düzeltmeleri
        text = text.replace("İ", "i").replace("I", "ı")
        text = text.lower()
        degisimler = str.maketrans("şçöğüı", "scogui")
        text = text.translate(degisimler)
        return text

    # --- FONKSİYONLAR ---

    def dosya_secildi(e: ft.FilePickerResultEvent):
        nonlocal df_global
        if e.files:
            dosya_yolu = e.files[0].path
            bilgi_mesaji.value = "Dosya analiz ediliyor..."
            bilgi_mesaji.color = "blue"
            page.update()
            
            try:
                # Excel Okuma
                df_global = pd.read_excel(
                    dosya_yolu, 
                    usecols="C,E,M,N,Q,R,T", 
                    dtype=str 
                )
                
                # İsimlendirme
                df_global.columns = [
                    "İşletme Adı", "Kayıt Numarası", "Firma Adı", 
                    "Denetim Tarihi", "Adres", "İlçe", "Cep Telefonu"
                ]
                
                df_global = df_global.fillna("")
                
                # --- İYİLEŞTİRME 2: İLÇEYİ DE ARAMAYA DAHİL ET ---
                # Arama havuzuna İşletme, Firma ve İlçeyi ekliyoruz.
                df_global["Gizli_Arama_Metni"] = df_global.apply(
                    lambda row: tr_normalize(f"{row['İşletme Adı']} {row['Firma Adı']} {row['İlçe']}"), 
                    axis=1
                )
                
                bilgi_mesaji.value = f"Hazır: {len(df_global)} işletme indekslendi."
                bilgi_mesaji.color = "green"
                arama_kutusu.disabled = False
                arama_kutusu.focus()
                
            except Exception as ex:
                bilgi_mesaji.value = f"Hata: {ex}"
                bilgi_mesaji.color = "red"
            page.update()

    def arama_yap(e):
        try:
            girilen_metin = arama_kutusu.value
            if not girilen_metin:
                sonuc_listesi.controls.clear()
                page.update()
                return

            # --- İYİLEŞTİRME 1: AKILLI KELİME ARAMA ---
            # "Ordu Cadı Kazanı" bulmak için "Ordu" ve "Kazanı" kelimelerini ayırıyoruz.
            aranan_kelimeler = tr_normalize(girilen_metin).split()
            
            sonuc_listesi.controls.clear()
            
            if df_global is not None and len(aranan_kelimeler) > 0:
                # Pandas içinde filtreleme: Tüm kelimelerin geçtiği satırları bul
                # Mantık: Her kelime için tek tek kontrol et, hepsi varsa (AND) getir.
                mask = pd.Series([True] * len(df_global))
                for kelime in aranan_kelimeler:
                    mask = mask & df_global["Gizli_Arama_Metni"].str.contains(kelime, na=False)
                
                filtrelenmis = df_global[mask]
                
                # --- İYİLEŞTİRME 4: PERFORMANS (İlk 50 sonucu göster) ---
                # Binlerce sonuç gelirse telefon donar, limit koymak iyidir.
                for index, row in filtrelenmis.head(50).iterrows():
                    sonuc_listesi.controls.append(
                        ft.Card(
                            content=ft.ListTile(
                                leading=ft.Icon(ft.Icons.STORE_MALL_DIRECTORY, color="blue"),
                                title=ft.Text(row["İşletme Adı"], weight="bold"),
                                subtitle=ft.Text(f"{row['İlçe']} - {row['Firma Adı']}", size=12),
                                on_click=lambda x, r=row: detay_goster(r)
                            )
                        )
                    )
            page.update()
        except Exception as ex:
            print(f"Arama hatası: {ex}")

    def harita_ac(servis, adres, ilce):
        # --- İYİLEŞTİRME 3: ADRESİ GÜÇLENDİRME ---
        # Sadece mahalle adı yetmez, "Ordu" ve İlçe adını ekleyip garantiye alıyoruz.
        tam_adres = f"{adres}, {ilce}, Ordu, Türkiye"
        encoded_adres = urllib.parse.quote(tam_adres)
        
        url = ""
        if servis == "google":
            url = f"https://www.google.com/maps/search/?api=1&query={encoded_adres}"
        elif servis == "yandex":
            # Yandex mobil için en garanti format
            url = f"https://yandex.com.tr/harita/?text={encoded_adres}"
            
        page.launch_url(url)

    def detay_goster(row):
        dlg = ft.AlertDialog(
            title=ft.Text(row["İşletme Adı"], size=20, weight="bold"),
            content=ft.Column([
                ft.Text(f"Firma: {row['Firma Adı']}", size=16),
                ft.Divider(),
                ft.Text(f"Kayıt No: {row['Kayıt Numarası']}", weight="bold", color="red"),
                ft.Text(f"Tarih: {row['Denetim Tarihi']}"),
                ft.Text(f"Tel: {row['Cep Telefonu']}"),
                ft.Divider(),
                ft.Text("Adres:", weight="bold"),
                ft.Text(f"{row['Adres']} / {row['İlçe']}"),
                
                ft.Divider(),
                ft.Text("Navigasyon Başlat:", size=14, color="grey"),
                
                ft.Row([
                    ft.ElevatedButton(
                        "Google Maps",
                        icon=ft.Icons.MAP, 
                        style=ft.ButtonStyle(color="white", bgcolor="green"),
                        # İlçe bilgisini de fonksiyona gönderiyoruz
                        on_click=lambda e: harita_ac("google", row['Adres'], row['İlçe'])
                    ),
                    ft.ElevatedButton(
                        "Yandex",
                        icon=ft.Icons.NEAR_ME, 
                        style=ft.ButtonStyle(color="white", bgcolor="red"),
                        on_click=lambda e: harita_ac("yandex", row['Adres'], row['İlçe'])
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
                
            ], height=400, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Kapat", on_click=lambda e: page.close(dlg))
            ],
        )
        page.open(dlg)

    # --- ARAYÜZ ---
    
    file_picker = ft.FilePicker(on_result=dosya_secildi)
    page.overlay.append(file_picker)

    header = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=30), 
            ft.Text("Denetim Asistanı", size=22, weight="bold")
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=10,
        bgcolor="#ECEFF1", 
        border_radius=10
    )

    dosya_btn = ft.ElevatedButton(
        "Excel Dosyası Seç", 
        icon=ft.Icons.UPLOAD_FILE, 
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["xlsx", "xls"])
    )
    
    bilgi_mesaji = ft.Text("Veri bekleniyor...", italic=True)
    
    arama_kutusu = ft.TextField(
        label="İşletme, İlçe veya Firma Ara...", 
        hint_text="Örn: A101 Perşembe",
        prefix_icon=ft.Icons.SEARCH, 
        border_radius=20,
        on_change=arama_yap,
        disabled=True
    )
    
    sonuc_listesi = ft.ListView(expand=1, spacing=5, padding=10)

    page.add(
        header,
        ft.Row([dosya_btn], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([bilgi_mesaji], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        arama_kutusu,
        sonuc_listesi
    )

ft.app(target=main)
