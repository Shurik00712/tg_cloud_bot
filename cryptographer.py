from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import os
import hashlib

def encrypt_file(input_file, output_file, password):
    
    salt = get_random_bytes(16)
    
    password = bytes(str(password).encode())
    password = hashlib.sha512(password).digest()
    
    key = PBKDF2(password, salt, 32, count=1000000)
    
    iv = get_random_bytes(16)
    
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    os.remove(input_file)
    with open(output_file, 'wb') as f:
        f.write(salt)
        f.write(iv)
        f.write(tag)
        f.write(ciphertext)
    
def decrypt_file(input_file, output_file, password):
    with open(input_file, 'rb') as f:
        salt = f.read(16)
        iv = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()
    password = bytes(str(password).encode())
    password = hashlib.sha512(password).digest()

    key = PBKDF2(password, salt, 32, count=1000000)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    
    try:
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        with open(output_file, 'wb') as f:
            f.write(plaintext)
        return True
    except ValueError:
        return False
