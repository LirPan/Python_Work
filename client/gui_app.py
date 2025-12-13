import tkinter as tk
from tkinter import messagebox, ttk
import socket
import json
import sys

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

    def send_request(self, action, data):
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

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("体育场馆管理系统 - 登录")
        self.root.geometry("400x300")
        
        self.network = NetworkClient()
        
        # 初始化界面
        self.create_login_frame()

    def create_login_frame(self):
        self.clear_frame()
        self.frame = tk.Frame(self.root, padx=20, pady=20)
        self.frame.pack(expand=True, fill='both')

        tk.Label(self.frame, text="欢迎登录", font=("Arial", 16)).pack(pady=10)

        # 账号
        tk.Label(self.frame, text="账号 (学号/工号):").pack(anchor='w')
        self.entry_account = tk.Entry(self.frame)
        self.entry_account.pack(fill='x', pady=5)

        # 密码
        tk.Label(self.frame, text="密码:").pack(anchor='w')
        self.entry_password = tk.Entry(self.frame, show="*")
        self.entry_password.pack(fill='x', pady=5)

        # 按钮区域
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(fill='x', pady=20)
        
        tk.Button(btn_frame, text="登录", command=self.handle_login, bg="#4CAF50", fg="white", width=10).pack(side='left', padx=5)
        tk.Button(btn_frame, text="注册账号", command=self.create_register_frame, width=10).pack(side='right', padx=5)

    def create_register_frame(self):
        self.clear_frame()
        self.frame = tk.Frame(self.root, padx=20, pady=20)
        self.frame.pack(expand=True, fill='both')

        tk.Label(self.frame, text="新用户注册", font=("Arial", 16)).pack(pady=10)

        # 表单区域
        form_frame = tk.Frame(self.frame)
        form_frame.pack(fill='both', expand=True)

        # 账号
        tk.Label(form_frame, text="账号 (必填):").grid(row=0, column=0, sticky='w')
        self.reg_account = tk.Entry(form_frame)
        self.reg_account.grid(row=0, column=1, sticky='ew', padx=5, pady=2)

        # 密码
        tk.Label(form_frame, text="密码 (必填, >5位):").grid(row=1, column=0, sticky='w')
        self.reg_password = tk.Entry(form_frame, show="*")
        self.reg_password.grid(row=1, column=1, sticky='ew', padx=5, pady=2)

        # 姓名
        tk.Label(form_frame, text="姓名 (必填):").grid(row=2, column=0, sticky='w')
        self.reg_name = tk.Entry(form_frame)
        self.reg_name.grid(row=2, column=1, sticky='ew', padx=5, pady=2)

        # 角色
        tk.Label(form_frame, text="角色:").grid(row=3, column=0, sticky='w')
        self.reg_role = ttk.Combobox(form_frame, values=["student", "teacher"])
        self.reg_role.current(0)
        self.reg_role.grid(row=3, column=1, sticky='ew', padx=5, pady=2)

        # 电话
        tk.Label(form_frame, text="电话:").grid(row=4, column=0, sticky='w')
        self.reg_phone = tk.Entry(form_frame)
        self.reg_phone.grid(row=4, column=1, sticky='ew', padx=5, pady=2)

        # 按钮
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(fill='x', pady=20)
        tk.Button(btn_frame, text="提交注册", command=self.handle_register, bg="#2196F3", fg="white").pack(side='left', fill='x', expand=True, padx=5)
        tk.Button(btn_frame, text="返回登录", command=self.create_login_frame).pack(side='right', padx=5)

    def clear_frame(self):
        if hasattr(self, 'frame'):
            self.frame.destroy()

    def handle_login(self):
        account = self.entry_account.get().strip()
        password = self.entry_password.get().strip()

        if not account or not password:
            messagebox.showwarning("提示", "请输入账号和密码")
            return

        resp = self.network.send_request("login", {"account": account, "password": password})
        
        if resp.get("status") == "success":
            user = resp.get("user")
            messagebox.showinfo("成功", f"登录成功！\n欢迎回来，{user['name']} ({user['role']})")
            # 这里可以跳转到主界面，目前先打印
            print(f"用户登录: {user}")
        else:
            messagebox.showerror("登录失败", resp.get("message", "未知错误"))

    def handle_register(self):
        account = self.reg_account.get().strip()
        password = self.reg_password.get().strip()
        name = self.reg_name.get().strip()
        role = self.reg_role.get()
        phone = self.reg_phone.get().strip()

        # 表单验证
        if not account:
            messagebox.showwarning("验证失败", "账号不能为空")
            return
        if len(password) < 6:
            messagebox.showwarning("验证失败", "密码长度必须大于等于6位")
            return
        if not name:
            messagebox.showwarning("验证失败", "姓名不能为空")
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
            messagebox.showinfo("成功", "注册成功！请返回登录。")
            self.create_login_frame()
        else:
            messagebox.showerror("注册失败", resp.get("message"))

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
