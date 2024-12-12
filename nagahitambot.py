import os
import extract_msg
import vobject
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
import logging

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler
)

# Definisikan state untuk conversation
CHOOSING = 0

def convert_msg_to_txt(file_path):
    try:
        msg = extract_msg.Message(file_path)
        txt_file_path = file_path.replace('.msg', '.txt')
        with open(txt_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {msg.subject}\n")
            f.write(f"From: {msg.sender}\n")
            f.write(f"To: {msg.to}\n")
            f.write(f"Date: {msg.date}\n")
            f.write("\nBody:\n")
            f.write(msg.body)
        return txt_file_path
    except Exception as e:
        print(f"Error dalam konversi MSG ke TXT: {str(e)}")
        return None

def convert_txt_to_vcf(file_path, base_name):
    try:
        vcf_file_path = f"downloads/{base_name}.vcf"
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open(vcf_file_path, 'w', encoding='utf-8') as f:
            for i, line in enumerate(lines, start=1):
                contact_info = line.strip()
                if contact_info:
                    f.write("BEGIN:VCARD\n")
                    f.write("VERSION:3.0\n")
                    f.write(f"FN:{base_name} {i}\n")  # Menggunakan nama base dan nomor urut
                    f.write(f"TEL:{contact_info}\n")  # Menyimpan nomor telepon tanpa label
                    f.write("END:VCARD\n")
        
        # Pastikan file VCF tidak kosong
        if os.path.getsize(vcf_file_path) == 0:
            raise ValueError("File VCF kosong setelah konversi.")
        
        return vcf_file_path
    except Exception as e:
        print(f"Error dalam konversi TXT ke VCF: {str(e)}")
        return None

def convert_msg_to_vcf(file_path, adm_number, navy_number):
    try:
        msg = extract_msg.Message(file_path)
        vcf_file_path = file_path.replace('.msg', '.vcf')
        with open(vcf_file_path, 'w', encoding='utf-8') as f:
            # Format ADM
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:3.0\n")
            f.write(f"FN:{msg.sender}\n")
            f.write(f"TEL:{adm_number}\n")  # Nomor ADM tanpa TYPE
            f.write(f"NOTE:SUBJEK: {msg.subject}\n")
            f.write(f"NOTE:TANGGAL: {msg.date}\n")
            f.write(f"NOTE:ISI:\n{msg.body}\n")
            f.write("END:VCARD\n")
            
            # Format NAVY
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:3.0\n")
            f.write(f"FN:{msg.sender}\n")
            f.write(f"TEL:{navy_number}\n")  # Nomor NAVY tanpa TYPE
            f.write(f"NOTE:SUBJEK: {msg.subject}\n")
            f.write(f"NOTE:TANGGAL: {msg.date}\n")
            f.write(f"NOTE:ISI:\n{msg.body}\n")
            f.write("END:VCARD\n")
        
        return vcf_file_path
    except Exception as e:
        print(f"Error dalam konversi MSG ke VCF: {str(e)}")
        return None

def convert_msg_to_adm_navy(file_path, adm_number, navy_number):
    try:
        msg = extract_msg.Message(file_path)
        adm_file_path = file_path.replace('.msg', '_ADM.txt')
        navy_file_path = file_path.replace('.msg', '_NAVY.txt')
        with open(adm_file_path, 'w', encoding='utf-8') as f:
            f.write("=== FORMAT ADM ===\n")
            f.write(f"DARI: {msg.sender}\n")
            f.write(f"UNTUK: {adm_number}\n")  # Menggunakan nomor ADM yang diterima
            f.write(f"TANGGAL: {msg.date}\n")
            f.write(f"SUBJEK: {msg.subject}\n")
            f.write("\nISI:\n")
            f.write(msg.body)
        with open(navy_file_path, 'w', encoding='utf-8') as f:
            f.write("=== FORMAT NAVY ===\n")
            f.write(f"FROM: {msg.sender}\n")
            f.write(f"TO: {navy_number}\n")  # Menggunakan nomor NAVY yang diterima
            f.write(f"DATE: {msg.date}\n")
            f.write(f"SUBJECT: {msg.subject}\n")
            f.write("\nCONTENT:\n")
            f.write(msg.body)
        return (adm_file_path, navy_file_path)
    except Exception as e:
        print(f"Error dalam konversi MSG ke ADM/NAVY: {str(e)}")
        return None

async def start(update: Update, context: CallbackContext):
    """Fungsi untuk menampilkan menu utama dengan keyboard button"""
    user = update.message.from_user
    logger.info(f"User {user.username} ({user.id}) memulai bot.")
    
    keyboard = [
        [KeyboardButton("Start")],
        [KeyboardButton("1️⃣ MSG ke TXT 📝")],
        [KeyboardButton("2️⃣ TXT ke VCF 📱")],
        [KeyboardButton("3️⃣ MSG ke ADM & NAVY 📋")],
        [KeyboardButton("4️⃣ Message ke VCF 📱")],
        [KeyboardButton("ℹ️ Panduan Penggunaan")],
        [KeyboardButton("📄 Format File"), KeyboardButton("👨‍💻 Developer")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    username = f"@{user.username}" if user.username else user.first_name
    welcome_message = (
        f"Halo {username}! 👋\n\n"
        "Selamat datang di *Bot Naga Hitam!* 🤖\n\n"
        "Silakan pilih jenis konversi yang diinginkan atau kirim langsung file yang ingin dikonversi.\n\n"
        "Gunakan menu 'ℹ️ Panduan Penggunaan' untuk informasi lebih detail."
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    return CHOOSING

async def panduan_penggunaan(update: Update, context: CallbackContext):
    """Fungsi untuk menampilkan panduan penggunaan"""
    panduan = (
        "📖 *PANDUAN PENGGUNAAN*\n\n"
        "*1. Konversi MSG ke TXT:*\n"
        "- Kirim file .msg\n"
        "- Bot akan mengembalikan file .txt\n\n"
        "*2. Konversi TXT ke VCF:*\n"
        "- Format TXT Akan Jadi:\n"
        "```\n"
        "Name: Nama Lengkap\n"
        "Phone: +62812xxxxx\n"
        "```\n"
        "- Bot akan mengembalikan file .vcf\n\n"
        "*3. Konversi MSG ke ADM & NAVY:*\n"
        "- Kirim nomor ADM\n"
        "- Kirim nomor NAVY\n"
        "- Bot akan mengembalikan file .vcf\n\n"
        "*4. Konversi Message ke VCF:*\n"
        "- Opsional: Masukkan nama file VCF atau Skip\n"
        "- Masukkan nama kontak\n"
        "- Kirim pesan yang akan disimpan\n"
        "- Bot akan mengembalikan file .vcf dengan pesan dalam catatan"
    )
    await update.message.reply_text(panduan, parse_mode='Markdown')
    return CHOOSING

async def format_file(update: Update, context: CallbackContext):
    """Fungsi untuk menampilkan format file yang didukung"""
    format_info = (
        "📁 *FORMAT FILE YANG DIDUKUNG*\n\n"
        "*1. File MSG (.msg)*\n"
        "- Email dalam format Outlook\n"
        "- Ukuran maksimal 20MB\n\n"
        "*2. File TXT (.txt)*\n"
        "- Format teks biasa\n"
        "- Berisi data kontak\n"
        "- Encoding UTF-8\n\n"
        "❗ *Catatan:*\n"
        "Pastikan file sesuai format untuk hasil optimal"
    )
    await update.message.reply_text(format_info, parse_mode='Markdown')
    return CHOOSING

async def about_dev(update: Update, context: CallbackContext):
    """Fungsi untuk menampilkan informasi developer"""
    about = (
        "👨‍💻 *TENTANG DEVELOPER*\n\n"
        "Bot ini dikembangkan oleh:\n"
        "Nama Developer     : Equinox\n"
        "Hubungi developer  : @damarhatii\n"
        "Hubungi Owner      : @toyng\n"
        "📧 damarhati123@gmail.com"
    )
    await update.message.reply_text(about, parse_mode='Markdown')
    return CHOOSING

async def handle_text(update: Update, context: CallbackContext):
    """Fungsi untuk menangani input teks dari keyboard button"""
    text = update.message.text
    if 'contacts' not in context.user_data:
        context.user_data['contacts'] = []
    if 'filename' not in context.user_data:
        context.user_data['filename'] = 'default_filename'
    if text == "Start":
        return await start(update, context)
    elif text == "1️⃣ MSG ke TXT 📝":
        context.user_data['waiting_for_number'] = True
        await update.message.reply_text(
            "Silakan masukkan nomor yang ingin disimpan."
        )
    elif context.user_data.get('waiting_for_number'):
        context.user_data['number'] = text
        context.user_data['waiting_for_number'] = False
        context.user_data['waiting_for_filename'] = True
        await update.message.reply_text(
            "Silakan masukkan nama file (tanpa ekstensi) untuk menyimpan pesan Anda."
        )
    elif context.user_data.get('waiting_for_filename'):
        context.user_data['filename'] = text
        context.user_data['waiting_for_filename'] = False
        
        # Simpan pesan ke file TXT
        await save_message_to_txt(update, context)
        
    elif text == "2️⃣ TXT ke VCF 📱":
        context.user_data['waiting_for_vcf_filename'] = True
        await update.message.reply_text(
            "Silakan masukkan nama untuk file VCF."
        )
    
    elif context.user_data.get('waiting_for_vcf_filename'):
        # Simpan nama file VCF yang diinput oleh pengguna
        context.user_data['vcf_filename'] = text
        context.user_data['waiting_for_vcf_filename'] = False
        context.user_data['waiting_for_txt_file'] = True
        await update.message.reply_text(
            "Silakan kirim file TXT yang ingin dikonversi."
        )

    elif text == "3️⃣ MSG ke ADM & NAVY 📋":
        context.user_data['adm_numbers'] = []  # Inisialisasi daftar nomor ADM
        context.user_data['navy_numbers'] = []  # Inisialisasi daftar nomor NAVY
        context.user_data['waiting_for_adm_number'] = True
        await update.message.reply_text("Masukkan nomor Admin:")
        
    elif context.user_data.get('waiting_for_adm_number'):
        # Pisahkan input berdasarkan baris baru dan tambahkan ke daftar
        numbers = text.strip().split('\n')
        for number in numbers:
            if number.strip():
                context.user_data['adm_numbers'].append(number.strip())
        
        # Langsung lanjut ke input Navy
        context.user_data['waiting_for_adm_number'] = False
        context.user_data['waiting_for_navy_number'] = True
        await update.message.reply_text("Masukkan nomor Navy:")
    
    elif context.user_data.get('waiting_for_navy_number'):
        # Pisahkan input berdasarkan baris baru dan tambahkan ke daftar
        numbers = text.strip().split('\n')
        for number in numbers:
            if number.strip():
                context.user_data['navy_numbers'].append(number.strip())
        
        # Langsung proses pembuatan VCF
        adm_numbers = context.user_data['adm_numbers']
        navy_numbers = context.user_data['navy_numbers']
        
        # Buat file VCF dengan nomor yang diberikan
        vcf_file_path = create_vcf_from_multiple_numbers(adm_numbers, navy_numbers)
        
        if vcf_file_path:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(vcf_file_path, 'rb'),
                filename="Admin & Navy.vcf"
            )
            await update.message.reply_text("Pesan berhasil dikirim ke dalam file Admin & Navy! ✅")
        else:
            await update.message.reply_text('Terjadi kesalahan: File VCF tidak dapat dibuat.')
        
        # Reset state
        context.user_data['adm_numbers'] = []
        context.user_data['navy_numbers'] = []
        context.user_data['waiting_for_adm_number'] = False
        context.user_data['waiting_for_navy_number'] = False

    elif text == "4️⃣ Message ke VCF 📱":
        context.user_data['waiting_for_vcf_filenames'] = True
        await update.message.reply_text("Silakan masukkan nama file untuk VCF:")
        
    elif context.user_data.get('waiting_for_vcf_filenames'):
        # Simpan nama file VCF yang diinput oleh pengguna
        context.user_data['vcf_filename'] = text
        context.user_data['waiting_for_vcf_filenames'] = False
        context.user_data['waiting_for_name'] = True
        await update.message.reply_text("Masukkan nama kontak:")
        
    elif context.user_data.get('waiting_for_name'):
        # Simpan nama kontak
        name = text.strip()
        context.user_data['current_name'] = name
        context.user_data['waiting_for_name'] = False
        context.user_data['waiting_for_numbers'] = True
        await update.message.reply_text("Masukkan nomor-nomor (satu per baris):")
        
    elif context.user_data.get('waiting_for_numbers'):
        # Pisahkan input berdasarkan baris baru
        numbers = text.strip().split('\n')
        for number in numbers:
            if number.strip():  # Pastikan tidak kosong
                context.user_data['contacts'].append({
                    'name': context.user_data['current_name'],
                    'number': number.strip()
                })
        
        # Buat VCF dari kontak yang diinput
        vcf_file_path = create_vcf_from_contacts(context.user_data['contacts'])
        
        if vcf_file_path:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(vcf_file_path, 'rb'),
                filename=f"{context.user_data[filename]}.vcf"
            )
        await update.message.reply_text("Pesan berhasil dikirim ke dalam file VCF! ✅")
        
        # Reset state
        context.user_data['contacts'] = []
        context.user_data['waiting_for_name'] = False
        context.user_data['waiting_for_numbers'] = False

    elif context.user_data.get('waiting_for_message_vcf'):
        if context.user_data.get('contact_name') is None:
            # Simpan nama kontak
            context.user_data['contact_name'] = text
            await update.message.reply_text(
                f"Nama kontak '{text}' telah disimpan. Silakan kirim pesan yang akan dikonversi ke VCF."
            )
        else:
            # Proses pesan menjadi VCF
            contact_name = context.user_data['contact_name']
            message_text = text
            vcf_filename = context.user_data.get('vcf_filename', contact_name)
            
            # Buat file VCF dari pesan
            vcf_file_path = create_vcf_from_message(contact_name, message_text, vcf_filename)
            
            if vcf_file_path:
                filename = os.path.basename(vcf_file_path)
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=open(vcf_file_path, 'rb'),
                    filename=filename
                )
            else:
                await update.message.reply_text('Terjadi kesalahan: File VCF tidak dapat dibuat.')
            
            # Reset state
            context.user_data['waiting_for_message_vcf'] = False
            context.user_data['contact_name'] = None
            context.user_data['vcf_filename'] = None

    elif text == "ℹ️ Panduan Penggunaan":
        return await panduan_penggunaan(update, context)
    elif text == "📄 Format File":
        return await format_file(update, context)
    elif text == "👨‍💻 Developer":
        return await about_dev(update, context)
    else:
        await update.message.reply_text(
            "Silakan pilih menu yang tersedia atau kirim file untuk dikonversi."
        )
    
    return CHOOSING

async def button(update: Update, context: CallbackContext):
    """Fungsi untuk menangani klik tombol inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'selesai':
        # Jika pengguna mengklik tombol 'Selesai', proses pembuatan VCF
        adm_numbers = context.user_data['adm_numbers']
        navy_numbers = context.user_data['navy_numbers']
        
        # Buat file VCF dengan nomor yang diberikan
        vcf_file_path = create_vcf_from_numbers(adm_numbers, navy_numbers)
        
        if vcf_file_path:
            await context.bot.send_document(chat_id=query.message.chat.id, document=open(vcf_file_path, 'rb'), filename="contacts.vcf")
        else:
            await query.message.reply_text('Terjadi kesalahan: File VCF tidak dapat dibuat.')
        
        # Reset state
        context.user_data['adm_numbers'] = []
        context.user_data['navy_numbers'] = []
        context.user_data['waiting_for_adm_number'] = False
        context.user_data['waiting_for_navy_number'] = False

    # Tambahkan logika lain untuk tombol lainnya jika diperlukan

async def save_message_to_txt(update: Update, context: CallbackContext):
    """Fungsi untuk menyimpan pesan ke file TXT"""
    try:
        number = context.user_data['number']
        filename = f"downloads/{context.user_data['filename']}.txt"
        
        # Pastikan direktori downloads ada
        os.makedirs('downloads', exist_ok=True)
        
        # Tulis nomor ke file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{number}\n")
        
        # Kirim file ke user menggunakan path file
        with open(filename, 'rb') as file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file,
                filename=f"{context.user_data['filename']}.txt"
            )
        
        # Reset state
        context.user_data['waiting_for_message'] = False
        
        # Hapus file setelah dikirim
        cleanup_files(filename)
        
        await update.message.reply_text("Pesan berhasil dikirim ke dalam file TXT! ✅")
    
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")
        context.user_data['waiting_for_message'] = False

async def message_handler(update: Update, context: CallbackContext):
    """Handler untuk semua pesan teks"""
    if context.user_data.get('waiting_for_message'):
        await save_message_to_txt(update, context)
    else:
        await handle_text(update, context)

async def handle_file(update: Update, context: CallbackContext):
    try:
        file = await update.message.document.get_file()
        file_name = update.message.document.file_name
        logger.info(f"User {update.message.from_user.username} mengirim file: {file_name}")
        
        downloaded_file = f"downloads/{file_name}"
        os.makedirs('downloads', exist_ok=True)
        await file.download_to_drive(downloaded_file)
        
        if file_name.lower().endswith('.txt') and context.user_data.get('waiting_for_txt_file'):
            # Proses konversi dari TXT ke VCF
            vcf_filename = context.user_data['vcf_filename']
            vcf_file_path = convert_txt_to_vcf(downloaded_file, vcf_filename)
            
            if vcf_file_path:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=open(vcf_file_path, 'rb'),
                    filename=os.path.basename(vcf_file_path)
                )
                await update.message.reply_text("File VCF berhasil dikirim! ✅")
            else:
                await update.message.reply_text('Terjadi kesalahan: File VCF tidak dapat dibuat.')
            
            # Reset state
            context.user_data['waiting_for_txt_file'] = False
            context.user_data['vcf_filename'] = None

    except Exception as e:
        logger.error(f"Error saat memproses file: {str(e)}")
        await update.message.reply_text(f'Terjadi kesalahan: {str(e)}')

    return CHOOSING

def cleanup_files(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        base_path = os.path.splitext(file_path)[0]
        for ext in ['.txt', '.vcf', '_ADM.txt', '_NAVY.txt']:
            if os.path.exists(base_path + ext):
                os.remove(base_path + ext)
    except Exception as e:
        print(f"Error dalam membersihkan file: {str(e)}")

def create_vcf_from_numbers(adm_numbers, navy_numbers):
    try:
        vcf_file_path = "downloads/Admin & Navy.vcf"  # Tentukan nama file VCF
        with open(vcf_file_path, 'w', encoding='utf-8') as f:
            # Tulis semua nomor dalam satu file VCF
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:3.0\n")
            f.write("FN:Admin\n")
            for adm_number in adm_numbers:
                f.write(f"TEL;TYPE=CELL:{adm_number}\n")
            f.write("END:VCARD\n")
            
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:3.0\n")
            f.write("FN:Navy\n")
            for navy_number in navy_numbers:
                f.write(f"TEL;TYPE=CELL:{navy_number}\n")
            f.write("END:VCARD\n")
        
        return vcf_file_path
    except Exception as e:
        print(f"Error dalam membuat VCF: {str(e)}")
        return None

def create_vcf_from_message(contact_name, message_text, vcf_filename=None):
    """Fungsi untuk membuat file VCF dari pesan"""
    try:
        # Gunakan nama file yang diberikan atau nama kontak jika tidak ada
        filename = vcf_filename if vcf_filename else contact_name
        # Pastikan nama file aman untuk sistem file
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
        vcf_file_path = f"downloads/{safe_filename}.vcf"
        
        with open(vcf_file_path, 'w', encoding='utf-8') as f:
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:3.0\n")
            f.write(f"FN:{contact_name}\n")
            f.write("NOTE:")
            
            # Memecah pesan menjadi baris-baris untuk menghindari baris yang terlalu panjang
            message_lines = message_text.split('\n')
            for line in message_lines:
                # Escape karakter khusus dalam VCF
                escaped_line = line.replace(',', '\\,').replace(';', '\\;')
                f.write(escaped_line + '\\n')
            
            f.write("\n")
            f.write("END:VCARD\n")
        
        return vcf_file_path
    except Exception as e:
        print(f"Error dalam membuat VCF dari pesan: {str(e)}")
        return None

def create_vcf_from_multiple_numbers(adm_numbers, navy_numbers):
    """Fungsi untuk membuat file VCF dari multiple nomor"""
    try:
        vcf_file_path = "downloads/Admin & Navy.vcf"  # Tentukan nama file VCF
        with open(vcf_file_path, 'w', encoding='utf-8') as f:
            # Tulis nomor-nomor Admin
            for i, adm_number in enumerate(adm_numbers, 1):
                f.write("BEGIN:VCARD\n")
                f.write("VERSION:3.0\n")
                f.write(f"FN:Admin {i}\n")  # Menambahkan nomor urut
                f.write(f"TEL;TYPE=CELL:{adm_number}\n")
                f.write("END:VCARD\n")
            
            # Tulis nomor-nomor Navy
            for i, navy_number in enumerate(navy_numbers, 1):
                f.write("BEGIN:VCARD\n")
                f.write("VERSION:3.0\n")
                f.write(f"FN:Navy {i}\n")  # Menambahkan nomor urut
                f.write(f"TEL;TYPE=CELL:{navy_number}\n")
                f.write("END:VCARD\n")
        
        return vcf_file_path
    except Exception as e:
        print(f"Error dalam membuat VCF: {str(e)}")
        return None

def create_vcf_from_contacts(contacts):
    """Fungsi untuk membuat file VCF dari daftar kontak"""
    try:
        vcf_file_path = "downloads/contacts.vcf"
        with open(vcf_file_path, 'w', encoding='utf-8') as f:
            for contact in contacts:
                f.write("BEGIN:VCARD\n")
                f.write("VERSION:3.0\n")
                f.write(f"FN:{contact['name']}\n")
                f.write(f"TEL;TYPE=CELL:{contact['number']}\n")
                f.write("END:VCARD\n")
        
        return vcf_file_path
    except Exception as e:
        print(f"Error dalam membuat VCF: {str(e)}")
        return None

async def convert_and_send_vcf(update: Update, context: CallbackContext, file_path, adm_number, navy_number):
    try:
        vcf_file_path = convert_msg_to_vcf(file_path, adm_number, navy_number)
        
        if vcf_file_path:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(vcf_file_path, 'rb'),
                filename=os.path.basename(vcf_file_path)
            )
            await update.message.reply_text("✅ File VCF Admin dan Navy telah berhasil dibuat dan dikirim! Anda dapat mengimpornya sebagai kontak.")
            await update.message.reply_text("Silakan periksa file yang telah dikirim dan gunakan untuk menyimpan kontak.")
        else:
            await update.message.reply_text('❌ Terjadi kesalahan: File VCF tidak dapat dibuat.')
        
        # Reset state setelah mengirim file
        context.user_data['waiting_for_adm_number'] = False
        context.user_data['waiting_for_navy_number'] = False

    except Exception as e:
        logger.error(f"Error saat mengonversi dan mengirim VCF: {str(e)}")
        await update.message.reply_text(f'❌ Terjadi kesalahan: {str(e)}')

def main():
    application = ApplicationBuilder().token("7663855363:AAGXCVZZt0qS9WcHRS_tv7yXIMDhKQgykME").build()
    
    # Buat conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^Start$'), start)  # Menambahkan entry point untuk tombol "Start"
        ],
        states={
            CHOOSING: [
                MessageHandler(filters.Document.ALL, handle_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^Start$'), handle_text),
                CallbackQueryHandler(button)
            ]
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^Start$'), start)  # Menambahkan fallback untuk tombol "Start"
        ],
        per_chat=True,
        per_user=False,
        per_message=False
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
