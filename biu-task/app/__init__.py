import json
import os
import logging
from sqlalchemy import create_engine, MetaData, Table
import pytz
from flask import Flask, current_app
from apscheduler.schedulers.background import BackgroundScheduler
from .email_utils import send_email
from apscheduler.triggers.interval import IntervalTrigger
from .selenium_utils import fetch_elearning_tasks
from flask_mail import Mail
from cryptography.fernet import Fernet  # Ganti dengan cryptography untuk enkripsi
from dotenv import load_dotenv

load_dotenv()
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask-Mail
mail = Mail()

# Buat scheduler sebagai variabel global
scheduler = BackgroundScheduler()

# Load encryption key dari environment variable
key = os.getenv("ENCRYPTION_KEY")
if not key:
    raise ValueError("Encryption key tidak ditemukan di environment variable.")
cipher_suite = Fernet(key.encode())

def create_app():
    """
    Factory function untuk membuat dan mengonfigurasi instance Flask.
    """
    app = Flask(__name__)

    # Load konfigurasi dari file config.py
    try:
        app.config.from_pyfile('config.py')
        logger.info("Konfigurasi berhasil dimuat dari config.py")
    except FileNotFoundError:
        logger.error("File config.py tidak ditemukan!")
        raise

    # Cek apakah konfigurasi database ada
    if 'SQLALCHEMY_DATABASE_URI' not in app.config:
        logger.error("Konfigurasi 'SQLALCHEMY_DATABASE_URI' tidak ditemukan di config.py")
        raise ValueError("Konfigurasi 'SQLALCHEMY_DATABASE_URI' tidak ditemukan di config.py")

    # Initialize Flask-Mail
    mail.init_app(app)

    # Inisialisasi scheduler hanya sekali
    if not scheduler.running:
        scheduler.start()

        # Atur timezone ke WIB (Asia/Jakarta)
        wib = pytz.timezone('Asia/Jakarta')

        # Tambahkan job ke scheduler
        scheduler.add_job(
            func=fetch_and_notify,
            trigger=IntervalTrigger(minutes=2, timezone=wib),
            misfire_grace_time=3600  # 1 hour grace period
        )
        logger.info("Scheduler berhasil diinisialisasi dan job ditambahkan")

    # Register blueprint (jika ada)
    with app.app_context():
        try:
            from . import routes
            app.register_blueprint(routes.bp)
            logger.info("Blueprint berhasil diregistrasi")
        except ImportError:
            logger.warning("Tidak ada blueprint yang ditemukan")

    return app

