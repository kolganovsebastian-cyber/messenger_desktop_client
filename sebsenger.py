import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import socket
import messaging_protocol as mp
import json
import datetime
import time


class ChatBubble(QWidget):
    def __init__(self, text, sent=True):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setStyleSheet(
            f"""
            background-color: {"#0a84ff" if sent else "#3a3f47"};
            color: white;
            padding: 8px 12px;
            border-radius: 12px;
            max-width: 200px;
            """
        )
        if sent:
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            layout.addWidget(bubble)
            layout.addStretch()


class LoginWindow(QWidget):
    def __init__(self, connection, callback):
        super().__init__()
        self.connection = connection
        self.callback = callback
        self.setWindowTitle("Login")
        self.setFixedSize(300, 150)
        layout = QVBoxLayout(self)
        self.invalid_text = QLabel("INVALID Triesss letf; 12 ")
        self.invalid_text.setStyleSheet(
                """
                QLabel {
                    background-color: #2c2f33;
                    color: red;
                    border: black;
                    border-radius: 2px;
                }
                """
            )
        self.invalid_text.hide()
        self.tri_num = 3
        layout.addWidget(self.invalid_text)
        self.username_field = QLineEdit()
        self.username_field.setPlaceholderText("Username")
        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText("Password")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.try_login)
        layout.addWidget(self.username_field)
        layout.addWidget(self.password_field)
        layout.addWidget(self.login_button)
        

    def try_login(self):
        username = self.username_field.text()
        password = self.password_field.text()
        log_in = self.connection.login(username=username, password=password)
        print(log_in)
        if log_in is not None:
            self.callback(username)
            self.close()
        else:
            self.tri_num -= 1
            self.invalid_text.setText(f"INVALID Triesss letf; {self.tri_num}")
            self.invalid_text.show()
            if self.tri_num == 0:
                raise NotImplementedError("NOT IMPLEMENTED NOT COMING SOON")


