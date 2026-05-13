import socket
import threading
import sys
import os
from utils import send_encrypted, recv_encrypted

HOST = '127.0.0.1'
PORT = 5050

print("=== Server (Secure AES-CBC Chat) ===")
print("Waiting for a client to connect...")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)  # Only listen for 1 client in this 1-on-1 reconstructed version

client_sock, client_addr = server.accept()
print(f"[*] Client connected from {client_addr}\n")

shutting_down = False

def receive():
    """
    Background thread to continually receive encrypted messages from the client.
    """
    global shutting_down
    while not shutting_down:
        try:
            message = recv_encrypted(client_sock)
            if message is None:
                print("\n[!] Client has closed the connection.")
                shutting_down = True
                os._exit(0)
            print(f"\n[Client]: {message}")
            print("You: ", end="", flush=True)
            
        except Exception as e:
            if not shutting_down:
                print(f"\n[!] Error receiving message: {e}")
            shutting_down = True
            os._exit(1)

# Start background decryption/receive thread
receive_thread = threading.Thread(target=receive, daemon=True)
receive_thread.start()

# Main thread handles sending inputs
print("You can now start typing messages securely. Type 'quit' to exit.")
while not shutting_down:
    try:
        msg = input("You: ")
        if msg.lower() == 'quit':
            shutting_down = True
            client_sock.close()
            server.close()
            print("Server shutting down.")
            sys.exit(0)
            
        if msg.strip():
            send_encrypted(client_sock, msg)
            
    except (KeyboardInterrupt, EOFError):
        shutting_down = True
        client_sock.close()
        server.close()
        sys.exit(0)
    except Exception as e:
        if not shutting_down:
            print(f"Error sending message: {e}")
            shutting_down = True
        sys.exit(1)
