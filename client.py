import socket
import threading
import tkinter as tk
from tkinter import messagebox
import time

# Khởi tạo client
HOST = '127.0.0.1'
PORT = 55555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(10.0)  # Đặt timeout 10 giây
client.connect((HOST, PORT))

# Biến để đồng bộ hóa với GUI
update_gui = threading.Event()

# Hàm nhận tin nhắn từ server (an toàn với GUI)
def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"Received: {message} at {time.strftime('%H:%M:%S')}")  # Debug
            # Sử dụng root.after để cập nhật GUI từ thread khác
            root.after(0, update_status, message)
        except socket.timeout:
            print(f"Timeout waiting for message at {time.strftime('%H:%M:%S')}")
            continue  # Tiếp tục thử đọc
        except Exception as e:
            print(f"Error in receive: {e} at {time.strftime('%H:%M:%S')}")
            root.after(0, show_error, "Mất kết nối với server!")
            client.close()
            root.after(0, root.destroy)
            break

# Hàm cập nhật trạng thái GUI
def update_status(message):
    if "START" in message:
        status_label.config(text="Game bắt đầu! Chọn Kéo, Búa hoặc Bao")
        enable_buttons()
    elif message == "CONNECTED":
        status_label.config(text="Đã kết nối, chờ người chơi thứ 2...")
    elif message == "FULL":
        messagebox.showerror("Lỗi", "Phòng đã đầy!")
        root.destroy()
    elif message == "NEW_GAME":
        status_label.config(text="Ván mới! Chọn Kéo, Búa hoặc Bao")
        enable_buttons()
    elif message in ["Người chơi 1 thắng!", "Người chơi 2 thắng!", "Hòa!"]:
        status_label.config(text=message)
        disable_buttons()
    else:
        status_label.config(text=message)
        disable_buttons()

# Hàm hiển thị lỗi
def show_error(message):
    messagebox.showerror("Lỗi", message)

# Hàm gửi lựa chọn
def send_choice(choice):
    try:
        client.send(choice.encode('utf-8'))
        disable_buttons()
        status_label.config(text="Đã chọn, chờ đối thủ...")
        print(f"Sent choice: {choice} at {time.strftime('%H:%M:%S')}")  # Debug
    except Exception as e:
        print(f"Error sending choice: {e} at {time.strftime('%H:%M:%S')}")
        messagebox.showerror("Lỗi", "Không thể gửi lựa chọn!")
        client.close()
        root.destroy()

# Hàm kích hoạt các nút
def enable_buttons():
    keo_button.config(state='normal')
    bua_button.config(state='normal')
    bao_button.config(state='normal')

# Hàm vô hiệu hóa các nút
def disable_buttons():
    keo_button.config(state='disabled')
    bua_button.config(state='disabled')
    bao_button.config(state='disabled')

# Giao diện GUI
root = tk.Tk()
root.title("Kéo Búa Bao")
root.geometry("300x200")

# Nhãn trạng thái
status_label = tk.Label(root, text="Đang kết nối...")
status_label.pack(pady=20)

# Nút chọn Kéo
keo_button = tk.Button(root, text="Kéo", command=lambda: send_choice("keo"), state='disabled')
keo_button.pack(pady=5)

# Nút chọn Búa
bua_button = tk.Button(root, text="Búa", command=lambda: send_choice("bua"), state='disabled')
bua_button.pack(pady=5)

# Nút chọn Bao
bao_button = tk.Button(root, text="Bao", command=lambda: send_choice("bao"), state='disabled')
bao_button.pack(pady=5)

# Đảm bảo đóng kết nối khi thoát
def on_closing():
    try:
        client.close()
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Bắt đầu thread nhận tin nhắn
receive_thread = threading.Thread(target=receive, daemon=True)
receive_thread.start()

# Chạy giao diện
root.mainloop()