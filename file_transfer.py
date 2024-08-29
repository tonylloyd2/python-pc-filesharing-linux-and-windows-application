import socket
import os
import threading
from tkinter import Tk, Label, Button, Entry, StringVar, filedialog, messagebox, Radiobutton, IntVar

BROADCAST_PORT = 5000
FILE_TRANSFER_PORT = 5001

# GUI must be initialized after the root window is created
def run_gui():
    root = Tk()
    root.title("File Transfer Application")
    root.geometry("400x300")

    # Now we can initialize the StringVars and other tkinter variables
    global file_path_var, status_var
    file_path_var = StringVar()
    status_var = StringVar()
    
    def start_role():
        choice = role_choice.get()
        if choice == 1:  # Start Server
            start_server()
        elif choice == 2:  # Start Client
            if file_path_var.get():
                send_file()
            else:
                messagebox.showwarning("File Required", "Please select a file to send.")
    
    # Role Selection
    Label(root, text="Choose your role:").pack(pady=10)
    role_choice = IntVar()
    Radiobutton(root, text="Receiver (Server)", variable=role_choice, value=1).pack()
    Radiobutton(root, text="Sender (Client)", variable=role_choice, value=2).pack()

    # File Selection (Only visible when acting as client)
    Label(root, text="File to Send (Client Only):").pack(pady=5)
    Entry(root, textvariable=file_path_var, width=30).pack(pady=5)
    Button(root, text="Browse", command=browse_file).pack(pady=5)

    # Start Button
    Button(root, text="Start", command=start_role).pack(pady=20)

    # Status Display
    Label(root, textvariable=status_var).pack(pady=10)
    status_var.set("Ready to transfer files")

    root.mainloop()

### Server and Client Functions
def broadcast_ip():
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_message = "FILE_SERVER"
    while True:
        broadcast_socket.sendto(broadcast_message.encode('utf-8'), ('<broadcast>', BROADCAST_PORT))

def start_server():
    threading.Thread(target=broadcast_ip, daemon=True).start()  # Start broadcasting the server's IP address
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', FILE_TRANSFER_PORT))
    server_socket.listen(1)
    
    status_var.set(f"Server listening on port {FILE_TRANSFER_PORT}...")
    
    client_socket, addr = server_socket.accept()
    status_var.set(f"Connection from {addr} established.")
    
    # Perform handshake
    client_socket.send("READY".encode('utf-8'))
    client_ready = client_socket.recv(1024).decode('utf-8')
    
    if client_ready == "READY":
        # Receive file details
        file_name = client_socket.recv(1024).decode('utf-8')
        file_size = int(client_socket.recv(1024).decode('utf-8'))
        
        with open(file_name, 'wb') as file:
            bytes_received = 0
            while bytes_received < file_size:
                data = client_socket.recv(1024)
                if not data:
                    break
                file.write(data)
                bytes_received += len(data)
        
        status_var.set(f"Received file: {file_name}")
        messagebox.showinfo("Success", f"File '{file_name}' received successfully!")
    else:
        status_var.set("Handshake failed. No file transferred.")
    
    client_socket.close()
    server_socket.close()

def discover_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.bind(('', BROADCAST_PORT))
    
    status_var.set("Searching for server...")
    while True:
        data, server_address = client_socket.recvfrom(1024)
        if data.decode('utf-8') == "FILE_SERVER":
            status_var.set(f"Server found at {server_address[0]}")
            return server_address[0]

def send_file():
    server_ip = discover_server()
    
    if not server_ip:
        messagebox.showerror("Error", "Server not found.")
        return
    
    file_path = file_path_var.get()

    if not file_path:
        messagebox.showerror("Error", "Please select a file to send.")
        return
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, FILE_TRANSFER_PORT))
        
        # Perform handshake
        client_ready = client_socket.recv(1024).decode('utf-8')
        if client_ready == "READY":
            client_socket.send("READY".encode('utf-8'))
            
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Send file details
            client_socket.send(file_name.encode('utf-8'))
            client_socket.send(str(file_size).encode('utf-8'))
            
            with open(file_path, 'rb') as file:
                while True:
                    bytes_read = file.read(1024)
                    if not bytes_read:
                        break
                    client_socket.sendall(bytes_read)
            
            status_var.set(f"Sent file: {file_name}")
            messagebox.showinfo("Success", f"File '{file_name}' sent successfully!")
        else:
            status_var.set("Handshake failed. No file sent.")
        
        client_socket.close()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def browse_file():
    file_path = filedialog.askopenfilename()
    file_path_var.set(file_path)

if __name__ == "__main__":
    run_gui()
