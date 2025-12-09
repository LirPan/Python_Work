import sqlite3
import os

# 获取项目根目录 (假设此文件在 server/ 目录下)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sports_venue.db')

class DBManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def validate_login(self, account, password):
        """
        验证登录
        :param account: 用户账号
        :param password: 密码 (暂未加密，实际应比对哈希)
        :return: (bool, str/dict) - (是否成功, 用户信息或错误消息)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 查询用户
            cursor.execute("SELECT user_account, name, role FROM users WHERE user_account=? AND password=?", (account, password))
            user = cursor.fetchone()
            
            if user:
                # 登录成功，返回用户信息
                user_info = {
                    "account": user[0],
                    "name": user[1],
                    "role": user[2]
                }
                return True, user_info
            else:
                return False, "账号或密码错误"
        except Exception as e:
            return False, f"数据库错误: {str(e)}"
        finally:
            conn.close()
