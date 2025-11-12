import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import socket
import threading
import json
import time
from datetime import datetime
import subprocess
import platform

class LocalMessenger:
    def __init__(self):
        self.host = self.get_local_ip()
        self.port = 8888
        self.username = f"User_{self.host}"
        
        # Хранилище данных
        self.users = {}
        self.chats = {}
        self.current_chat = None
        self.server_socket = None
        self.running = True
        
        # GUI
        self.root = tk.Tk()
        self.setup_gui()
        
    def get_local_ip(self):
        """Получаем локальный IP адрес"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def scan_network(self):
        """Сканируем сеть для поиска других пользователей"""
        base_ip = '.'.join(self.host.split('.')[:-1])
        
        def ping_ip(ip):
            """Пинг конкретного IP"""
            try:
                if platform.system().lower() == "windows":
                    param = "-n"
                else:
                    param = "-c"
                
                result = subprocess.run(
                    ["ping", param, "1", "-w", "1000", ip],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except:
                return False
        
        def check_messenger(ip):
            """Проверяем запущен ли мессенджер на IP"""
            if ip == self.host:
                return False
                
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, self.port))
                sock.close()
                return result == 0
            except:
                return False
        
        # Сканируем диапазон IP
        threads = []
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            thread = threading.Thread(target=self.check_and_add_user, args=(ip,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
            # Небольшая задержка чтобы не перегружать сеть
            if i % 10 == 0:
                time.sleep(0.1)
    
    def check_and_add_user(self, ip):
        """Проверяем и добавляем пользователя"""
        if ip == self.host:
            return
            
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, self.port))
            sock.close()
            
            if result == 0:
                self.add_user(ip)
        except:
            pass
    
    def setup_gui(self):
        """Настройка графического интерфейса"""
        self.root.title(f"Local Messenger - {self.host}")
        self.root.geometry("1000x700")
        
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель с информацией
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text=f"Your IP: {self.host}", 
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(top_frame, text="Scan Network", 
                  command=self.scan_network).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(top_frame, text="Add User", 
                  command=self.add_user_manual).pack(side=tk.RIGHT)
        
        # Основной контент
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - пользователи и чаты
        left_frame = ttk.Frame(content_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Пользователи
        users_label = ttk.Label(left_frame, text="Online Users", font=('Arial', 11, 'bold'))
        users_label.pack(anchor='w', pady=(0, 5))
        
        self.users_listbox = tk.Listbox(left_frame, font=('Arial', 10))
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        # Группы
        groups_label = ttk.Label(left_frame, text="Group Chats", font=('Arial', 11, 'bold'))
        groups_label.pack(anchor='w', pady=(10, 5))
        
        self.groups_listbox = tk.Listbox(left_frame, font=('Arial', 10))
        self.groups_listbox.pack(fill=tk.BOTH, expand=True)
        self.groups_listbox.bind('<<ListboxSelect>>', self.on_group_select)
        
        ttk.Button(left_frame, text="Create Group", 
                  command=self.create_group).pack(fill=tk.X, pady=(5, 0))
        
        # Правая панель - чат
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок чата
        self.chat_header = ttk.Label(right_frame, text="Select a chat to start messaging", 
                                   font=('Arial', 12, 'bold'))
        self.chat_header.pack(anchor='w', pady=(0, 10))
        
        # Область сообщений
        self.messages_text = scrolledtext.ScrolledText(
            right_frame, 
            font=('Arial', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Панель ввода
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X)
        
        self.message_entry = ttk.Entry(input_frame, font=('Arial', 12))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_button = ttk.Button(input_frame, text="Send", 
                                     command=self.send_message, state=tk.DISABLED)
        self.send_button.pack(side=tk.RIGHT)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Ready to use")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, padding=2)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Настройка тегов для текста
        self.setup_text_tags()
    
    def setup_text_tags(self):
        """Настройка форматирования текста"""
        self.messages_text.tag_configure("own", foreground="blue", font=('Arial', 10, 'bold'))
        self.messages_text.tag_configure("other", foreground="green", font=('Arial', 10, 'bold'))
        self.messages_text.tag_configure("time", foreground="gray", font=('Arial', 8))
        self.messages_text.tag_configure("system", foreground="orange", font=('Arial', 9))
    
    def add_user_manual(self):
        """Ручное добавление пользователя"""
        ip = simpledialog.askstring("Add User", "Enter IP address:")
        if ip and self.validate_ip(ip):
            self.check_and_add_user(ip)
        else:
            messagebox.showerror("Error", "Invalid IP address")
    
    def validate_ip(self, ip):
        """Проверка IP адреса"""
        try:
            socket.inet_aton(ip)
            return True
        except:
            return False
    
    def add_user(self, ip):
        """Добавление пользователя в список"""
        if ip not in self.users and ip != self.host:
            self.users[ip] = {"status": "online", "last_seen": datetime.now()}
            self.update_users_list()
            self.update_status(f"User {ip} added")
    
    def update_users_list(self):
        """Обновление списка пользователей"""
        self.users_listbox.delete(0, tk.END)
        for ip in sorted(self.users.keys()):
            self.users_listbox.insert(tk.END, f"🟢 {ip}")
    
    def update_status(self, message):
        """Обновление статуса"""
        def update():
            self.status_var.set(message)
            print(f"Status: {message}")
        self.root.after(0, update)
    
    def on_user_select(self, event):
        """Выбор пользователя для чата"""
        selection = self.users_listbox.curselection()
        if selection:
            ip = self.users_listbox.get(selection[0]).replace("🟢 ", "")
            self.open_private_chat(ip)
    
    def on_group_select(self, event):
        """Выбор группового чата"""
        selection = self.groups_listbox.curselection()
        if selection:
            group_name = self.groups_listbox.get(selection[0])
            self.open_group_chat(group_name)
    
    def open_private_chat(self, ip):
        """Открытие приватного чата"""
        self.current_chat = f"private_{ip}"
        self.chat_header.config(text=f"Chat with {ip}")
        self.send_button.config(state=tk.NORMAL)
        self.message_entry.config(state=tk.NORMAL)
        self.message_entry.focus()
        self.clear_chat()
        self.load_chat_history(f"private_{ip}")
        self.update_status(f"Chat with {ip}")
    
    def open_group_chat(self, group_name):
        """Открытие группового чата"""
        self.current_chat = f"group_{group_name}"
        self.chat_header.config(text=f"Group: {group_name}")
        self.send_button.config(state=tk.NORMAL)
        self.message_entry.config(state=tk.NORMAL)
        self.message_entry.focus()
        self.clear_chat()
        self.load_chat_history(f"group_{group_name}")
    
    def create_group(self):
        """Создание новой группы"""
        name = simpledialog.askstring("Create Group", "Enter group name:")
        if name:
            group_id = f"group_{name}"
            if group_id not in self.chats:
                self.chats[group_id] = []
                self.groups_listbox.insert(tk.END, name)
                self.update_status(f"Group '{name}' created")
    
    def clear_chat(self):
        """Очистка чата"""
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.config(state=tk.DISABLED)
    
    def load_chat_history(self, chat_id):
        """Загрузка истории чата"""
        if chat_id in self.chats:
            for msg in self.chats[chat_id]:
                self.display_message(
                    msg['sender'],
                    msg['content'],
                    msg['timestamp'],
                    msg['sender'] == self.host
                )
    
    def display_message(self, sender, content, timestamp, is_own):
        """Отображение сообщения"""
        self.messages_text.config(state=tk.NORMAL)
        
        try:
            time_obj = datetime.fromisoformat(timestamp)
            time_str = time_obj.strftime("%H:%M:%S")
        except:
            time_str = timestamp
        
        tag = "own" if is_own else "other"
        prefix = "You" if is_own else sender
        
        self.messages_text.insert(tk.END, f"[{time_str}] ", "time")
        self.messages_text.insert(tk.END, f"{prefix}: ", tag)
        self.messages_text.insert(tk.END, f"{content}\n")
        
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)
    
    def send_message(self, event=None):
        """Отправка сообщения"""
        text = self.message_entry.get().strip()
        if not text or not self.current_chat:
            return
        
        timestamp = datetime.now().isoformat()
        
        # Сохраняем локально
        if self.current_chat not in self.chats:
            self.chats[self.current_chat] = []
        
        self.chats[self.current_chat].append({
            'sender': self.host,
            'content': text,
            'timestamp': timestamp,
            'type': 'text'
        })
        
        # Показываем сообщение
        self.display_message(self.host, text, timestamp, True)
        
        # Отправляем по сети
        message = {
            'type': 'message',
            'chat_id': self.current_chat,
            'sender': self.host,
            'content': text,
            'timestamp': timestamp
        }
        
        if self.current_chat.startswith('private_'):
            target_ip = self.current_chat.replace('private_', '')
            threading.Thread(target=self.send_to_user, args=(target_ip, message), daemon=True).start()
        else:
            # Отправляем всем пользователям в группе
            for ip in self.users:
                threading.Thread(target=self.send_to_user, args=(ip, message), daemon=True).start()
        
        self.message_entry.delete(0, tk.END)
    
    def send_to_user(self, ip, message):
        """Отправка сообщения пользователю"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, self.port))
            sock.send(json.dumps(message).encode('utf-8'))
            sock.close()
            self.update_status(f"Message sent to {ip}")
        except Exception as e:
            self.update_status(f"Failed to send to {ip}: {str(e)}")
    
    def start_server(self):
        """Запуск сервера для приема сообщений"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(10)
            self.server_socket.settimeout(1)
            
            self.update_status(f"Server started on port {self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except:
                    if not self.running:
                        break
                    
        except Exception as e:
            self.update_status(f"Server error: {e}")
    
    def handle_client(self, client_socket, addr):
        """Обработка входящих соединений"""
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if data:
                message = json.loads(data)
                self.process_message(message, addr[0])
        except Exception as e:
            self.update_status(f"Client error: {e}")
        finally:
            client_socket.close()
    
    def process_message(self, message, sender_ip):
        """Обработка входящих сообщений"""
        if message.get('type') == 'message':
            # Автоматически добавляем отправителя
            if sender_ip not in self.users:
                self.add_user(sender_ip)
            
            chat_id = message.get('chat_id')
            content = message.get('content')
            timestamp = message.get('timestamp')
            sender = message.get('sender', sender_ip)
            
            if chat_id not in self.chats:
                self.chats[chat_id] = []
            
            self.chats[chat_id].append({
                'sender': sender,
                'content': content,
                'timestamp': timestamp,
                'type': 'text'
            })
            
            # Показываем сообщение если этот чат открыт
            if self.current_chat == chat_id:
                self.display_message(sender, content, timestamp, False)
            else:
                self.update_status(f"New message from {sender}")
    
    def start_network(self):
        """Запуск сетевых служб"""
        server_thread = threading.Thread(target=self.start_server, daemon=True)
        server_thread.start()
        
        # Автоматическое сканирование сети при запуске
        self.root.after(2000, self.scan_network)
        
        # Периодическое сканирование
        self.root.after(30000, self.periodic_scan)
    
    def periodic_scan(self):
        """Периодическое сканирование сети"""
        if self.running:
            self.scan_network()
            self.root.after(30000, self.periodic_scan)  # Каждые 30 секунд
    
    def run(self):
        """Запуск приложения"""
        self.start_network()
        
        try:
            self.root.mainloop()
        finally:
            self.running = False
            if self.server_socket:
                self.server_socket.close()

def main():
    """Главная функция"""
    print("=" * 50)
    print("🚀 Local Network Messenger")
    print("=" * 50)
    print("Features:")
    print("• Automatic network discovery")
    print("• Private and group chats") 
    print("• No registration required")
    print("• Works in local network")
    print("=" * 50)
    
    app = LocalMessenger()
    app.run()

if __name__ == "__main__":
    main()