def fetch_and_notify():
    """
    Fungsi untuk mengambil tugas dari e-learning dan mengirim notifikasi via email.
    """
    app = create_app()  # Buat instance aplikasi Flask
    with app.app_context():  # Masuk ke dalam konteks aplikasi
        try:
            # Buat koneksi ke database
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            metadata = MetaData()
            user_table = Table('users', metadata, autoload_with=engine)
            logger.info("Koneksi ke database berhasil dibuat")

            # Ambil data pengguna dari database
            with engine.connect() as connection:
                query = user_table.select().with_only_columns(
                    user_table.c.username, user_table.c.password, user_table.c.email
                )
                result = connection.execute(query).fetchall()
                logger.info(f"Berhasil mengambil {len(result)} pengguna dari database")

                # Proses setiap pengguna
                for row in result:
                    username = row[0]
                    encrypted_password = row[1]  # Password yang sudah dienkripsi
                    email = row[2]

                    # Dekripsi password
                    try:
                        plaintext_password = cipher_suite.decrypt(encrypted_password.encode()).decode()
                        logger.info(f"Password untuk {username} berhasil didekripsi.")
                    except Exception as e:
                        logger.error(f"Gagal mendekripsi password untuk {username}: {e}")
                        continue

                    # Ambil tugas dari e-learning
                    try:
                        fetch_elearning_tasks(username, plaintext_password)  # Gunakan password plaintext
                        logger.info(f"Berhasil mengambil tugas untuk pengguna: {username}")
                    except Exception as e:
                        logger.error(f"Gagal mengambil tugas untuk pengguna {username}: {e}")
                        continue

                    # Baca file JSON hasil tugas
                    json_file_path = "hasil_tugas.json"
                    if os.path.exists(json_file_path):
                        with open(json_file_path, "r", encoding="utf-8") as file:
                            all_users_data = json.load(file)
                    else:
                        all_users_data = []
                        logger.warning(f"File {json_file_path} tidak ditemukan")

                    # Cari data pengguna di file JSON
                    user_data = next(
                        (user for user in all_users_data if user.get('username') and user.get('username').split(' ')[0] == username.split(' ')[0]),
                        None
                    )

                    # Siapkan konten JSON untuk email
                    if user_data:
                        user_json_content = {
                            "username": username,
                            "userProfile": user_data.get('userProfile', 'N/A'),
                            "results": user_data.get('results', []),
                            "statusResults": user_data.get('statusResults', []),
                            "alerts": user_data.get('alerts', [])
                        }
                    else:
                        user_json_content = {
                            "username": "N/A",
                            "userProfile": "N/A",
                            "results": [],
                            "statusResults": [],
                            "alerts": []
                        }

                    # Buat konten HTML untuk email
                    html_content = f"""
                    <html>
                    <head>
                        <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            margin: 0;
                            padding: 20px;
                            background-color: #f4f4f4;
                        }}
                        h1 {{
                            color: #333;
                            border-bottom: 2px solid #eee;
                            padding-bottom: 10px;
                        }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 20px 0;
                        }}
                        th, td {{
                            padding: 12px;
                            text-align: left;
                            border-bottom: 1px solid #ddd;
                        }}
                        th {{
                            background-color: #f2f2f2;
                        }}
                        .status-overdue {{
                            color: red;
                        }}
                        .status-due-today {{
                            color: orange;
                        }}
                        .status-due-tomorrow {{
                            color: green;
                        }}
                        </style>
                    </head>
                    <body>
                        <h1>USERNAME: {user_json_content.get('username', 'N/A')}</h1>
                        <h1>USER PROFILE: {user_json_content.get('userProfile', 'N/A')}</h1>
                        <h1>Hasil Tugas</h1>
                        <table>
                        <tr>
                            <th>Mata Kuliah</th>
                            <th>Tugas Mulai</th>
                            <th>Tugas Selesai</th>
                        </tr>
                    """
                    for result in user_json_content.get('results', []):
                        mata_kuliah = result.get('MataKuliah', 'N/A')
                        tugas_mulai = result.get('Tugas Mulai', 'N/A')
                        tugas_selesai = result.get('Tugas Selesai', 'N/A')
                        html_content += f"<tr><td>{mata_kuliah}</td><td>{tugas_mulai}</td><td>{tugas_selesai}</td></tr>"

                    html_content += """
                        </table>
                        <h1>Status Tugas</h1>
                        <table>
                            <tr>
                                <th>Status</th>
                                <th>Detail</th>
                                <th>User Info</th>
                            </tr>
                    """
                    for status in user_json_content.get('statusResults', []):
                        status_tugas = status.get('Status Tugas', 'N/A')
                        detail = status.get('Detail Belum Kumpul', status.get('Detail Tugas', 'N/A'))
                        user_info = status.get('User Info', 'N/A')
                        html_content += f"<tr><td>{status_tugas}</td><td>{detail}</td><td>{user_info}</td></tr>"

                    html_content += """
                        </table>
                        <h1>Alerts</h1>
                        <ul>
                    """
                    for alert in user_json_content.get('alerts', []):
                        html_content += f"<li>{alert}</li>"

                    html_content += """
                        </ul>
                    </body>
                    </html>
                    """

                    # Kirim email
                    try:
                        send_email("Task Results", [email], html_content)
                        logger.info(f"Email berhasil dikirim ke {email}")
                    except Exception as e:
                        logger.error(f"Gagal mengirim email ke {email}: {e}")

        except Exception as e:
            logger.error(f"Terjadi error saat menjalankan fetch_and_notify: {e}")

# Jalankan aplikasi
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False)  # Nonaktifkan reloader