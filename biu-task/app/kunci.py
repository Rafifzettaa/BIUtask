from cryptography.fernet import Fernet

# Generate key
key = Fernet.generate_key()
print(f"Encryption Key: {key.decode()}")