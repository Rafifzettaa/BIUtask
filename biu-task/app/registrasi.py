from flask import Flask, request, jsonify
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, exc
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Konfigurasi Database
DATABASE_URL = "postgresql://postgres.koepkwhgtyjeoqmzsmmy:Rafif123.@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Definisi Tabel
user_table = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(120), nullable=False),
    Column("password", String(255), nullable=False),
    Column("email", String(120), nullable=False, unique=True)
)

# Membuat sesi
Session = sessionmaker(bind=engine)

@app.route('/register', methods=['POST'])
def register():
    # Ambil data dari request JSON
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    # Validasi input
    if not username or not password or not email:
        return jsonify({"error": "All fields are required!"}), 400

    try:
        # Periksa apakah user sudah ada
        with engine.connect() as connection:
            query = user_table.select().where(user_table.c.username == username)
            result = connection.execute(query).fetchone()

            if result:
                return jsonify({"error": "Username already exists!"}), 400

        # Menggunakan sesi untuk melakukan insert
        session = Session()

        # Masukkan data ke tabel
        new_user = user_table.insert().values(
            username=username,
            password=password,  # Pastikan password sudah di-hash
            email=email
        )
        session.execute(new_user)
        session.commit()

        return jsonify({"message": "User registered successfully!"}), 201

    except exc.IntegrityError as e:
        # Menangani error seperti duplikat email
        return jsonify({"error": "Email already exists!"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True)
