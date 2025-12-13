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
            
            if user:  # 登录成功，返回用户信息
                user_info = {
                    "account": user[0],
                    "name": user[1],
                    "role": user[2]
                }
                return True, user_info
            else:  #找不到user，登陆失败
                return False, "账号或密码错误"
        except Exception as e:
            return False, f"数据库错误: {str(e)}"
        finally:
            conn.close()

    def register_user(self, account, password, name, role, phone):
        """
        注册新用户
        :param account: 账号
        :param password: 密码
        :param name: 姓名
        :param role: 角色
        :param phone: 电话
        :return: (bool, str) - (是否成功, 消息)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            import datetime
            create_time = datetime.datetime.now()
            # 默认信用分 100
            cursor.execute("""
                INSERT INTO users (user_account, password, name, role, phone, credit_score, create_time)
                VALUES (?, ?, ?, ?, ?, 100, ?)
            """, (account, password, name, role, phone, create_time))
            conn.commit()
            return True, "注册成功"
        except sqlite3.IntegrityError:
            return False, "该账号已存在"
        except Exception as e:
            return False, f"注册失败: {str(e)}"
        finally:
            conn.close()

    def get_available_slots(self, venue_id, date_str):
        """
        查询某场馆某天的可用时间段
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 关联查询：时间段 -> 场地 -> 场馆
            # 查询所有时间段（包括已满），由前端判断是否可预约
            sql = """
                SELECT ts.slot_id, c.court_name, ts.start_time, ts.end_time, 
                       ts.current_reservations, ts.max_reservations, ts.is_hot
                FROM time_slots ts
                JOIN courts c ON ts.court_id = c.court_id
                WHERE c.venue_id = ? AND ts.date = ?
                ORDER BY ts.start_time, c.court_name
            """
            cursor.execute(sql, (venue_id, date_str))
            rows = cursor.fetchall()
            
            slots = []
            for row in rows:
                slots.append({
                    "slot_id": row[0],
                    "court_name": row[1],
                    "start_time": row[2],
                    "end_time": row[3],
                    "current": row[4],
                    "max": row[5],
                    "is_hot": row[6]
                })
            return True, slots
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def create_reservation(self, user_account, slot_id):
        """
        创建预约 (核心事务逻辑)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            import datetime
            # 1. 检查用户信用分 (需求：信用分过低可能限制预约，这里先做基础检查)
            cursor.execute("SELECT credit_score FROM users WHERE user_account=?", (user_account,))
            user_res = cursor.fetchone()
            if not user_res:
                return False, "用户不存在"
            credit_score = user_res[0]
            # 逻辑：信用分限制 (示例：低于60分不能预约热门时段)
            if is_hot and credit_score < 60:
                return False, "您的信用分低于60，无法预约热门时段"
            
            # 2. 检查时间段状态 (容量、是否热门)
            cursor.execute("SELECT current_reservations, max_reservations, is_hot, start_time FROM time_slots WHERE slot_id=?", (slot_id,))
            slot_res = cursor.fetchone()
            if not slot_res:
                return False, "时间段不存在"
            current_res, max_res, is_hot, start_time = slot_res
            # 逻辑：如果满了，无法预约
            if current_res >= max_res:
                return False, "该时段预约人数已满"
            
            # 3. 检查用户是否在该时段已有预约 (防止冲突)
            # 这里简化处理，假设一个 slot_id 代表一个具体场地的具体时段
            # 如果是不同场地同一时间，可能需要更复杂的 SQL 判断 start_time
            cursor.execute("""
                SELECT r.reservation_id FROM reservations r
                WHERE r.user_account = ? AND r.slot_id = ? AND r.status = 'confirmed'
            """, (user_account, slot_id))
            if cursor.fetchone():
                return False, "您已预约过该时段，请勿重复预约"

            # 4. 执行预约 (事务开始)
            # 插入预约记录
            create_time = datetime.datetime.now()
            cursor.execute("""
                INSERT INTO reservations (user_account, slot_id, status, create_time)
                VALUES (?, ?, 'confirmed', ?)
            """, (user_account, slot_id, create_time))
            
            # 更新时间段的当前预约人数 (+1)
            cursor.execute("""
                UPDATE time_slots 
                SET current_reservations = current_reservations + 1 
                WHERE slot_id = ?
            """, (slot_id,))
            
            conn.commit() # 提交事务
            return True, "预约成功"
            
        except Exception as e:
            conn.rollback() # 发生错误回滚
            return False, f"预约失败: {str(e)}"
        finally:
            conn.close()

    def get_user_reservations(self, user_account):
        """
        获取用户的预约列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT r.reservation_id, v.venue_name, c.court_name, ts.date, ts.start_time, ts.end_time, r.status
                FROM reservations r
                JOIN time_slots ts ON r.slot_id = ts.slot_id
                JOIN courts c ON ts.court_id = c.court_id
                JOIN venues v ON c.venue_id = v.venue_id
                WHERE r.user_account = ?
                ORDER BY r.create_time DESC
            """
            cursor.execute(sql, (user_account,))
            rows = cursor.fetchall()
            
            res_list = []
            for row in rows:
                res_list.append({
                    "id": row[0],
                    "venue": row[1],
                    "court": row[2],
                    "date": row[3],
                    "time": f"{row[4]}-{row[5]}",
                    "status": row[6]
                })
            return True, res_list
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def cancel_reservation(self, user_account, reservation_id):
        """
        取消预约
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            import datetime
            
            # 1. 检查预约是否存在且属于该用户，且状态为 confirmed
            cursor.execute("""
                SELECT slot_id, status FROM reservations 
                WHERE reservation_id = ? AND user_account = ?
            """, (reservation_id, user_account))
            res = cursor.fetchone()
            
            if not res:
                return False, "预约不存在或无权操作"
            
            slot_id, status = res
            
            if status != 'confirmed':
                return False, f"当前状态({status})无法取消"
            
            # 2. 执行取消 (事务)
            cancel_time = datetime.datetime.now()
            
            # 更新预约状态
            cursor.execute("""
                UPDATE reservations 
                SET status = 'cancelled', cancel_time = ?
                WHERE reservation_id = ?
            """, (cancel_time, reservation_id))
            
            # 释放名额 (人数 -1)
            cursor.execute("""
                UPDATE time_slots 
                SET current_reservations = current_reservations - 1 
                WHERE slot_id = ?
            """, (slot_id,))
            
            conn.commit()
            return True, "取消成功"
            
        except Exception as e:
            conn.rollback()
            return False, f"取消失败: {str(e)}"
        finally:
            conn.close()
