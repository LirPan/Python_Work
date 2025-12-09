import socket
import threading
import json
import sys
import os

# 将项目根目录添加到 sys.path，以便导入 server.db_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from server.db_manager import DBManager
except ImportError:
    # Fallback for direct execution
    sys.path.append(current_dir)
    from db_manager import DBManager

class SportsVenueServer:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.db_manager = DBManager()
        self.running = True

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"[*] 服务器已启动，监听 {self.host}:{self.port}")
            print(f"[*] 等待客户端连接...")
            
            while self.running:
                client_sock, addr = self.server_socket.accept()
                print(f"[*] 接受连接来自: {addr}")
                
                # 为每个客户端创建一个独立的线程进行处理
                client_handler = threading.Thread(target=self.handle_client, args=(client_sock,))
                client_handler.daemon = True # 设置为守护线程，主程序退出时自动结束
                client_handler.start()
        except Exception as e:
            print(f"[!] 服务器启动失败: {e}")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket):
        try:
            while True:
                # 接收数据 (最大 4096 字节)
                request_data = client_socket.recv(4096).decode('utf-8')
                if not request_data:
                    break
                
                print(f"[>] 收到请求: {request_data}")
                
                try:
                    request = json.loads(request_data)
                    response = self.process_request(request)
                except json.JSONDecodeError:
                    response = {"status": "error", "message": "无效的 JSON 格式"}
                except Exception as e:
                    response = {"status": "error", "message": f"服务器内部错误: {str(e)}"}
                
                # 发送响应
                # ensure_ascii=False 允许直接输出中文，而不是 Unicode 编码
                response_data = json.dumps(response, ensure_ascii=False)
                print(f"[<] 发送响应: {response_data}")
                client_socket.send(response_data.encode('utf-8'))
                
        except ConnectionResetError:
            print(f"[*] 客户端强制断开连接")
        except Exception as e:
            print(f"[!] 客户端处理错误: {e}")
        finally:
            print(f"[*] 连接关闭")
            client_socket.close()

    def process_request(self, request):
        """
        根据请求的 action 字段分发处理逻辑
        """
        action = request.get('action')
        data = request.get('data')
        
        if action == 'login':
            return self.handle_login(data)
        # 这里可以继续添加 elif action == 'register': ...
        else:
            return {"status": "error", "message": f"未知的请求类型: {action}"}

    def handle_login(self, data):
        if not data:
            return {"status": "error", "message": "缺少请求数据"}
            
        account = data.get('account')
        password = data.get('password')
        
        if not account or not password:
            return {"status": "error", "message": "账号或密码不能为空"}
            
        success, result = self.db_manager.validate_login(account, password)
        
        if success:
            return {"status": "success", "message": "登录成功", "user": result}
        else:
            return {"status": "fail", "message": result}

if __name__ == '__main__':
    # 可以在这里配置 IP 和 端口
    server = SportsVenueServer()
    server.start()
