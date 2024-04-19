import hashlib

def hash_password(password):
    # Convert the password to bytes
    password_bytes = password.encode('utf-8')

    # Create a SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Update the hash object with the password bytes
    sha256_hash.update(password_bytes)

    # Get the hashed password as a hexadecimal string
    hashed_password = sha256_hash.hexdigest()

    return hashed_password