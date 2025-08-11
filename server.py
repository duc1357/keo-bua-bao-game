import socket
import threading
import time

HOST = '127.0.0.1'
PORT = 55556

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)

clients = {}       # {client_socket: id}
choices = {}       # {id: choice}
lock = threading.Lock()

def remove_client(client):
    with lock:
        if client in clients:
            cid = clients[client]
            print(f"[REMOVE] Removing client {cid}")
            del clients[client]
            if cid in choices:
                del choices[cid]
    try:
        client.shutdown(socket.SHUT_RDWR)
    except:
        pass
    client.close()

def determine_winner():
    with lock:
        print(f"[DEBUG] Checking choices: {choices}")
        if len(choices) != 2:
            print("[DEBUG] Not enough choices to determine winner.")
            return
        choice1 = choices.get(0)
        choice2 = choices.get(1)

    if not choice1 or not choice2:
        print("[DEBUG] Missing choice.")
        return

    if choice1 == choice2:
        # Hòa -> gửi cho cả 2
        for c in clients:
            c.send("Hòa!\n".encode('utf-8'))
    elif (choice1 == "keo" and choice2 == "bao") or \
         (choice1 == "bao" and choice2 == "bua") or \
         (choice1 == "bua" and choice2 == "keo"):
        # Client 0 thắng
        for c, cid in clients.items():
            if cid == 0:
                c.send("Bạn đã thắng!\n".encode('utf-8'))
            else:
                c.send("Bạn đã thua!\n".encode('utf-8'))
    else:
        # Client 1 thắng
        for c, cid in clients.items():
            if cid == 1:
                c.send("Bạn đã thắng!\n".encode('utf-8'))
            else:
                c.send("Bạn đã thua!\n".encode('utf-8'))

    time.sleep(2)
    for c in clients:
        c.send("NEW_GAME\n".encode('utf-8'))

    with lock:
        choices.clear()
    print("[DEBUG] Game reset.")

def handle_client(client):
    buffer = ""
    cid = clients[client]
    while True:
        try:
            data = client.recv(1024).decode('utf-8')
            if not data:
                print(f"[DISCONNECT] Client {cid} disconnected.")
                remove_client(client)
                break

            buffer += data
            while '\n' in buffer:
                message, buffer = buffer.split('\n', 1)
                message = message.strip()
                if not message:
                    continue
                with lock:
                    choices[cid] = message
                print(f"[CHOICE] Client {cid} chose: {message}")

                trigger = False
                with lock:
                    if len(choices) == 2:
                        trigger = True
                if trigger:
                    determine_winner()

        except Exception as e:
            print(f"[ERROR] Client {cid}: {e}")
            remove_client(client)
            break

def main():
    print(f"[SERVER] Running on {HOST}:{PORT}")
    next_id = 0
    while True:
        client, addr = server.accept()
        print(f"[CONNECT] New connection from {addr}")
        with lock:
            if len(clients) < 2:
                clients[client] = next_id
                client.send("CONNECTED\n".encode('utf-8'))
                next_id += 1
                if len(clients) == 2:
                    for c in clients:
                        c.send("START\n".encode('utf-8'))
                    for c in clients:
                        threading.Thread(target=handle_client, args=(c,), daemon=True).start()
            else:
                client.send("FULL\n".encode('utf-8'))
                client.close()

if __name__ == "__main__":
    main()
