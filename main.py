import tkinter as tk
from tkinter import filedialog, messagebox, ttk # ttk modern widget'lar için
from PIL import Image, UnidentifiedImageError
import os
import threading # Uzun süren işlemlerde arayüzün donmaması için

# Global değişkenler (seçilen dosyalar ve çıktı klasörü)
selected_files = []
output_directory = ""

# --- Çekirdek Fonksiyon: Resmi Siyah Beyaza Çevirme ---
def convert_to_grayscale(input_path, output_dir):
    """
    Verilen bir resim dosyasını siyah beyaza çevirir ve belirtilen klasöre kaydeder.
    Başarı durumunu ve hata mesajını (varsa) döndürür.
    """
    try:
        img = Image.open(input_path)
        # 'L' modu: 8-bit piksel, siyah beyaz (luminance)
        bw_img = img.convert('L')

        # Yeni dosya adını oluştur (orijinal ad + _siyahbeyaz)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_filename = f"{name}_siyahbeyaz{ext}"
        output_path = os.path.join(output_dir, output_filename)

        # Kaydetme (Eğer aynı isimde dosya varsa üzerine yazar)
        bw_img.save(output_path)
        return True, None # Başarılı, Hata yok

    except UnidentifiedImageError:
        return False, f"HATA: '{os.path.basename(input_path)}' geçerli bir resim dosyası değil."
    except Exception as e:
        return False, f"HATA: '{os.path.basename(input_path)}' işlenirken hata: {e}"

# --- GUI Fonksiyonları ---

