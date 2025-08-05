import socket
import threading
import time

# Khởi tạo server
HOST = '127.0.0.1'
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)  # Chỉ chấp nhận tối đa 2 kết nối

clients = []
choices = {}
lock = threading.Lock()

# Hàm gửi tin nhắn tới tất cả client với retry
def broadcast(message, max_retries=5):
    with lock:
        for i, client in enumerate(clients[:]):
            retries = 0
            while retries < max_retries:
                try:
                    client.settimeout(1.0)  # Đặt timeout để tránh treo
                    client.send(message.encode('utf-8'))
                    print(f"Sent to client {i}: {message} at {time.strftime('%H:%M:%S')}")
                    break
                except Exception as e:
                    retries += 1
                    print(f"Failed to send to client {i} (Attempt {retries}/{max_retries}): {e} at {time.strftime('%H:%M:%S')}")
                    if retries == max_retries:
                        remove_client(client)
                    time.sleep(0.2)  # Tăng thời gian chờ giữa các lần thử

# Hàm xóa client khi ngắt kết nối
def remove_client(client):
    with lock:
        if client in clients:
            index = clients.index(client)
            clients.remove(client)
            if index in choices:
                del choices[index]
            client.close()
            print(f"Client {index} removed at {time.strftime('%H:%M:%S')}")

# Hàm xác định người thắng
def determine_winner():
    with lock:
        print(f"Checking choices: {choices} at {time.strftime('%H:%M:%S')}")
        if len(choices) != 2:
            print(f"Error: Only {len(choices)} choices received at {time.strftime('%H:%M:%S')}")
            return
        choice1 = choices.get(0)
        choice2 = choices.get(1)
        
        if not choice1 or not choice2:
            print(f"Error: Missing choice at {time.strftime('%H:%M:%S')}")
            return
            
        result = ""
        if choice1 == choice2:
            result = "Hòa!"
        elif (choice1 == "keo" and choice2 == "bao") or \
             (choice1 == "bao" and choice2 == "bua") or \
             (choice1 == "bua" and choice2 == "keo"):
            result = "Người chơi 1 thắng!"
        else:
            result = "Người chơi 2 thắng!"
        
        broadcast(result)
        print(f"Winner determined: {result} at {time.strftime('%H:%M:%S')}")
        time.sleep(0.2)  # Đợi để đảm bảo gửi xong

# Hàm xử lý từng client
def handle_client(client):
    while True:
        try:
            client.settimeout(10.0)  # Đặt timeout cho recv
            choice = client.recv(1024).decode('utf-8')
            if not choice:
                break
                
            with lock:
                client_id = clients.index(client)
                choices[client_id] = choice
                print(f"Client {client_id} chose: {choice} at {time.strftime('%H:%M:%S')}")
            
            with lock:
                if len(choices) == 2:
                    print(f"Two choices received: {choices} at {time.strftime('%H:%M:%S')}")
                    determine_winner()
                    broadcast("NEW_GAME")
                    choices.clear()
                    print(f"Game reset at {time.strftime('%H:%M:%S')}")
                    
        except socket.timeout:
            print(f"Timeout for client {clients.index(client)} at {time.strftime('%H:%M:%S')}")
            remove_client(client)
            break
        except Exception as e:
            print(f"Error in handle_client: {e} at {time.strftime('%H:%M:%S')}")
            remove_client(client)
            break

# Hàm chính của server
def main():
    print(f"Server đang chạy trên {HOST}:{PORT} at {time.strftime('%H:%M:%S')}")
    
    while True:
        try:
            client, address = server.accept()
            print(f"Kết nối mới từ {address} at {time.strftime('%H:%M:%S')}")
            
            with lock:
                if len(clients) < 2:
                    clients.append(client)
                    client.send("CONNECTED".encode('utf-8'))
                    
                    if len(clients) == 2:
                        for i, c in enumerate(clients):
                            c.send("START".encode('utf-8'))
                            print(f"Sent START to client {i} at {time.strftime('%H:%M:%S')}")
                else:
                    client.send("FULL".encode('utf-8'))
                    client.close()
        except Exception as e:
            print(f"Lỗi khi chấp nhận kết nối: {e} at {time.strftime('%H:%M:%S')}")
            break

if __name__ == "__main__":
    main()