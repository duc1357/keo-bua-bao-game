import socket
import threading
import tkinter as tk
from tkinter import messagebox
import time

HOST = '127.0.0.1'
PORT = 55556

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(120.0)
client.connect((HOST, PORT))

update_gui = threading.Event()

def receive():
    buffer = ""
    while not update_gui.is_set():
        try:
            data = client.recv(1024).decode('utf-8')
            if not data:
                root.after(0, show_error, "Mất kết nối với server!")
                break
            buffer += data
            print(f"[DEBUG] Buffer nhận: {repr(buffer)}")
            while '\n' in buffer:
                message, buffer = buffer.split('\n', 1)
                message = message.strip()
                if message:
                    print(f"[DEBUG] Nhận message: {message}")
                    root.after(0, update_status, message)
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[ERROR] Receive: {e}")
            root.after(0, show_error, "Mất kết nối với server!")
            break
    try:
        client.close()
    except:
        pass

def update_status(message):
    if message == "CONNECTED":
        status_label.config(text="Đã kết nối, chờ người chơi thứ 2...")
    elif message == "FULL":
        messagebox.showerror("Lỗi", "Phòng đã đầy!")
        root.destroy()
    elif message == "START":
        status_label.config(text="Game bắt đầu! Chọn Kéo, Búa hoặc Bao")
        enable_buttons()
    elif message == "NEW_GAME":
        status_label.config(text="Ván mới! Chọn Kéo, Búa hoặc Bao")
        enable_buttons()
    elif message in ["Bạn đã thắng!", "Bạn đã thua!", "Hòa!"]:
        status_label.config(text=message)
        messagebox.showinfo("Kết quả", message)
        disable_buttons()
    elif message == "Đã chọn, chờ đối thủ...":
        status_label.config(text=message)
    else:
        status_label.config(text=f"[DEBUG] {message}")

def show_error(message):
    messagebox.showerror("Lỗi", message)

def send_choice(choice):
    try:
        client.send((choice + '\n').encode('utf-8'))
        disable_buttons()
        status_label.config(text="Đã chọn, chờ đối thủ...")
        print(f"[DEBUG] Sent choice: {choice}")
    except Exception as e:
        messagebox.showerror("Lỗi", "Không thể gửi lựa chọn!")
        try:
            client.close()
        except:
            pass
        root.destroy()

def enable_buttons():
    keo_button.config(state='normal')
    bua_button.config(state='normal')
    bao_button.config(state='normal')

def disable_buttons():
    keo_button.config(state='disabled')
    bua_button.config(state='disabled')
    bao_button.config(state='disabled')

root = tk.Tk()
root.title("Kéo Búa Bao")
root.geometry("300x200")

status_label = tk.Label(root, text="Đang kết nối...", font=("Arial", 12))
status_label.pack(pady=20)

keo_button = tk.Button(root, text="Kéo", command=lambda: send_choice("keo"), state='disabled', width=10)
keo_button.pack(pady=5)

bua_button = tk.Button(root, text="Búa", command=lambda: send_choice("bua"), state='disabled', width=10)
bua_button.pack(pady=5)

bao_button = tk.Button(root, text="Bao", command=lambda: send_choice("bao"), state='disabled', width=10)
bao_button.pack(pady=5)

def on_closing():
    update_gui.set()
    try:
        client.close()
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
threading.Thread(target=receive, daemon=True).start()
root.mainloop()
