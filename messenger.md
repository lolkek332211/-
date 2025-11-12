import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import socket
import threading
import json
import time
from datetime import datetime
from typing import Dict, List, Set
import uuid

class LocalMessenger:
    def __init__(self):
        self.host = self.get_local_ip()
        self.port = 8888
        self.username = f"User_{self.host}"
        
        # Хранилище данных
        self.users: Set[str] = set()
        self.chats: Dict[str, List[Dict]] = {}
        self.current_chat = None
        self.socket = None
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
    
    def setup_gui(self):
        """Настройка графического интерфейса"""
        self.root.title(f"Python Мессенджер - {self.host}")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Создаем стиль
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настраиваем цвета
        style.configure('TFrame', background='#2c3e50')
        style.configure('TLabel', background='#2c3e50', foreground='white')
        style.configure('TButton', background='#3498db', foreground='white')
        style.configure('TEntry', fieldbackground='#ecf0f1')
        style.configure('TListbox', background='#34495e', foreground='white')
        
        # Основной фрейм
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - пользователи и чаты
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Информация о пользователе
        info_frame = ttk.Frame(left_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="Ваш IP:", font=('Arial', 10, 'bold')).pack(anchor='w')
        ttk.Label(info_frame, text=self.host, font=('Arial', 12, 'bold'), 
                 foreground='#3498db').pack(anchor='w')
        
        # Вкладки
        notebook = ttk.Notebook(left_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка пользователей
        users_frame = ttk.Frame(notebook)
        notebook.add(users_frame, text="👤 Пользователи")
        
        self.users_listbox = tk.Listbox(users_frame, bg='#34495e', fg='white', 
                                       font=('Arial', 10), selectbackground='#3498db')
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        # Вкладка групповых чатов
        groups_frame = ttk.Frame(notebook)
        notebook.add(groups_frame, text="👥 Группы")
        
        self.groups_listbox = tk.Listbox(groups_frame, bg='#34495e', fg='white',
                                        font=('Arial', 10), selectbackground='#27ae60')
        self.groups_listbox.pack(fill=tk.BOTH, expand=True)
        self.groups_listbox.bind('<<ListboxSelect>>', self.on_group_select)
        
        # Кнопка создания группы
        ttk.Button(groups_frame, text="Создать группу", 
                  command=self.create_group).pack(fill=tk.X, pady=5)
        
        # Правая панель - чат
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок чата
        self.chat_header = ttk.Label(right_frame, text="Выберите чат", 
                                   font=('Arial', 12, 'bold'), foreground='white')
        self.chat_header.pack(anchor='w', pady=(0, 10))
        
        # Область сообщений
        self.messages_text = scrolledtext.ScrolledText(
            right_frame, 
            bg='#ecf0f1', 
            fg='#2c3e50', 
            font=('Arial', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Панель ввода сообщения
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X)
        
        self.message_entry = ttk.Entry(input_frame, font=('Arial', 12))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_button = ttk.Button(input_frame, text="Отправить", 
                                     command=self.send_message, state=tk.DISABLED)
        self.send_button.pack(side=tk.RIGHT)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, style='TLabel')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def start_network(self):
        """Запуск сетевых функций"""
        # Запускаем сервер в отдельном потоке
        server_thread = threading.Thread(target=self.start_server, daemon=True)
        server_thread.start()
        
        # Запускаем широковещательное оповещение
        broadcast_thread = threading.Thread(target=self.broadcast_presence, daemon=True)
        broadcast_thread.start()
        
        # Сканируем сеть на наличие других пользователей
        self.scan_network()
    
    def start_server(self):
        """Запуск TCP сервера для приема сообщений"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            self.update_status(f"Сервер запущен на {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                except:
                    break
                    
        except Exception as e:
            self.update_status(f"Ошибка сервера: {e}")
    
    def handle_client(self, client_socket, addr):
        """Обработка входящих соединений"""
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if data:
                message = json.loads(data)
                self.process_message(message, addr[0])
                
        except Exception as e:
            print(f"Ошибка обработки клиента: {e} - messenger.ru.py:183")
        finally:
            client_socket.close()
    
    def process_message(self, message: Dict, sender_ip: str):
        """Обработка входящих сообщений"""
        msg_type = message.get('type')
        
        if msg_type == 'presence':
            self.add_user(sender_ip)
            
        elif msg_type == 'message':
            chat_id = message.get('chat_id')
            content = message.get('content')
            timestamp = message.get('timestamp')
            
            if chat_id not in self.chats:
                self.chats[chat_id] = []
                
            self.chats[chat_id].append({
                'sender': sender_ip,
                'content': content,
                'timestamp': timestamp,
                'type': 'received'
            })
            
            # Если это текущий чат, обновляем отображение
            if self.current_chat == chat_id:
                self.display_message(sender_ip, content, timestamp, False)
                
        elif msg_type == 'group_create':
            group_name = message.get('group_name')
            group_id = message.get('group_id')
            self.add_group(group_id, group_name)
    
    def broadcast_presence(self):
        """Широковещательное оповещение о своем присутствии"""
        while self.running:
            try:
                message = {
                    'type': 'presence',
                    'username': self.username,
                    'ip': self.host,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.broadcast_message(message)
                time.sleep(5)  # Оповещаем каждые 5 секунд
                
            except Exception as e:
                print(f"Ошибка broadcast: {e} - messenger.ru.py:233")
                time.sleep(5)
    
    def broadcast_message(self, message: Dict):
        """Отправка сообщения всем в сети"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        for i in range(1, 255):
            try:
                target_ip = '.'.join(self.host.split('.')[:-1]) + f'.{i}'
                if target_ip != self.host:
                    sock.sendto(
                        json.dumps(message).encode('utf-8'),
                        (target_ip, self.port)
                    )
            except:
                pass
        sock.close()
    
    def scan_network(self):
        """Сканирование сети для поиска пользователей"""
        message = {
            'type': 'discovery',
            'username': self.username,
            'ip': self.host
        }
        self.broadcast_message(message)
    
    def send_direct_message(self, target_ip: str, message: Dict):
        """Отправка сообщения конкретному пользователю"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((target_ip, self.port))
            sock.send(json.dumps(message).encode('utf-8'))
            sock.close()
            return True
        except:
            return False
    
    def add_user(self, ip: str):
        """Добавление пользователя в список"""
        if ip != self.host and ip not in self.users:
            self.users.add(ip)
            self.root.after(0, self.update_users_list)
    
    def add_group(self, group_id: str, group_name: str):
        """Добавление группы в список"""
        # Создаем отображаемое имя группы
        display_name = f"{group_name}"
        
        # Проверяем, нет ли уже такой группы
        existing_groups = [self.groups_listbox.get(i) for i in range(self.groups_listbox.size())]
        if display_name not in existing_groups:
            self.root.after(0, lambda: self.groups_listbox.insert(tk.END, display_name))
            # Сохраняем mapping для поиска
            if not hasattr(self, 'group_mapping'):
                self.group_mapping = {}
            self.group_mapping[display_name] = group_id
    
    def update_users_list(self):
        """Обновление списка пользователей"""
        self.users_listbox.delete(0, tk.END)
        for user in sorted(self.users):
            self.users_listbox.insert(tk.END, f"🟢 {user}")
    
    def update_status(self, message: str):
        """Обновление статусной строки"""
        self.root.after(0, lambda: self.status_var.set(message))
    
    def on_user_select(self, event):
        """Обработка выбора пользователя"""
        selection = self.users_listbox.curselection()
        if selection:
            user_ip = self.users_listbox.get(selection[0]).replace("🟢 ", "")
            self.open_private_chat(user_ip)
    
    def on_group_select(self, event):
        """Обработка выбора группы"""
        selection = self.groups_listbox.curselection()
        if selection:
            group_name = self.groups_listbox.get(selection[0])
            self.open_group_chat(group_name)
    
    def open_private_chat(self, user_ip: str):
        """Открытие приватного чата"""
        chat_id = f"private_{user_ip}"
        self.current_chat = chat_id
        self.chat_header.config(text=f"💬 Чат с {user_ip}")
        self.send_button.config(state=tk.NORMAL)
        self.message_entry.config(state=tk.NORMAL)
        self.clear_chat_area()
        self.load_chat_history(chat_id)
    
    def open_group_chat(self, group_name: str):
        """Открытие группового чата"""
        chat_id = f"group_{group_name}"
        self.current_chat = chat_id
        self.chat_header.config(text=f"👥 {group_name}")
        self.send_button.config(state=tk.NORMAL)
        self.message_entry.config(state=tk.NORMAL)
        self.clear_chat_area()
        self.load_chat_history(chat_id)
    
    def create_group(self):
        """Создание новой группы"""
        group_name = simpledialog.askstring("Создание группы", "Введите название группы:")
        if group_name and group_name.strip():
            group_name = group_name.strip()
            chat_id = f"group_{group_name}"
            
            # Добавляем группу в список
            self.groups_listbox.insert(tk.END, group_name)
            self.chats[chat_id] = []
            
            # Оповещаем других о создании группы
            message = {
                'type': 'group_create',
                'group_name': group_name,
                'group_id': chat_id,
                'creator': self.host,
                'timestamp': datetime.now().isoformat()
            }
            self.broadcast_message(message)
            
            self.update_status(f"Группа '{group_name}' создана")
    
    def send_message(self, event=None):
        """Отправка сообщения"""
        message_text = self.message_entry.get().strip()
        if not message_text or not self.current_chat:
            return
        
        timestamp = datetime.now().isoformat()
        
        # Сохраняем сообщение локально
        if self.current_chat not in self.chats:
            self.chats[self.current_chat] = []
        
        self.chats[self.current_chat].append({
            'sender': self.host,
            'content': message_text,
            'timestamp': timestamp,
            'type': 'sent'
        })
        
        # Отображаем сообщение
        self.display_message(self.host, message_text, timestamp, True)
        
        # Отправляем сообщение
        message = {
            'type': 'message',
            'chat_id': self.current_chat,
            'content': message_text,
            'sender': self.host,
            'timestamp': timestamp
        }
        
        if self.current_chat.startswith('private'):
            # Личное сообщение
            target_ip = self.current_chat.replace('private_', '')
            self.send_direct_message(target_ip, message)
        else:
            # Групповое сообщение - отправляем всем
            self.broadcast_message(message)
        
        self.message_entry.delete(0, tk.END)
    
    def display_message(self, sender: str, content: str, timestamp: str, is_own: bool):
        """Отображение сообщения в чате"""
        self.messages_text.config(state=tk.NORMAL)
        
        # Форматируем время
        try:
            time_obj = datetime.fromisoformat(timestamp)
            time_str = time_obj.strftime("%H:%M")
        except:
            time_str = timestamp
        
        # Добавляем сообщение
        if is_own:
            prefix = "Вы"
            tag = "own_message"
        else:
            prefix = sender
            tag = "other_message"
        
        self.messages_text.insert(tk.END, f"{prefix} ({time_str}):\n", tag)
        self.messages_text.insert(tk.END, f"{content}\n\n")
        
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)
    
    def clear_chat_area(self):
        """Очистка области чата"""
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.config(state=tk.DISABLED)
    
    def load_chat_history(self, chat_id: str):
        """Загрузка истории чата"""
        if chat_id in self.chats:
            for msg in self.chats[chat_id]:
                is_own = msg.get('type') == 'sent' or msg.get('sender') == self.host
                self.display_message(
                    msg['sender'], 
                    msg['content'], 
                    msg['timestamp'], 
                    is_own
                )
    
    def setup_text_tags(self):
        """Настройка тегов для форматирования текста"""
        self.messages_text.tag_configure("own_message", foreground="#3498db", font=('Arial', 10, 'bold'))
        self.messages_text.tag_configure("other_message", foreground="#2c3e50", font=('Arial', 10, 'bold'))
    
    def run(self):
        """Запуск приложения"""
        self.setup_text_tags()
        self.start_network()
        
        try:
            self.root.mainloop()
        finally:
            self.running = False
            if self.socket:
                self.socket.close()

def main():
    """Основная функция"""
    app = LocalMessenger()
    app.run()

if __name__ == "__main__":
    main()