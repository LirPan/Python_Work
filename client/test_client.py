import socket
import json
import sys

def test_client():
    host = '127.0.0.1'
    port = 8888
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"正在连接服务器 {host}:{port} ...")
        client_socket.connect((host, port))
        print("连接成功！")
        
        # 测试 1: 登录成功
        print("\n--- 测试 1: 尝试使用正确账号登录 ---")
        login_request = {
            "action": "login",
            "data": {
                "account": "2021001",
                "password": "123456"
            }
        }
        send_request(client_socket, login_request)
        
        # 测试 2: 登录失败
        print("\n--- 测试 2: 尝试使用错误密码登录 ---")
        fail_request = {
            "action": "login",
            "data": {
                "account": "2021001",
                "password": "6543210"
            }
        }
        send_request(client_socket, fail_request)
        
    except ConnectionRefusedError:
        print("连接被拒绝。请确保服务器 (server/server.py) 正在运行。")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        client_socket.close()
        print("\n连接已关闭。")

def send_request(sock, request_dict):
    # 发送
    json_str = json.dumps(request_dict, ensure_ascii=False)
    print(f"发送: {json_str}")
    sock.send(json_str.encode('utf-8'))
    
    # 接收
    response_data = sock.recv(4096).decode('utf-8')
    try:
        # 尝试解析 JSON 并格式化输出，方便阅读
        parsed_json = json.loads(response_data)
        print(f"接收: {json.dumps(parsed_json, ensure_ascii=False)}")
    except:
        print(f"接收: {response_data}")

if __name__ == '__main__':
    test_client()
