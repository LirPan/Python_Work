import sqlite3
import os
import datetime

# 获取数据库路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sports_venue.db')

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"正在向 {DB_PATH} 插入测试数据...")
    
    try:
        # 插入测试用户 (如果不存在)
        # 注意：这里直接存储明文密码 '123456'，实际项目请使用 hash
        users = [
            ('2021001', '123456', '张三', 'student', '13800138000', 100, datetime.datetime.now()),
            ('2021002', '123456', '李四', 'teacher', '13900139000', 100, datetime.datetime.now()),
            ('admin', 'admin888', '管理员', 'admin', '10086', 100, datetime.datetime.now())
        ]
        
        for user in users:
            try:
                cursor.execute("""
                    INSERT INTO users (user_account, password, name, role, phone, credit_score, create_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, user)
                print(f"已添加用户: {user[0]} ({user[2]})")
            except sqlite3.IntegrityError:
                print(f"用户 {user[0]} 已存在，跳过。")
        
        conn.commit()
        print("测试数据插入完成。")
        
    except Exception as e:
        print(f"插入数据时出错: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    seed_data()
