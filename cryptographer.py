from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import os

def encrypt_file_rust_style(input_file, output_file, password):
    """
    Современное шифрование в стиле Rust-библиотек
    """
    # Генерируем соль (как в Rust криптобиблиотеках)
    salt = get_random_bytes(16)
    
    # Создаем ключ с помощью PBKDF2 (аналог Rust's argon2)
    key = PBKDF2(password, salt, 32, count=1000000)
    
    # Генерируем nonce (как в Rust crypto)
    iv = get_random_bytes(16)
    
    # Шифрование в режиме GCM (современный, как в Rust)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    
    # Шифруем и получаем tag для аутентификации
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    os.remove(input_file)
    # Сохраняем в формате: salt + iv + tag + ciphertext
    with open(output_file, 'wb') as f:
        f.write(salt)
        f.write(iv)
        f.write(tag)
        f.write(ciphertext)
    
    print(f"Файл зашифрован в стиле Rust: {output_file}")

def decrypt_file_rust_style(input_file, output_file, password):
    """
    Расшифровка в стиле Rust
    """
    with open(input_file, 'rb') as f:
        salt = f.read(16)
        iv = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()
    
    key = PBKDF2(password, salt, 32, count=1000000)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    
    try:
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        with open(output_file, 'wb') as f:
            f.write(plaintext)
        print(f"Файл расшифрован: {output_file}")
        return True
    except ValueError:
        print("Ошибка аутентификации!")
        return False
