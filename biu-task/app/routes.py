from flask import Blueprint, render_template, request,flash, redirect, url_for, current_app, Flask
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, exc
from .selenium_utils import fetch_elearning_tasks
from sqlalchemy.orm import sessionmaker
from .email_utils import send_email
from datetime import datetime
import pytz
from cryptography.fernet import Fernet
import json
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.DEBUG)

bp = Blueprint('main', __name__)
# Load encryption key dari environment variable
key = os.getenv("ENCRYPTION_KEY")
if not key:
    raise ValueError("Encryption key tidak ditemukan di environment variable.")
cipher_suite = Fernet(key.encode())
def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    # Initialize scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()

    app.scheduler = scheduler
    app.register_blueprint(bp)
    return app



@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        logging.debug(f"Received registration data: username={username}, email={email}")

        # Validasi input pengguna
        if not username.strip() or not password.strip() or not email.strip():
            flash("All fields are required!", "warning")
            return redirect(url_for('main.register'))

        try:
            # Enkripsi password
            encrypted_password = cipher_suite.encrypt(password.encode())

            # Buat koneksi ke database
            engine = create_engine("postgresql://postgres.koepkwhgtyjeoqmzsmmy:Rafif123.@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres")
            metadata = MetaData()
            user_table = Table(
                "users", metadata,
                Column("id", Integer, primary_key=True),
                Column("username", String, unique=True, nullable=False),
                Column("password", String, nullable=False),  # Simpan password terenkripsi
                Column("email", String, unique=True, nullable=False)
            )

            Session = sessionmaker(bind=engine)
            session = Session()

            # Periksa apakah username atau email sudah ada
            existing_user = session.query(user_table).filter(
                (user_table.c.username == username) | (user_table.c.email == email)
            ).first()

            if existing_user:
                flash("User with the same username or email already exists!", "warning")
                return redirect(url_for('main.register'))

            # Insert user baru ke database
            new_user = user_table.insert().values(
                username=username,
                password=encrypted_password.decode(),  # Simpan sebagai string
                email=email
            )
            session.execute(new_user)
            session.commit()
            logging.debug(f"User {username} inserted into the database successfully.")
            flash('Registration successful!', 'success')

        except exc.IntegrityError:
            logging.error(f"Integrity error for user {username}: username or email already exists.")
            flash("Username or email already exists!", "warning")
            return redirect(url_for('main.register'))
        except Exception as e:
            logging.error(f"Error inserting user {username} into the database: {e}")
            flash(f"Error registering user: {e}", 'danger')
            return redirect(url_for('main.register'))
        finally:
            session.close()

        return redirect(url_for('main.index'))

    return render_template('register.html')
@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        schedule_time = request.form['schedule_time']
        engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
        metadata = MetaData()
        user_table = Table('users', metadata, autoload_with=engine)

        with engine.connect() as connection:
            # Check if user is already registered
            query = user_table.select().where(user_table.c.username == username)
            result = connection.execute(query).fetchone()

            if result is None:
                # User not found, redirect to registration page
                return redirect(url_for('main.register'))

        # Fetch tasks and generate JSON file
        fetch_elearning_tasks(username, password)

        # Read JSON content from file
        # Read JSON content from file
        json_file_path = "hasil_tugas.json"
        if os.path.exists(json_file_path):
            with open(json_file_path, "r", encoding="utf-8") as file:
                all_users_data = json.load(file)

            # Find the user's data in the JSON file
            user_data = next((user for user in all_users_data if user.get('username') and user.get('username').split(' ')[0] == username.split(' ')[0]), None)
            if user_data:
                user_json_content = {
                    "username": username,  # New field
                    "userProfile": user_data.get('userProfile', 'N/A'),  # Renamed field
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
        else:
            return render_template('index.html', message="JSON file not found!")

        # Generate HTML content from JSON data
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

        # Save HTML content to file
        with open("hasil_tugas.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        print("HTML TERSIMPAN")

        # Convert schedule_time from WIB to UTC
        wib = pytz.timezone('Asia/Jakarta')
        utc = pytz.utc
        local_time = wib.localize(datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M'))
        utc_time = local_time.astimezone(utc)

        # Schedule email
        def send_email_job():
            with current_app.app_context():
                send_email('E-learning Tasks', [email], html_content)

        current_app.scheduler.add_job(
            func=send_email_job,
            trigger='date',
            run_date=utc_time
        )

        return render_template('index.html', content=html_content, message="Email scheduled successfully!")
    return render_template('index.html')