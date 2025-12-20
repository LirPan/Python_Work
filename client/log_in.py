import sys
import json
import socket
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox, 
                             QStackedWidget, QComboBox, QFrame)
from PyQt5.QtCore import Qt

# Import TeacherDashboard from the new Qt file
try:
    from import_class import TeacherDashboard
except ImportError:
    from client.import_class import TeacherDashboard

class NetworkClient:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.client_socket = None

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"连接服务器失败: {e}")
            return False

    def send_request(self, action, data=None):
        if isinstance(action, dict) and data is None:
            data = action.get("data", {})
            action = action.get("action")

        if not self.client_socket:
            if not self.connect():
                return {"status": "error", "message": "无法连接到服务器"}
        
        try:
            request = {"action": action, "data": data}
            self.client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            response_data = self.client_socket.recv(4096).decode('utf-8')
            return json.loads(response_data)
        except Exception as e:
            return {"status": "error", "message": f"通信错误: {str(e)}"}
    
    def close(self):
        if self.client_socket:
            self.client_socket.close()

class LoginWindow(QWidget):
    def __init__(self, network_client=None, login_callback=None):
        super().__init__()
        self.login_callback = login_callback
        if network_client:
            self.network = network_client
        else:
            self.network = NetworkClient()
            
        self.setWindowTitle("体育场馆管理系统")
        self.resize(400, 350)
        
        self.stacked_widget = QStackedWidget()
        self.init_login_ui()
        self.init_register_ui()
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)
        
        self.show_login()

    def init_login_ui(self):
        self.login_page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("欢迎登录")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Form
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        
        form_layout.addWidget(QLabel("账号 (学号/工号):"))
        self.login_account = QLineEdit()
        form_layout.addWidget(self.login_account)
        
        form_layout.addWidget(QLabel("密码:"))
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.login_password)
        
        layout.addWidget(form_frame)
        
        # Buttons
        btn_layout = QHBoxLayout()
        login_btn = QPushButton("登录")
        login_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        login_btn.clicked.connect(self.handle_login)
        
        reg_btn = QPushButton("注册账号")
        reg_btn.clicked.connect(self.show_register)
        
        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(reg_btn)
        layout.addLayout(btn_layout)
        
        self.login_page.setLayout(layout)
        self.stacked_widget.addWidget(self.login_page)

    def init_register_ui(self):
        self.register_page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("新用户注册")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Form
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        
        form_layout.addWidget(QLabel("账号 (必填):"))
        self.reg_account = QLineEdit()
        form_layout.addWidget(self.reg_account)
        
        form_layout.addWidget(QLabel("密码 (必填, >5位):"))
        self.reg_password = QLineEdit()
        self.reg_password.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.reg_password)
        
        form_layout.addWidget(QLabel("姓名 (必填):"))
        self.reg_name = QLineEdit()
        form_layout.addWidget(self.reg_name)
        
        form_layout.addWidget(QLabel("角色:"))
        self.reg_role = QComboBox()
        self.reg_role.addItems(["student", "teacher"])
        form_layout.addWidget(self.reg_role)
        
        form_layout.addWidget(QLabel("电话:"))
        self.reg_phone = QLineEdit()
        form_layout.addWidget(self.reg_phone)
        
        layout.addWidget(form_frame)
        
        # Buttons
        btn_layout = QHBoxLayout()
        submit_btn = QPushButton("提交注册")
        submit_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        submit_btn.clicked.connect(self.handle_register)
        
        back_btn = QPushButton("返回登录")
        back_btn.clicked.connect(self.show_login)
        
        btn_layout.addWidget(submit_btn)
        btn_layout.addWidget(back_btn)
        layout.addLayout(btn_layout)
        
        self.register_page.setLayout(layout)
        self.stacked_widget.addWidget(self.register_page)

    def show_login(self):
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.setWindowTitle("体育场馆管理系统 - 登录")

    def show_register(self):
        self.stacked_widget.setCurrentWidget(self.register_page)
        self.setWindowTitle("体育场馆管理系统 - 注册")

    def handle_login(self):
        account = self.login_account.text().strip()
        password = self.login_password.text().strip()

        if not account or not password:
            QMessageBox.warning(self, "提示", "请输入账号和密码")
            return

        resp = self.network.send_request("login", {"account": account, "password": password})
        
        if resp.get("status") == "success":
            user = resp.get("user")
            
            # Call callback if exists
            if self.login_callback:
                self.login_callback(user)
            
            if user['role'] == 'teacher':
                QMessageBox.information(self, "提示", f"现在为教师端。\n欢迎教师用户: {user['name']}")
                self.close() # Close login window to return to Home
            elif user['role'] == 'student':
                QMessageBox.information(self, "提示", f"现在为学生端。\n欢迎学生用户: {user['name']}")
                self.close() # Close login window to return to Home
            elif user['role'] == 'admin':
                QMessageBox.information(self, "提示", f"现在为管理员端。\n欢迎管理员用户: {user['name']}")
                self.close() # Close login window to return to Home
        else:
            QMessageBox.critical(self, "登录失败", resp.get("message", "未知错误"))

    def handle_register(self):
        account = self.reg_account.text().strip()
        password = self.reg_password.text().strip()
        name = self.reg_name.text().strip()
        role = self.reg_role.currentText()
        phone = self.reg_phone.text().strip()

        if not account:
            QMessageBox.warning(self, "验证失败", "账号不能为空")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "验证失败", "密码长度必须大于等于6位")
            return
        if not name:
            QMessageBox.warning(self, "验证失败", "姓名不能为空")
            return

        data = {
            "account": account,
            "password": password,
            "name": name,
            "role": role,
            "phone": phone
        }

        resp = self.network.send_request("register", data)
        
        if resp.get("status") == "success":
            QMessageBox.information(self, "成功", "注册成功！请返回登录。")
            self.show_login()
        else:
            QMessageBox.critical(self, "注册失败", resp.get("message"))

    def open_teacher_dashboard(self, user):
        self.hide()
        self.dashboard = TeacherDashboard(self.network, user, self.restore_login)
        self.dashboard.show()

    def restore_login(self):
        self.show_login()
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