class Sebsenger:
    def __init__(self):
        self.connection = ServerConnection()
        self.username = None
        self.login_window = LoginWindow(self.connection, self.start_main_window)
        self.login_window.show()

    def start_main_window(self, username):
        self.message_history = self.connection.get_message_history()
        self.new_messages_count = {}
        file = open("old_history.json", "r", encoding="utf-8")
        old_history = json.load(file)
        file.close()
        for a in self.message_history:
            new_history_count = len(self.message_history[a])
            old_history_count = len(old_history[a])
            self.new_messages_count[a] = new_history_count - old_history_count
        self.get_message_thread = GetMessagesThread(self.connection)
        self.get_message_thread.signal.connect(self.update_chat)
        self.get_message_thread.start()
        self.username = username
        self.window = QWidget()
        self.window.setWindowTitle("massangar")
        self.window.setFixedSize(500, 440)
        self.main_layout = QHBoxLayout(self.window)
        self.chat_list_container = QWidget()
        self.chat_list_layout = QVBoxLayout(self.chat_list_container)
        self.chat_list_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_list_layout.setSpacing(5)
        self.chat_list_container.setFixedWidth(150)
        self.create_chat_buttons()
        self.chat_list_layout.addStretch()
        self.chat_layout_container = QVBoxLayout()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.chat_content = QWidget()
        self.chat_content_layout = QVBoxLayout(self.chat_content)
        self.chat_content_layout.addStretch()
        self.scroll.setWidget(self.chat_content)
        self.input_field = QLineEdit()
        self.send_button = QPushButton("➤")
        self.send_button.setFixedWidth(40)
        self.send_button.clicked.connect(self.send_message)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        self.chat_layout_container.addWidget(self.scroll)
        self.chat_layout_container.addLayout(input_layout)
        self.main_layout.addWidget(self.chat_list_container)
        self.main_layout.addLayout(self.chat_layout_container)
        self.user_to_chat = None
        self.window.show()

    def open_chat(self, user_to_chat):
        if self.user_to_chat != user_to_chat:
            for i in reversed(range(self.chat_content_layout.count())):
                widget = self.chat_content_layout.itemAt(i).widget()
                if widget is not None:
                    widget.setParent(None)
            if self.user_to_chat != None:
                self.btn_list[self.user_to_chat].setStyleSheet(
                        """
                        QPushButton {
                            background-color: #2c2f33;
                            color: white;
                            border: none;
                            border-radius: 6px;
                        }
                        QPushButton:hover {
                            background-color: #3a3f47;
                        }
                        """
                    )
            self.user_to_chat = user_to_chat
            button_to_change = self.btn_list[self.user_to_chat]
            button_to_change.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #0062ff;
                        color: white;
                        border: none;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #3a3f47;
                    }
                    """
                )
            history_with_user = self.message_history[user_to_chat]
            for history in history_with_user:
                self.add_message(history["message"], history["is_sent"])
            message = self.message_history[user_to_chat][-1]["message"]
            if len(message) > 7:
                message = message[:6] + "..."
            self.btn_list[user_to_chat].setText(user_to_chat + " " + message)
            self.new_messages_count[user_to_chat] = 0

    def add_message(self, text, sent=True):
        bubble = ChatBubble(text, sent)
        self.chat_content_layout.insertWidget(self.chat_content_layout.count() - 1, bubble)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def send_message(self):
        text = self.input_field.text()
        if not text:
            return
        self.add_message(text, sent=True)
        self.input_field.clear()
        self.connection.send_message(text, self.user_to_chat)

    def create_chat_buttons(self):
        self.btn_list = {}
        for a in self.message_history:
            if self.message_history[a] != []:
                last_message = self.message_history[a][-1]["message"]
            else: 
                last_message = "No Messages"
            if len(last_message) > 7:
                last_message = last_message[:6] + "..."
            if self.new_messages_count[a] != 0:
                last_message = last_message + str(self.new_messages_count[a])
            btn = QPushButton(a + " " + last_message)
            btn.setFixedHeight(35)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #2c2f33;
                    color: white;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #3a3f47;
                }
                """
                )
            btn.clicked.connect(lambda _, user_to_chat=a: self.open_chat(user_to_chat))
            self.chat_list_layout.addWidget(btn)
            self.btn_list[a] = btn
            

    def update_chat(self, dicti):
        btn = self.btn_list[dicti["sender_username"]]
        if self.user_to_chat == dicti["sender_username"]:
            self.add_message(dicti["message"], sent=False)
            btn.setText(dicti["sender_username"] + " " + dicti["message"])
        else:
            dicti_to_send = {"message": dicti["message"], "date": str(datetime.date.today), "is_sent": False}
            self.message_history[dicti["sender_username"]].append(dicti_to_send)
            self.new_messages_count[dicti["sender_username"]] += 1
            message = dicti["message"]
            if len(message) > 7:
                message = message[:6] + "..."
            self.btn_list[dicti["sender_username"]].setText(f"{dicti["sender_username"]} {message} {self.new_messages_count[dicti["sender_username"]]}")

    def quit(self):
        file = open("old_history.json", "w", encoding="utf-8")
        json.dump(self.message_history, file, indent=4, ensure_ascii=False)
        file.close()
        self.connection.disconnect()


class ServerConnection():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("127.0.0.1", 8500))
    
    def login(self, username, password):
        mp.send_text(self.socket, username)
        mp.send_text(self.socket, password)
        accepted = mp.recv_information(self.socket)[1]
        if accepted == "0":
            return None
        else:
            file = open("cookies.json", "w", encoding="utf-8")
            dict_to_write = {"username": username, "password": password, "date": str(datetime.date.today())}
            json.dump(dict_to_write, file, ensure_ascii=False, indent=4)
            file.close()
            return username
    
    def get_message_history(self):
        received = mp.recv_information(self.socket)
        if received[0] == "JSN":
            message_history = json.loads(received[1])
            return message_history
        else:
            raise NotImplementedError("YOZ DONT MAK JASOPN")
 
    def send_message(self, message, receiver_username):
        dict_to_send = {"message": message, "receiver_username": receiver_username}
        mp.send_jason(self.socket, dict_to_send)

    def disconnect(self):
        mp.send_jason(self.socket, {"message": "exit"})

class GetMessagesThread(QThread):
    signal = pyqtSignal(dict)
    def __init__(self, connection, parent=None):
        super().__init__(parent)
        self.connection = connection
    def run(self):
        while True:
            message = mp.recv_information(self.connection.socket)[1]
            if message == "Ok Exit":
                break
            message = json.loads(message)
            self.signal.emit(message)


app = QApplication(sys.argv)
client = Sebsenger()
app.aboutToQuit.connect(client.quit)
app.exec()
