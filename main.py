import flet as ft
import pandas as pd
import urllib.parse

def main(page: ft.Page):
    page.title = "İşletme Denetim Sistemi V3.1"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10

    df_global = None

    # ---------- TÜRKÇE NORMALİZASYON ----------
    def tr_normalize(text):
        if text is None:
            return ""
        text = str(text)
        text = text.replace("İ", "i").replace("I", "ı")
        text = text.lower()
        text = text.translate(str.maketrans("şçöğüı", "scogui"))
        return text

    # ---------- DOSYA SEÇ ----------
    def dosya_secildi(e: ft.FilePickerResultEvent):
        nonlocal df_global

        if not e.files:
            return

        bilgi_mesaji.value = "Dosya analiz ediliyor..."
        bilgi_mesaji.color = "blue"
        page.update()

        try:
            df_global = pd.read_excel(
                e.files[0].path,
                usecols="C,E,M,N,Q,R,T",
                dtype=str
            )

            df_global.columns = [
                "İşletme Adı", "Kayıt Numarası", "Firma Adı",
                "Denetim Tarihi", "Adres", "İlçe", "Cep Telefonu"
            ]

            df_global = df_global.fillna("")

            df_global["Gizli_Arama_Metni"] = df_global.apply(
                lambda r: tr_normalize(
                    f"{r['İşletme Adı']} {r['Firma Adı']} {r['İlçe']}"
                ),
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

    # ---------- ARAMA ----------
    def arama_yap(e):
        sonuc_listesi.controls.clear()

        if not arama_kutusu.value or df_global is None:
            page.update()
            return

        kelimeler = tr_normalize(arama_kutusu.value).split()
        mask = pd.Series([True] * len(df_global))

        for k in kelimeler:
            mask &= df_global["Gizli_Arama_Metni"].str.contains(k, na=False)

        for _, row in df_global[mask].head(50).iterrows():
            sonuc_listesi.controls.append(
                ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.STORE, color="blue"),
                        title=ft.Text(row["İşletme Adı"], weight="bold"),
                        subtitle=ft.Text(f"{row['İlçe']} - {row['Firma Adı']}"),
                        on_click=lambda e, r=row: detay_goster(r)
                    )
                )
            )

        page.update()

    # ---------- HARİTA ----------
    def harita_ac(servis, adres, ilce):
        hedef = f"{adres} {ilce} Ordu"
        encoded = urllib.parse.quote(hedef)

        if servis == "google":
            url = f"https://www.google.com/maps/search/?api=1&query={encoded}"
        else:
            url = f"https://maps.yandex.com/?text={encoded}"
            # Direkt navigasyon için:
            # url = f"https://maps.yandex.com/?rtext=~{encoded}&rtt=auto"

        page.launch_url(url)

    # ---------- TELEFON ----------
    def telefon_ara(numara):
        if numara:
            page.launch_url(f"tel:{numara}")

    # ---------- DETAY ----------
    def detay_goster(row):
        dlg = ft.AlertDialog(
            title=ft.Text(row["İşletme Adı"], size=20, weight="bold"),
            content=ft.Column(
                [
                    ft.Text(f"Firma: {row['Firma Adı']}"),
                    ft.Text(f"Kayıt No: {row['Kayıt Numarası']}", color="red"),
                    ft.Text(f"Tarih: {row['Denetim Tarihi']}"),
                    ft.Text(f"Tel: {row['Cep Telefonu']}"),
                    ft.Divider(),
                    ft.Text("Adres:", weight="bold"),
                    ft.Text(f"{row['Adres']} / {row['İlçe']}"),
                    ft.Divider(),
                    ft.Text("İşlem Seç:", color="grey"),

                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Google Maps",
                                icon=ft.Icons.MAP,
                                bgcolor="green",
                                color="white",
                                on_click=lambda e: harita_ac(
                                    "google", row["Adres"], row["İlçe"]
                                ),
                            ),
                            ft.ElevatedButton(
                                "Yandex",
                                icon=ft.Icons.NEAR_ME,
                                bgcolor="red",
                                color="white",
                                on_click=lambda e: harita_ac(
                                    "yandex", row["Adres"], row["İlçe"]
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),

                    ft.ElevatedButton(
                        "📞 Telefonla Ara",
                        icon=ft.Icons.CALL,
                        bgcolor="blue",
                        color="white",
                        on_click=lambda e: telefon_ara(row["Cep Telefonu"]),
                    ),
                ],
                height=420,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[ft.TextButton("Kapat", on_click=lambda e: page.close(dlg))],
        )

        page.open(dlg)

    # ---------- ARAYÜZ ----------
    file_picker = ft.FilePicker(on_result=dosya_secildi)
    page.overlay.append(file_picker)

    header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=30),
                ft.Text("Denetim Asistanı", size=22, weight="bold"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=10,
        bgcolor="#ECEFF1",
        border_radius=10,
    )

    dosya_btn = ft.ElevatedButton(
        "Excel Dosyası Seç",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=False, allowed_extensions=["xlsx", "xls"]
        ),
    )

    bilgi_mesaji = ft.Text("Veri bekleniyor...", italic=True)

    arama_kutusu = ft.TextField(
        label="İşletme / Firma / İlçe Ara",
        prefix_icon=ft.Icons.SEARCH,
        on_change=arama_yap,
        disabled=True,
    )

    sonuc_listesi = ft.ListView(expand=1, spacing=5, padding=10)

    page.add(
        header,
        ft.Row([dosya_btn], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([bilgi_mesaji], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        arama_kutusu,
        sonuc_listesi,
    )

ft.app(target=main)
