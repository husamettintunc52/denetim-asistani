import flet as ft
import pandas as pd
import urllib.parse 

def main(page: ft.Page):
    # --- AYARLAR ---
    page.title = "İşletme Denetim Sistemi"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    # Global değişken
    df_global = None 

    # --- YARDIMCI FONKSİYON: TÜRKÇE KARAKTER NORMALİZASYONU ---
    def tr_normalize(text):
        """
        Türkçe karakterleri İngilizce karşılıklarına çevirir ve küçültür.
        Böylece 'ŞEKER', 'şeker', 'seker', 'SEKER' hepsi eşit sayılır.
        """
        if text is None: return ""
        text = str(text)
        
        # Önce problemli harfleri (I ve İ) manuel düzelt
        text = text.replace("İ", "i").replace("I", "ı")
        text = text.lower() # Hepsini küçült
        
        # Diğer Türkçe karakterleri dönüştür
        degisimler = str.maketrans("şçöğüı", "scogui")
        text = text.translate(degisimler)
        
        return text

    # --- FONKSİYONLAR ---

    def dosya_secildi(e: ft.FilePickerResultEvent):
        nonlocal df_global
        if e.files:
            dosya_yolu = e.files[0].path
            bilgi_mesaji.value = "Dosya işleniyor, lütfen bekleyin..."
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
                
                # --- KRİTİK ADIM: ARAMA İÇİN GİZLİ SÜTUN OLUŞTURMA ---
                # İşletme Adı ve Firma Adını birleştirip normalize ediyoruz.
                # Arama işlemini bu gizli sütun üzerinde yapacağız.
                
                # Lambda fonksiyonu ile her satırı normalize et
                df_global["Gizli_Arama_Metni"] = df_global.apply(
                    lambda row: tr_normalize(row["İşletme Adı"] + " " + row["Firma Adı"]), 
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
        ham_aranan = arama_kutusu.value
        # Kullanıcının yazdığını da normalize et (ş -> s, İ -> i)
        aranan = tr_normalize(ham_aranan)
        
        sonuc_listesi.controls.clear()
        
        if df_global is not None and len(aranan) > 1:
            # Aramayı oluşturduğumuz "Gizli_Arama_Metni" sütununda yapıyoruz
            filtrelenmis = df_global[df_global["Gizli_Arama_Metni"].str.contains(aranan, na=False)]
            
            for index, row in filtrelenmis.iterrows():
                # Listeleme Görünümü
                sonuc_listesi.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.Icons.STORE_MALL_DIRECTORY, color="blue"), 
                            title=ft.Text(row["İşletme Adı"], weight="bold"),
                            # Firma adını da subtitle'a ekledim ki neden bulduğunu gör
                            subtitle=ft.Text(f"{row['Firma Adı']}\n{row['İlçe']}", size=12),
                            is_three_line=True,
                            on_click=lambda x, r=row: detay_goster(r)
                        )
                    )
                )
        page.update()

    def harita_ac(servis, adres):
        encoded_adres = urllib.parse.quote(adres)
        url = ""
        if servis == "google":
            url = f"https://www.google.com/maps/search/?api=1&query={encoded_adres}"
        elif servis == "yandex":
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
                ft.Text(f"{row['Adres']}"),
                
                ft.Divider(),
                ft.Text("Navigasyon:", size=14, color="grey"),
                
                ft.Row([
                    ft.ElevatedButton(
                        "Google Maps",
                        icon=ft.Icons.MAP, 
                        style=ft.ButtonStyle(color="white", bgcolor="green"),
                        on_click=lambda e: harita_ac("google", row['Adres'])
                    ),
                    ft.ElevatedButton(
                        "Yandex",
                        icon=ft.Icons.NEAR_ME, 
                        style=ft.ButtonStyle(color="white", bgcolor="red"),
                        on_click=lambda e: harita_ac("yandex", row['Adres'])
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
        label="İşletme veya Firma Adı Ara...", 
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