def select_images():
    """Resim dosyalarını seçmek için dosya diyalogunu açar."""
    global selected_files
    # askopenfilenames çoklu dosya seçimine izin verir
    files = filedialog.askopenfilenames(
        title="Siyah Beyaza Çevrilecek Resimleri Seçin",
        filetypes=[("Resim Dosyaları", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                   ("Tüm Dosyalar", "*.*")]
    )
    if files: # Kullanıcı dosya seçtiyse
        selected_files = list(files) # Demet (tuple) yerine liste olarak sakla
        lbl_files_count.config(text=f"{len(selected_files)} resim seçildi.")
        update_status("Resimler seçildi. Kayıt klasörünü seçip 'Dönüştür'e basın.")
    else:
        # Kullanıcı iptal ederse veya bir şey seçmezse listeyi temizle
        selected_files = []
        lbl_files_count.config(text="Hiç resim seçilmedi.")
        update_status("Lütfen işlenecek resimleri seçin.")

def select_output_dir():
    """Siyah beyaz resimlerin kaydedileceği klasörü seçmek için diyalog açar."""
    global output_directory
    directory = filedialog.askdirectory(title="Siyah Beyaz Resimlerin Kaydedileceği Klasörü Seçin")
    if directory: # Kullanıcı bir klasör seçtiyse
        output_directory = directory
        lbl_output_dir.config(text=f"Kayıt Yeri: {output_directory}", wraplength=350) # Uzun yollar için satır atlama
        update_status("Kayıt klasörü seçildi. Resimleri seçip 'Dönüştür'e basın.")
    else:
        # Seçim yapılmazsa temizle
        output_directory = ""
        lbl_output_dir.config(text="Kayıt yeri seçilmedi.")
        update_status("Lütfen çıktıların kaydedileceği klasörü seçin.")

def update_status(message):
    """Durum etiketini günceller."""
    lbl_status.config(text=message)
    root.update_idletasks() # Arayüzün hemen güncellenmesini sağlar

def update_progress(value):
    """İlerleme çubuğunu günceller."""
    progress_bar['value'] = value
    root.update_idletasks() # Arayüzün hemen güncellenmesini sağlar

def process_images_thread():
    """
    Dönüştürme işlemini ayrı bir thread'de çalıştırır.
    Bu, GUI'nin işlem sırasında donmasını engeller.
    """
    global selected_files, output_directory

    if not selected_files:
        messagebox.showwarning("Eksik Bilgi", "Lütfen önce işlenecek resimleri seçin.")
        return
    if not output_directory:
        messagebox.showwarning("Eksik Bilgi", "Lütfen önce kaydedilecek klasörü seçin.")
        return

    # Butonları devre dışı bırak
    btn_select_files.config(state=tk.DISABLED)
    btn_select_output.config(state=tk.DISABLED)
    btn_start.config(state=tk.DISABLED)
    update_status("Dönüştürme işlemi başlıyor...")
    progress_bar.pack(pady=(5, 10), fill=tk.X, padx=10) # İlerleme çubuğunu göster
    update_progress(0)

    success_count = 0
    error_count = 0
    error_messages = []
    total_files = len(selected_files)

    for i, file_path in enumerate(selected_files):
        update_status(f"İşleniyor: {i+1}/{total_files} - {os.path.basename(file_path)}")
        success, error_msg = convert_to_grayscale(file_path, output_directory)
        if success:
            success_count += 1
        else:
            error_count += 1
            if error_msg:
                error_messages.append(error_msg)

        # İlerlemeyi güncelle (% olarak)
        progress = int(((i + 1) / total_files) * 100)
        update_progress(progress)

    # İşlem bittiğinde durumu bildir
    final_message = f"İşlem Tamamlandı! {success_count} resim başarıyla dönüştürüldü."
    if error_count > 0:
        final_message += f" {error_count} resimde hata oluştu."
        # Hataları göstermek için messagebox kullanabiliriz (çok fazla hata varsa sorun olabilir)
        # İlk birkaç hatayı göstermek daha iyi olabilir
        messagebox.showerror("Hatalar", f"{error_count} Hata Oluştu:\n" + "\n".join(error_messages[:5]) + ("\n..." if len(error_messages)>5 else ""))

    update_status(final_message)

    # Butonları tekrar aktif et
    btn_select_files.config(state=tk.NORMAL)
    btn_select_output.config(state=tk.NORMAL)
    btn_start.config(state=tk.NORMAL)
    # İlerleme çubuğunu gizle veya sıfırla
    # progress_bar.pack_forget() # Gizlemek için
    update_progress(0) # Sıfırlamak için


def start_conversion():
    """Dönüştürme işlemini başlatmak için thread oluşturur."""
    # threading.Thread kullanarak process_images_thread fonksiyonunu çağır
    # daemon=True: Ana program kapandığında thread'in de kapanmasını sağlar
    conversion_thread = threading.Thread(target=process_images_thread, daemon=True)
    conversion_thread.start()

# --- Ana GUI Penceresini Oluşturma ---
root = tk.Tk()
root.title("Resim Siyah Beyaz Dönüştürücü v1.0")
root.geometry("450x400") # Pencere boyutunu biraz büyütelim

# Stil (Daha modern görünüm için ttk)
style = ttk.Style()
style.configure("TButton", padding=6, relief="flat", font=('Helvetica', 10))
style.configure("TLabel", padding=5, font=('Helvetica', 10))

# --- Widget'ları Oluşturma ---

# Resim Seçme Butonu ve Etiketi
frame_files = ttk.Frame(root, padding="10")
frame_files.pack(fill=tk.X)
btn_select_files = ttk.Button(frame_files, text="1. Resimleri Seç", command=select_images)
btn_select_files.pack(side=tk.LEFT, padx=(0, 10))
lbl_files_count = ttk.Label(frame_files, text="Hiç resim seçilmedi.")
lbl_files_count.pack(side=tk.LEFT)

# Çıktı Klasörü Seçme Butonu ve Etiketi
frame_output = ttk.Frame(root, padding="10")
frame_output.pack(fill=tk.X)
btn_select_output = ttk.Button(frame_output, text="2. Kayıt Klasörünü Seç", command=select_output_dir)
btn_select_output.pack(side=tk.LEFT, padx=(0, 10))
lbl_output_dir = ttk.Label(frame_output, text="Kayıt yeri seçilmedi.")
lbl_output_dir.pack(side=tk.LEFT)

# Dönüştürme Başlatma Butonu
frame_start = ttk.Frame(root, padding="20")
frame_start.pack()
btn_start = ttk.Button(frame_start, text="3. Dönüştürmeyi Başlat", command=start_conversion)
btn_start.pack()

# İlerleme Çubuğu (Başlangıçta gizli değil, pack ile eklenip çıkarılacak)
progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
# progress_bar.pack(pady=10) # Başlangıçta göstermek yerine işlem başlayınca gösterilecek

# Durum Etiketi
lbl_status = ttk.Label(root, text="Lütfen resimleri ve kayıt klasörünü seçin.", relief=tk.SUNKEN, anchor=tk.W, wraplength=430)
lbl_status.pack(side=tk.BOTTOM, fill=tk.X, ipady=5, padx=5, pady=5)


# --- Ana Döngüyü Başlatma ---
root.mainloop()