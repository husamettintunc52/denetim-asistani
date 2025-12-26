import flet as ft
import pandas as pd
import urllib.parse 
import re 

def main(page: ft.Page):
    # --- AYARLAR ---
    page.title = "Denetim Asistanı Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    # Global değişkenler
    df_global = None 

    # --- YARDIMCI FONKSİYONLAR ---

    def tr_normalize(text):
        if text is None: return ""
        text = str(text)
        text = text.replace("İ", "i").replace("I", "ı")
        text = text.lower()
        degisimler = str.maketrans("şçöğüı", "scogui")
        text = text.translate(degisimler)
        return text

    def telefon_temizle(tel_no):
        if pd.isna(tel_no) or tel_no == "" or str(tel_no).lower() == "nan":
            return None
        # Sadece rakamları al
        temiz_no = re.sub(r'\D', '', str(tel_no))
        if len(temiz_no) == 10:
            temiz_no = "0" + temiz_no
        return temiz_no

    # Sadece linki bozan teknik karakterleri düzeltir, adres içeriğine dokunmaz
    def teknik_duzeltme(adres):
        if pd.isna(adres): return ""
        adres = str(adres)
        # Excel'deki "Alt+Enter" satır boşluklarını normal boşluğa çevir
        adres = adres.replace("\n", " ").replace("\r", "")
        # Fazla boşlukları tek boşluğa indir
        adres = " ".join(adres.split())
        return adres

    # --- ANA FONKSİYONLAR ---

    def dosya_secildi(e: ft.FilePickerResultEvent):
        nonlocal df_global
        if e.files:
            dosya_yolu = e.files[0].path
            bilgi_mesaji.value = "Yükleniyor..."
            bilgi_mesaji.color = "blue"
            page.update()
            
            try:
                # Excel Okuma
                df_global = pd.read_excel(
                    dosya_yolu, 
                    usecols="C,E,M,N,Q,R,T", 
                    dtype=str 
                )
                
                df_global.columns = [
                    "İşletme Adı", "Kayıt Numarası", "Firma Adı", 
                    "Denetim Tarihi", "Adres", "İlçe", "Cep Telefonu"
                ]
                
                df_global = df_global.fillna("")
                
                # Arama İndeksi
                df_global["Gizli_Arama_Metni"] = df_global.apply(
                    lambda row: tr_normalize(f"{row['İşletme Adı']} {row['Firma Adı']} {row['İlçe']}"), 
                    axis=1
                )
                
                bilgi_mesaji.value = f"Hazır: {len(df_global)} işletme yüklendi."
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

            aranan_kelimeler = tr_normalize(girilen_metin).split()
            
            sonuc_listesi.controls.clear()
            
            if df_global is not None and len(aranan_kelimeler) > 0:
                mask = pd.Series([True] * len(df_global))
                for kelime in aranan_kelimeler:
                    mask = mask & df_global["Gizli_Arama_Metni"].str.contains(kelime, na=False)
                
                filtrelenmis = df_global[mask]
                
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
        # 1. Adresteki teknik hataları (enter boşluklarını) temizle
        sade_adres = teknik_duzeltme(adres)
        
        # 2. Adresin sonuna İlçe ve Şehir ekle (Bulunabilirliği artırır)
        # Ama adresin içindeki No:5, Daire:2 gibi bilgilere DOKUNMA.
        hedef = f"{sade_adres} {ilce} Ordu"
        
        encoded_adres = urllib.parse.quote(hedef)
        
        url = ""
        if servis == "google":
            # Google Maps Linki
            url = f"https://www.google.com/maps/search/?api=1&query={encoded_adres}"
            
        elif servis == "yandex":
            # Yandex Derin Linki (Deep Link)
            # 'yandexmaps://' protokolü direkt uygulamayı açmaya zorlar.
            url = f"yandexmaps://maps.yandex.com.tr/?text={encoded_adres}"
            
        page.launch_url(url)

    def telefon_et(numara):
        temiz_numara = telefon_temizle(numara)
        if temiz_numara:
            page.launch_url(f"tel:{temiz_numara}")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Numara kayıtlı değil!"))
            page.snack_bar.open = True
            page.update()

    def detay_goster(row):
        tel_no = row['Cep Telefonu']
        
        dlg = ft.AlertDialog(
            title=ft.Text(row["İşletme Adı"], size=18, weight="bold"),
            content=ft.Column([
                ft.Text(f"Firma: {row['Firma Adı']}"),
                ft.Divider(),
                ft.Text(f"Kayıt No: {row['Kayıt Numarası']}", weight="bold", color="red"),
                ft.Text(f"Son Denetim: {row['Denetim Tarihi']}"),
                ft.Divider(),
                ft.Text(f"Adres: {row['Adres']}\n({row['İlçe']})", size=13),
                ft.Divider(),
                
                ft.Text("İşlemler:", size=14, color="grey"),
                
                ft.Row([
                    # TELEFON BUTONU
                    ft.IconButton(
                        icon=ft.Icons.PHONE,
                        icon_color="white",
                        bgcolor="green",
                        icon_size=30,
                        tooltip="Ara",
                        on_click=lambda e: telefon_et(tel_no)
                    ),
                    # GOOGLE MAPS BUTONU
                    ft.IconButton(
                        icon=ft.Icons.MAP,
                        icon_color="white",
                        bgcolor="blue",
                        icon_size=30,
                        tooltip="Google Maps",
                        on_click=lambda e: harita_ac("google", row['Adres'], row['İlçe'])
                    ),
                    # YANDEX BUTONU (Kırmızı Y harfi simgesi yerine Navigasyon simgesi)
                    ft.IconButton(
                        icon=ft.Icons.NEAR_ME,
                        icon_color="white",
                        bgcolor="red",
                        icon_size=30,
                        tooltip="Yandex Navigasyon",
                        on_click=lambda e: harita_ac("yandex", row['Adres'], row['İlçe'])
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20)
                
            ], height=350, scroll=ft.ScrollMode.AUTO),
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
            ft.Icon(ft.Icons.SHIELD_MOON, size=30, color="white"), 
            ft.Text("Denetim Asistanı", size=22, weight="bold", color="white")
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=15,
        bgcolor=ft.colors.BLUE_800,
        border_radius=10
    )

    dosya_btn = ft.ElevatedButton(
        "Veritabanını Yükle", 
        icon=ft.Icons.UPLOAD_FILE, 
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["xlsx", "xls"])
    )
    
    bilgi_mesaji = ft.Text("Veri bekleniyor...", italic=True)
    
    arama_kutusu = ft.TextField(
        label="İşletme Ara...", 
        hint_text="Örn: Market Fatsa",
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
