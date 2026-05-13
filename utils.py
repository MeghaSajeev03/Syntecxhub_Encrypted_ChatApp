import os
import struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

KEY_FILE = 'shared.key'

def load_or_generate_key() -> bytes:
    """
    Loads the AES key or generates a new 256-bit one.
    """
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = os.urandom(32)  # AES-256
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        print(f"[*] Generated new AES-256 key and saved to {KEY_FILE}")
        return key

SHARED_KEY = load_or_generate_key()

def encrypt_message(message: str) -> bytes:
    """
    Encrypts a string message using AES in CBC mode with PKCS7 padding.
    """
    cipher = AES.new(SHARED_KEY, AES.MODE_CBC)
    # The IV is generated automatically by AES.new when using MODE_CBC
    padded_data = pad(message.encode('utf-8'), AES.block_size)
    ciphertext = cipher.encrypt(padded_data)
    
    # Prepend the IV so the receiver can initialize the decryption cipher
    return cipher.iv + ciphertext

def decrypt_message(encrypted_data: bytes) -> str:
    """
    Decrypts the message and unpads it.
    """
    iv = encrypted_data[:AES.block_size]
    ciphertext = encrypted_data[AES.block_size:]
    
    cipher = AES.new(SHARED_KEY, AES.MODE_CBC, iv)
    decrypted_padded_data = cipher.decrypt(ciphertext)
    
    decrypted_data = unpad(decrypted_padded_data, AES.block_size)
    return decrypted_data.decode('utf-8')

# ----------------- SOCKET UTILITIES -----------------

def send_encrypted(sock, message_str: str):
    """
    Encrypts a string and sends it over the socket with a 4-byte length prefix.
    """
    encrypted_bytes = encrypt_message(message_str)
    print(f"\n[+] Encrypting '{(message_str[:20] + '...') if len(message_str) > 20 else message_str}'")
    print(f"[+] Ciphertext to send: {encrypted_bytes}")
    msg_length = struct.pack('!I', len(encrypted_bytes))
    sock.sendall(msg_length + encrypted_bytes)

def recv_encrypted(sock) -> str:
    """
    Reads a length-prefixed message from the socket and decrypts it.
    Returns None if connection closes.
    """
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
        
    msglen = struct.unpack('!I', raw_msglen)[0]
    
    encrypted_bytes = recvall(sock, msglen)
    if not encrypted_bytes:
        return None
    
    print(f"\n[+] Received ciphertext: {encrypted_bytes}")
    print("[+] Decrypting message...")    
    return decrypt_message(encrypted_bytes)

def recvall(sock, n):
    """
    Helper to recv precisely n bytes from a TCP socket.
    """
    data = bytearray()
    while len(data) < n:
        try:
            packet = sock.recv(n - len(data))
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            return None
            
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)
