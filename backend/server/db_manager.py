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

    def add_teacher_schedule(self, teacher_account, venue_id, day_of_week, start_time, end_time):
        """
        教师添加课表 (特权操作)
        :param venue_id: 场馆ID (锁定该场馆下所有场地)
        :param day_of_week: 0=周一 ... 6=周日
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            import datetime
            import calendar
            
            # 1. 验证身份
            cursor.execute("SELECT role FROM users WHERE user_account=?", (teacher_account,))
            user = cursor.fetchone()
            if not user or user[0] != 'teacher':
                return False, "只有教师可以执行此操作"

            # 2. 获取该场馆下的所有场地ID
            cursor.execute("SELECT court_id FROM courts WHERE venue_id = ?", (venue_id,))
            courts = cursor.fetchall()
            if not courts:
                return False, "该场馆下没有场地"
            
            court_ids = [c[0] for c in courts]

            # 3. 计算4个月后的日期 (作为课表截止日期)
            today = datetime.date.today()
            today_str = today.strftime('%Y-%m-%d')
            
            year = today.year + (today.month + 4 - 1) // 12
            month = (today.month + 4 - 1) % 12 + 1
            day = min(today.day, calendar.monthrange(year, month)[1])
            end_date_str = datetime.date(year, month, day).strftime('%Y-%m-%d')

            # 4. 插入课表记录 (记录截止日期)
            cursor.execute("""
                INSERT INTO class_schedules (teacher_account, venue_id, day_of_week, start_time, end_time, end_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (teacher_account, venue_id, day_of_week, start_time, end_time, end_date_str))
            
            # 5. 遍历未来4个月的每一天，按需生成或更新时间段
            current_date = today
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            while current_date <= end_date:
                if current_date.weekday() == day_of_week:
                    date_str = current_date.strftime('%Y-%m-%d')
                    
                    # 对该场馆下的每一个场地进行锁定
                    for court_id in court_ids:
                        # 检查时间段是否存在
                        cursor.execute("""
                            SELECT slot_id, max_reservations, current_reservations 
                            FROM time_slots 
                            WHERE court_id = ? AND date = ? AND start_time = ? AND end_time = ?
                        """, (court_id, date_str, start_time, end_time))
                        
                        slot_res = cursor.fetchone()
                        
                        if slot_res:
                            # --- 情况A: 时间段已存在 ---
                            s_id, s_max, s_curr = slot_res
                            
                            # A1. 取消冲突预约
                            cursor.execute("""
                                UPDATE reservations 
                                SET status = 'cancelled_by_teacher', cancel_time = ?
                                WHERE slot_id = ? AND user_account != ? AND status = 'confirmed'
                            """, (datetime.datetime.now(), s_id, teacher_account))
                            
                            # A2. 锁定场地
                            cursor.execute("""
                                UPDATE time_slots 
                                SET current_reservations = ? 
                                WHERE slot_id = ?
                            """, (s_max, s_id))
                            
                        else:
                            # --- 情况B: 时间段不存在 (按需生成) ---
                            s_max = 1 # 默认容量
                            
                            cursor.execute("""
                                INSERT INTO time_slots (court_id, date, start_time, end_time, max_reservations, current_reservations, is_hot)
                                VALUES (?, ?, ?, ?, ?, ?, 0)
                            """, (court_id, date_str, start_time, end_time, s_max, s_max)) # 直接设为满员
                            s_id = cursor.lastrowid

                        # --- 公共步骤: 为教师创建预约 ---
                        # 检查是否已预约
                        cursor.execute("""
                            SELECT reservation_id FROM reservations 
                            WHERE slot_id = ? AND user_account = ? AND status = 'confirmed'
                        """, (s_id, teacher_account))
                        
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO reservations (user_account, slot_id, status, create_time)
                                VALUES (?, ?, 'confirmed', ?)
                            """, (teacher_account, s_id, datetime.datetime.now()))

                # 移动到下一天
                current_date += datetime.timedelta(days=1)

            conn.commit()
            return True, "课表导入成功，未来4个月的相关场地已锁定"
            
        except Exception as e:
            conn.rollback()
            return False, f"操作失败: {str(e)}"
        finally:
            conn.close()

    def remove_teacher_schedule(self, teacher_account, schedule_id):
        """
        教师移除课表 (解锁场地)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            import datetime
            import calendar
            
            # 1. 获取课表详情以用于查找受影响的 slot
            # 注意：这里需要获取 end_date，以便知道当初锁定了多久
            cursor.execute("SELECT court_id, day_of_week, start_time, end_time, end_date FROM class_schedules WHERE schedule_id=?", (schedule_id,))
            schedule = cursor.fetchone()
            if not schedule:
                return False, "课表不存在"
            
            court_id, day_of_week, start_time, end_time, end_date_str = schedule
            
            # 2. 删除课表记录
            cursor.execute("DELETE FROM class_schedules WHERE schedule_id=?", (schedule_id,))
            
            # 3. 解锁未来受影响的时间段 (使用当初记录的 end_date)
            today = datetime.date.today()
            today_str = today.strftime('%Y-%m-%d')
            
            # 如果 end_date 为空 (旧数据)，则默认按当前时间+4个月处理，或者直接跳过
            if not end_date_str:
                 # 兼容旧数据逻辑，或者直接报错。这里选择兼容：计算当前+4个月
                year = today.year + (today.month + 4 - 1) // 12
                month = (today.month + 4 - 1) % 12 + 1
                day = min(today.day, calendar.monthrange(year, month)[1])
                end_date_str = datetime.date(year, month, day).strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT slot_id, date, start_time, end_time 
                FROM time_slots 
                WHERE court_id = ? AND date >= ? AND date <= ?
            """, (court_id, today_str, end_date_str))
            
            slots = cursor.fetchall()
            
            for slot in slots:
                s_id, s_date_str, s_start, s_end = slot
                
                if s_start[:5] != start_time[:5] or s_end[:5] != end_time[:5]:
                    continue
                
                s_date = datetime.datetime.strptime(s_date_str, '%Y-%m-%d').date()
                if s_date.weekday() != day_of_week:
                    continue
                
                # --- 匹配成功，执行解锁逻辑 ---
                
                # 检查该时间段是否确实被该教师预约了 (避免误操作其他人的预约)
                cursor.execute("""
                    SELECT reservation_id FROM reservations 
                    WHERE slot_id = ? AND user_account = ? AND status = 'confirmed'
                """, (s_id, teacher_account))
                
                if cursor.fetchone():
                    # A. 取消教师的预约
                    cursor.execute("""
                        UPDATE reservations 
                        SET status = 'cancelled', cancel_time = ?
                        WHERE slot_id = ? AND user_account = ? AND status = 'confirmed'
                    """, (datetime.datetime.now(), s_id, teacher_account))
                    
                    # B. 重置场地状态
                    # 只有在确认是教师锁定的情况下才重置
                    cursor.execute("""
                        UPDATE time_slots 
                        SET current_reservations = 0 
                        WHERE slot_id = ?
                    """, (s_id,))
            
            conn.commit()
            return True, "课表移除成功，场地已释放"
            
        except Exception as e:
            conn.rollback()
            return False, f"操作失败: {str(e)}"
        finally:
            conn.close()

    def get_teacher_schedules(self, teacher_account):
        """获取教师的课表列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT cs.schedule_id, v.venue_name, c.court_name, cs.day_of_week, cs.start_time, cs.end_time
                FROM class_schedules cs
                JOIN courts c ON cs.court_id = c.court_id
                JOIN venues v ON c.venue_id = v.venue_id
                WHERE cs.teacher_account = ?
            """
            cursor.execute(sql, (teacher_account,))
            rows = cursor.fetchall()
            
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            res = []
            for row in rows:
                res.append({
                    "id": row[0],
                    "venue": row[1],
                    "court": row[2],
                    "day_str": weekdays[row[3]],
                    "time": f"{row[4]}-{row[5]}"
                })
            return True, res
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
