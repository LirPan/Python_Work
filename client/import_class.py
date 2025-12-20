from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QTextEdit, 
                             QMessageBox, QFrame, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt
import json

class TeacherDashboard(QWidget):
    def __init__(self, network_client, user_info, on_logout):
        super().__init__()
        self.network = network_client
        self.user = user_info
        self.on_logout = on_logout
        
        self.setWindowTitle(f"教师管理系统 - {self.user['name']}")
        self.resize(600, 500)
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        header_layout = QHBoxLayout(header_frame)
        
        welcome_label = QLabel(f"欢迎, {self.user['name']} 老师")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        header_layout.addWidget(welcome_label)
        
        header_layout.addStretch()
        
        logout_btn = QPushButton("注销")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5252; 
                color: white; 
                border: none; 
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff1744;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)
        
        main_layout.addWidget(header_frame)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addLayout(content_layout)

        # Section: Add Recurring Schedule
        title_label = QLabel("添加长期课表 (自动锁定未来4个月)")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        content_layout.addWidget(title_label)

        form_group = QGroupBox("课表信息")
        form_layout = QGridLayout()
        form_group.setLayout(form_layout)

        # Venue ID
        form_layout.addWidget(QLabel("场馆ID:"), 0, 0)
        self.entry_venue_id = QLineEdit()
        form_layout.addWidget(self.entry_venue_id, 0, 1)
        form_layout.addWidget(QLabel("(例如: 1)"), 0, 2)

        # Day of Week
        form_layout.addWidget(QLabel("星期:"), 1, 0)
        self.combo_day = QComboBox()
        self.combo_day.addItems(["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        form_layout.addWidget(self.combo_day, 1, 1)

        # Time Slot
        form_layout.addWidget(QLabel("开始时间:"), 2, 0)
        self.entry_start_time = QLineEdit("08:00")
        form_layout.addWidget(self.entry_start_time, 2, 1)
        form_layout.addWidget(QLabel("(格式 HH:MM)"), 2, 2)

        form_layout.addWidget(QLabel("结束时间:"), 3, 0)
        self.entry_end_time = QLineEdit("10:00")
        form_layout.addWidget(self.entry_end_time, 3, 1)

        # Submit Button
        submit_btn = QPushButton("添加课表")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                border: none; 
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        submit_btn.clicked.connect(self.add_schedule)
        form_layout.addWidget(submit_btn, 4, 1)

        content_layout.addWidget(form_group)

        # Section: Status/Logs
        log_label = QLabel("操作日志")
        log_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-top: 20px;")
        content_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd;")
        content_layout.addWidget(self.log_text)

    def log(self, message):
        self.log_text.append(message)
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_schedule(self):
        venue_id = self.entry_venue_id.text().strip()
        day_str = self.combo_day.currentText()
        start_time = self.entry_start_time.text().strip()
        end_time = self.entry_end_time.text().strip()

        if not venue_id or not start_time or not end_time:
            QMessageBox.warning(self, "输入错误", "请填写完整信息")
            return

        # Map day string to integer (0-6)
        day_map = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}
        day_of_week = day_map.get(day_str, 0)

        # Construct request data
        data = {
            "teacher_account": self.user['account'],
            "venue_id": int(venue_id),
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time
        }

        self.log(f"正在请求添加课表: {day_str} {start_time}-{end_time} @ 场馆{venue_id}...")
        
        try:
            response = self.network.send_request("add_schedule", data)
            
            if response.get("status") == "success":
                self.log("✅ 添加成功! 未来4个月的该时段已自动锁定。")
                QMessageBox.information(self, "成功", "课表添加成功！\n系统已自动为您锁定未来4个月的对应时段。")
            else:
                error_msg = response.get("message", "未知错误")
                self.log(f"❌ 添加失败: {error_msg}")
                QMessageBox.critical(self, "失败", f"添加失败: {error_msg}")
        except Exception as e:
            self.log(f"❌ 通信错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"通信错误: {str(e)}")

    def logout(self):
        reply = QMessageBox.question(self, "注销", "确定要退出登录吗?", 
                                     QMessageBox.Yes | QMessageBox.No, 
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            # self.close() # Embedded mode: let parent handle visibility
            self.on_logout()
