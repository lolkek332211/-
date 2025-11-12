import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import datetime
import time

class ModernMessenger:
    def __init__(self):
        self.host = self.get_local_ip()
        self.port = 8888
        self.clients = {}
        self.running = True
        self.current_chat = "general"  # Текущий активный чат
        
        print(f"🌐 Your IP: {self.host}")
        
        self.setup_gui()
        self.start_network()
    
    def get_local_ip(self):
        """Получаем локальный IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            try:
                return socket.gethostbyname(socket.gethostname())
            except:
                return "127.0.0.1"
    
    def start_network(self):
        """Запускаем сетевые компоненты"""
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            self.udp_socket.bind(('', self.port))
            self.add_message("🚀 Messenger started successfully", "system")
        except Exception as e:
            self.add_message(f"❌ Error: {e}", "error")
            return
        
        threading.Thread(target=self.receive_messages, daemon=True).start()
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.scan_network, daemon=True).start()
    
    def broadcast_presence(self):
        """Регулярная отправка broadcast сообщений"""
        while self.running:
            try:
                message = f"HELLO:{self.host}"
                self.udp_socket.sendto(message.encode('utf-8'), ('<broadcast>', self.port))
                time.sleep(3)
            except:
                time.sleep(5)
    
    def scan_network(self):
        """Активное сканирование сети"""
        base_ip = ".".join(self.host.split('.')[:-1]) + "."
        
        while self.running:
            try:
                for i in range(1, 255):
                    if not self.running:
                        break
                    target_ip = f"{base_ip}{i}"
                    if target_ip != self.host:
                        try:
                            message = f"PING:{self.host}"
                            self.udp_socket.sendto(message.encode('utf-8'), (target_ip, self.port))
                        except:
                            pass
                time.sleep(10)
            except:
                time.sleep(10)
    
    def receive_messages(self):
        """Прием сообщений"""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode('utf-8')
                self.handle_message(message, addr[0])
            except:
                pass
    
    def handle_message(self, message, ip):
        """Обработка входящих сообщений"""
        if message.startswith("HELLO:"):
            user_ip = message.split(":")[1]
            if user_ip != self.host and user_ip not in self.clients:
                self.clients[user_ip] = {"ip": ip, "status": "online", "last_seen": datetime.datetime.now()}
                self.update_users_list()
                self.add_message(f"👤 {user_ip} joined", "system")
                response = f"HELLO:{self.host}"
                self.udp_socket.sendto(response.encode('utf-8'), (ip, self.port))
        
        elif message.startswith("PING:"):
            user_ip = message.split(":")[1]
            if user_ip != self.host:
                response = f"HELLO:{self.host}"
                self.udp_socket.sendto(response.encode('utf-8'), (ip, self.port))
        
        elif message.startswith("MSG:"):
            parts = message.split(":", 2)
            if len(parts) == 3:
                sender, content = parts[1], parts[2]
                self.add_message(f"{content}", "received", sender)
        
        elif message.startswith("PRIVATE:"):
            parts = message.split(":", 3)
            if len(parts) == 4:
                sender, target, content = parts[1], parts[2], parts[3]
                if target == self.host:
                    self.add_message(f"{content}", "private", sender)
    
    def send_message(self, event=None):
        """Отправка сообщения"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        if self.current_chat == "general":
            # Отправляем всем пользователям
            for user_ip in self.clients:
                try:
                    msg = f"MSG:{self.host}:{message}"
                    self.udp_socket.sendto(msg.encode('utf-8'), (user_ip, self.port))
                except:
                    pass
            self.add_message(f"{message}", "sent")
        else:
            # Личное сообщение
            target_ip = self.current_chat
            try:
                msg = f"PRIVATE:{self.host}:{target_ip}:{message}"
                self.udp_socket.sendto(msg.encode('utf-8'), (target_ip, self.port))
                self.add_message(f"{message}", "sent_private")
            except Exception as e:
                self.add_message(f"❌ Send failed: {e}", "error")
        
        self.message_entry.delete(0, tk.END)
    
    def manual_connect(self):
        """Ручное подключение по IP"""
        ip = self.manual_ip_entry.get().strip()
        if not ip:
            return
        
        if ip == self.host:
            messagebox.showwarning("Warning", "Cannot connect to yourself")
            return
        
        if ip not in self.clients:
            self.clients[ip] = {"ip": ip, "status": "manual", "last_seen": datetime.datetime.now()}
            self.update_users_list()
            self.add_message(f"🔗 Manual connection: {ip}", "system")
            
            try:
                message = f"HELLO:{self.host}"
                self.udp_socket.sendto(message.encode('utf-8'), (ip, self.port))
            except:
                pass
        
        self.manual_ip_entry.delete(0, tk.END)
    
    def setup_gui(self):
        """Современный интерфейс"""
        self.root = tk.Tk()
        self.root.title(f"Modern Messenger - {self.host}")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Стиль для ttk
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#2c3e50')
        style.configure('TLabel', background='#2c3e50', foreground='white')
        style.configure('TButton', background='#3498db', foreground='white')
        style.configure('TEntry', fieldbackground='#ecf0f1')
        
        # Основной контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Левая панель - контакты
        left_panel = ttk.Frame(main_container, width=300)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Заголовок
        header_frame = ttk.Frame(left_panel)
        header_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(header_frame, text="Modern Messenger", 
                 font=('Arial', 16, 'bold'), foreground='#3498db').pack()
        ttk.Label(header_frame, text=f"IP: {self.host}", 
                 font=('Arial', 10), foreground='#bdc3c7').pack()
        
        # Поиск и добавление
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill='x', pady=(0, 10))
        
        self.manual_ip_entry = ttk.Entry(search_frame, font=('Arial', 10))
        self.manual_ip_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.manual_ip_entry.insert(0, "Enter IP...")
        
        ttk.Button(search_frame, text="+", width=3, 
                  command=self.manual_connect).pack(side='right')
        
        # Вкладки контактов
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill='both', expand=True)
        
        # Вкладка пользователей
        users_frame = ttk.Frame(notebook)
        notebook.add(users_frame, text="👥 Contacts")
        
        self.users_listbox = tk.Listbox(users_frame, bg='#34495e', fg='white', 
                                       font=('Arial', 11), selectbackground='#3498db',
                                       borderwidth=0, highlightthickness=0)
        self.users_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        # Общий чат
        general_chat_btn = ttk.Button(left_panel, text="💬 General Chat", 
                                     command=lambda: self.switch_chat("general"))
        general_chat_btn.pack(fill='x', pady=(5, 0))
        
        # Правая панель - чат
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Заголовок чата
        self.chat_header = ttk.Label(right_panel, text="💬 General Chat", 
                                   font=('Arial', 14, 'bold'), foreground='white')
        self.chat_header.pack(anchor='w', pady=(0, 10))
        
        # Область сообщений
        chat_container = ttk.Frame(right_panel)
        chat_container.pack(fill='both', expand=True)
        
        self.chat_text = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            state='disabled',
            bg='#ecf0f1',
            fg='#2c3e50',
            font=('Arial', 11),
            padx=15,
            pady=15,
            borderwidth=0,
            relief='flat'
        )
        self.chat_text.pack(fill='both', expand=True)
        
        # Панель ввода
        input_frame = ttk.Frame(right_panel)
        input_frame.pack(fill='x', pady=(10, 0))
        
        self.message_entry = ttk.Entry(input_frame, font=('Arial', 12))
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.message_entry.bind('<Return>', self.send_message)
        self.message_entry.focus()
        
        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side='right')
        
        # Статус бар
        self.status_var = tk.StringVar(value="🟢 Online - Ready to chat")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief='sunken', style='TLabel')
        status_bar.pack(side='bottom', fill='x')
        
        # Настройка тегов для текста
        self.setup_text_tags()
        
        # Запускаем обновление интерфейса
        self.root.after(1000, self.update_interface)
    
    def setup_text_tags(self):
        """Настройка стилей текста"""
        # Системные сообщения
        self.chat_text.tag_configure("system", foreground='#7f8c8d', font=('Arial', 10, 'italic'))
        self.chat_text.tag_configure("error", foreground='#e74c3c', font=('Arial', 10, 'bold'))
        
        # Сообщения
        self.chat_text.tag_configure("sent", foreground='#2c3e50', font=('Arial', 11))
        self.chat_text.tag_configure("received", foreground='#2c3e50', font=('Arial', 11))
        self.chat_text.tag_configure("private", foreground='#9b59b6', font=('Arial', 11))
        self.chat_text.tag_configure("sent_private", foreground='#8e44ad', font=('Arial', 11))
        
        # Временные метки
        self.chat_text.tag_configure("timestamp", foreground='#95a5a6', font=('Arial', 9))
        self.chat_text.tag_configure("username", foreground='#3498db', font=('Arial', 10, 'bold'))
    
    def on_user_select(self, event):
        """Выбор пользователя для личного чата"""
        selection = self.users_listbox.curselection()
        if selection:
            user_text = self.users_listbox.get(selection[0])
            user_ip = user_text.split(" ")[0]  # Извлекаем IP из текста
            self.switch_chat(user_ip)
    
    def switch_chat(self, chat_id):
        """Переключение между чатами"""
        self.current_chat = chat_id
        if chat_id == "general":
            self.chat_header.config(text="💬 General Chat")
            self.status_var.set("🟢 General Chat - Messages visible to everyone")
        else:
            self.chat_header.config(text=f"👤 Private chat with {chat_id}")
            self.status_var.set(f"🔒 Private chat with {chat_id}")
        
        # Очищаем и показываем историю чата
        self.clear_chat_display()
        # Здесь можно добавить загрузку истории чата
    
    def clear_chat_display(self):
        """Очистка отображения чата (для демо)"""
        self.chat_text.config(state='normal')
        self.chat_text.delete(1.0, tk.END)
        
        if self.current_chat == "general":
            self.add_message("Welcome to general chat! Everyone can see your messages here.", "system")
        else:
            self.add_message(f"Private chat with {self.current_chat}. Only you and them can see these messages.", "system")
        
        self.chat_text.config(state='disabled')
    
    def add_message(self, message, msg_type="received", sender=None):
        """Добавление сообщения в чат с современным форматированием"""
        self.chat_text.config(state='normal')
        
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Добавляем временную метку
        self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Добавляем имя отправителя если есть
        if sender and msg_type == "received":
            self.chat_text.insert(tk.END, f"{sender}: ", "username")
        elif msg_type == "sent":
            self.chat_text.insert(tk.END, "You: ", "username")
        elif msg_type == "private":
            self.chat_text.insert(tk.END, f"{sender} (private): ", "username")
        elif msg_type == "sent_private":
            self.chat_text.insert(tk.END, "You (private): ", "username")
        
        # Добавляем сообщение
        self.chat_text.insert(tk.END, f"{message}\n\n", msg_type)
        
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
    
    def update_users_list(self):
        """Обновление списка пользователей с иконками статуса"""
        self.users_listbox.delete(0, tk.END)
        
        # Добавляем общий чат в начало
        self.users_listbox.insert(tk.END, "🌐 General Chat")
        
        # Добавляем пользователей
        for user_ip, user_data in sorted(self.clients.items()):
            status_icon = "🟢" if user_data.get('status') == 'online' else "⚪"
            self.users_listbox.insert(tk.END, f"{status_icon} {user_ip}")
    
    def update_interface(self):
        """Периодическое обновление интерфейса"""
        self.update_users_list()
        
        # Обновляем статус онлайн/оффлайн
        current_time = datetime.datetime.now()
        for user_ip, user_data in self.clients.items():
            time_diff = (current_time - user_data['last_seen']).total_seconds()
            if time_diff > 30:  # 30 секунд без активности
                user_data['status'] = 'offline'
        
        self.root.after(5000, self.update_interface)
    
    def on_closing(self):
        """Действия при закрытии"""
        self.running = False
        try:
            self.udp_socket.close()
        except:
            pass
        self.root.destroy()
    
    def run(self):
        """Запуск приложения"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Центрируем окно
        self.root.eval('tk::PlaceWindow . center')
        
        self.root.mainloop()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Modern Network Messenger")
    print("=" * 50)
    print("Features:")
    print("• Modern dark theme interface")
    print("• General and private chats")
    print("• Automatic user discovery")
    print("• Real-time messaging")
    print("=" * 50)
    
    app = ModernMessenger()
    app.run()
