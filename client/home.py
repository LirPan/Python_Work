import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, 
                             QComboBox, QDateEdit, QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy, QMessageBox, QStackedWidget)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QPalette

# Import LoginWindow and NetworkClient
try:
    from log_in import LoginWindow, NetworkClient
    from import_class import TeacherDashboard
    from admin import AdminWidget
except ImportError:
    from client.log_in import LoginWindow, NetworkClient
    from client.import_class import TeacherDashboard
    from client.admin import AdminWidget

class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.current_user = None # Track login state
        
        # Initialize Network Client and connect immediately
        self.network = NetworkClient()
        if self.network.connect():
            print("Connected to server successfully")
        else:
            print("Failed to connect to server (Guest Mode)")

        self.setWindowTitle("GoSport - Home")
        self.resize(1200, 800)
        
        # Main Container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #ffffff;")
        
        # Main Layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Navigation Bar
        self.setup_navbar()
        
        # 2. Content Area (Stacked Widget)
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)
        
        # 3. Initialize Home Page
        self.setup_home_page()

    def setup_home_page(self):
        self.home_page = QWidget()
        self.home_layout = QVBoxLayout(self.home_page)
        self.home_layout.setContentsMargins(0, 0, 0, 0)
        self.home_layout.setSpacing(0)
        
        # Hero Section (Title + Background Placeholder)
        self.setup_hero_section(self.home_layout)
        
        # Search Card (The floating box)
        self.setup_search_card(self.home_layout)
        
        # Spacer at the bottom
        self.home_layout.addStretch(1)
        
        self.content_stack.addWidget(self.home_page)

    def setup_navbar(self):
        """Top Navigation Bar"""
        navbar = QFrame()
        navbar.setFixedHeight(80)
        navbar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e5e7eb;
            }
        """)
        
        nav_layout = QHBoxLayout(navbar)
        # Reduced margins to move content to edges (20 left, 20 right)
        nav_layout.setContentsMargins(20, 0, 20, 0)
        
        # Logo: GoSport
        logo = QLabel("GoSport")
        logo.setStyleSheet("font-family: 'Segoe UI', sans-serif; font-size: 28px; font-weight: bold; color: #1f2937;")
        # Make "Sport" green to match the style roughly
        logo.setText('Go<span style="color: #84cc16;">Sport</span>')
        nav_layout.addWidget(logo)
        
        # Use stretch factor to control spacing distribution
        # Side spaces are larger (3) than spaces between links (1)
        nav_layout.addStretch(3)
        
        # Navigation Links
        self.nav_buttons = []
        nav_items = ["Home", "场馆", "公告/论坛", "校园赛事", "管理课表", "个人中心", "后台管理", "设置"]
        for i, item in enumerate(nav_items):
            btn = QPushButton(item)
            btn.setCursor(Qt.PointingHandCursor)
            # Connect click signal with item name
            btn.clicked.connect(lambda checked, b=btn, name=item: self.handle_nav_click(b, name))
            
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
            # Add small stretch between nav items
            if i < len(nav_items) - 1:
                nav_layout.addStretch(1)
        
        # Set initial active tab
        if self.nav_buttons:
            self.set_active_nav(self.nav_buttons[0])
            
        nav_layout.addStretch(3)
        
        # Auth Buttons
        login_btn = QPushButton("Login")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.open_login_window)
        login_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #1f2937;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #84cc16;
            }
        """)
        
        signin_btn = QPushButton("Sign up")
        signin_btn.setCursor(Qt.PointingHandCursor)
        signin_btn.clicked.connect(self.open_register_window)
        signin_btn.setFixedSize(100, 48)
        signin_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #84cc16;
                background-color: white;
                color: #84cc16;
                font-size:24px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #84cc16;
                color: white;
            }
        """)
        
        nav_layout.addWidget(login_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(signin_btn)
        
        self.main_layout.addWidget(navbar)

    def set_active_nav(self, active_btn):
        """Updates the style of navigation buttons to show the active one"""
        base_style = """
            QPushButton {
                border: none;
                border-bottom: 3px solid transparent;
                background: transparent;
                color: #4b5563;
                font-size: 18px;
                font-weight: 500;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #84cc16;
            }
        """
        
        active_style = """
            QPushButton {
                border: none;
                border-bottom: 3px solid #84cc16;
                background: transparent;
                color: #84cc16;
                font-size: 18px;
                font-weight: 700;
                padding: 5px 10px;
            }
        """
        
        for btn in self.nav_buttons:
            if btn == active_btn:
                btn.setStyleSheet(active_style)
            else:
                btn.setStyleSheet(base_style)

    def setup_hero_section(self, parent_layout):
        """Center Title and Background Area"""
        hero_frame = QFrame()
        hero_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Placeholder for background image
        hero_frame.setStyleSheet("""
            QFrame {
                background-color: #f9fafb; 
                /* You can add background-image here later */
                /* background-image: url('path/to/image.jpg'); */
                /* background-position: center; */
                /* background-repeat: no-repeat; */
            }
        """)
        
        hero_layout = QVBoxLayout(hero_frame)
        hero_layout.setAlignment(Qt.AlignCenter)
        hero_layout.setContentsMargins(0, 120, 0, 60)
        
        # Big Title
        title = QLabel("FIND YOUR <span style='color: #84cc16;'>SPORT VENUE</span>")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-family: 'Segoe UI', sans-serif; font-size: 48px; font-weight: 800; color: #1f2937;")
        
        subtitle = QLabel("We have the best courts for you.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-family: 'Segoe UI', sans-serif; font-size: 18px; color: #6b7280; margin-top: 10px;")
        
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        hero_layout.addStretch() # Push content up a bit
        
        # Add hero frame with stretch factor 2 to make it consume less vertical space (moving card up)
        parent_layout.addWidget(hero_frame, 2)

    def setup_search_card(self, parent_layout):
        """The floating search box at the bottom"""
        # Container to center the card
        container = QWidget()
        container_layout = QHBoxLayout(container)
        # Use margins to control width adaptively (150px from each side)
        container_layout.setContentsMargins(150, 0, 150, 0)
        
        # The Card itself
        card = QFrame()
        card.setFixedHeight(180) # Fixed height only
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #f3f4f6;
            }
        """)
        
        # Add Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)
        
        # Card Layout
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        
        # Inputs Row
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(40)
        
        # 1. Venue Selection
        venue_container = QWidget()
        venue_layout = QVBoxLayout(venue_container)
        venue_layout.setContentsMargins(0,0,0,0)
        venue_layout.setSpacing(5)
        
        venue_label = QLabel("Venue")
        venue_label.setStyleSheet("font-size: 20px; color: #4b5563;")
        
        self.venue_combo = QComboBox()
        self.venue_combo.addItems(["Select Venue", "Basketball Court", "Badminton Court", "Tennis Court", "Swimming Pool"])
        self.venue_combo.setFixedHeight(40)
        self.venue_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 5px 10px;
                color: #374151;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        
        venue_layout.addWidget(venue_label)
        venue_layout.addWidget(self.venue_combo)
        
        # 2. Date Selection
        date_container = QWidget()
        date_layout = QVBoxLayout(date_container)
        date_layout.setContentsMargins(0,0,0,0)
        date_layout.setSpacing(5)
        
        date_label = QLabel("Picking up date")
        date_label.setStyleSheet("font-size: 20px; color: #4b5563;")
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(40)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 5px 10px;
                color: #374151;
                background-color: white;
            }
            QDateEdit::drop-down {
                border: none;
            }
        """)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        
        # Add to inputs layout
        inputs_layout.addWidget(venue_container)
        inputs_layout.addWidget(date_container)
        
        card_layout.addLayout(inputs_layout)
        
        # Search Button (Black Bar)
        search_btn = QPushButton("FIND VENUE TIME SLOT")
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.clicked.connect(self.handle_search)
        search_btn.setFixedHeight(45)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f2937;
                color: white;
                font-weight: bold;
                font-size: 20px;
                border-radius: 4px;
                letter-spacing: 1px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #111827;
            }
        """)
        
        card_layout.addWidget(search_btn)
        
        # Add card to container
        container_layout.addWidget(card)
        
        parent_layout.addWidget(container)
        # Add stretch at the bottom to push the card up slightly (adaptive)
        self.main_layout.addStretch(1)

    def open_login_window(self):
        """Opens the login/register window"""
        # Pass the existing network connection to LoginWindow and callback
        self.login_window = LoginWindow(self.network, login_callback=self.on_login_success)
        self.login_window.show()

    def open_register_window(self):
        """Opens the register window directly"""
        self.login_window = LoginWindow(self.network, login_callback=self.on_login_success)
        self.login_window.show_register()
        self.login_window.show()

    def handle_search(self):
        """Handle search button click"""
        if not self.current_user:
            self.open_login_window()
            return
        
        # Logged in user (student or teacher)
        venue = self.venue_combo.currentText()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        
        if venue == "Select Venue":
            QMessageBox.warning(self, "提示", "请选择一个场馆")
            return
            
        QMessageBox.information(self, "提示", f"正在查询 {date} 的 {venue}...\n(功能开发中)")

    def on_login_success(self, user):
        """Callback when login is successful"""
        self.current_user = user
        print(f"User logged in: {user['name']} ({user['role']})")
        # You could update UI here (e.g. change Login button to User Profile)

    def on_logout_success(self):
        """Callback when user logs out from dashboard"""
        self.current_user = None
        print("User logged out")
        
        # Switch back to Home
        self.content_stack.setCurrentIndex(0)
        self.set_active_nav(self.nav_buttons[0])
        
        # Clean up dashboards
        if hasattr(self, 'teacher_page'):
            self.content_stack.removeWidget(self.teacher_page)
            del self.teacher_page
        
        if hasattr(self, 'admin_page'):
            self.content_stack.removeWidget(self.admin_page)
            del self.admin_page

    def handle_nav_click(self, btn, name):
        """Handle navigation button clicks with permission checks"""
        if name == "Home":
            self.content_stack.setCurrentIndex(0)
            self.set_active_nav(btn)
            return

        if name == "管理课表":
            if not self.current_user:
                self.open_login_window()
                return
            
            if self.current_user['role'] == 'student':
                QMessageBox.warning(self, "权限不足", "此为教师/管理员功能，你没有该权限！")
                return
            
            else:
                # Switch to Teacher Dashboard in Stack
                if not hasattr(self, 'teacher_page'):
                    self.teacher_page = TeacherDashboard(self.network, self.current_user, self.on_logout_success)
                    self.content_stack.addWidget(self.teacher_page)
                
                self.content_stack.setCurrentWidget(self.teacher_page)
                self.set_active_nav(btn)
                return
        
        elif name == "后台管理":
            if not self.current_user:
                self.open_login_window()
                return
            
            if self.current_user['role'] != 'admin':
                QMessageBox.warning(self, "权限不足", "此为管理员功能，你没有该权限！")
                return
            
            # Switch to Admin Page in Stack
            if not hasattr(self, 'admin_page'):
                self.admin_page = AdminWidget(self.network, self.current_user)
                self.content_stack.addWidget(self.admin_page)
            
            self.content_stack.setCurrentWidget(self.admin_page)
            self.set_active_nav(btn)
            return
        
        # For other tabs or if permission granted (though for "管理课表" we might open a new window instead of switching tab)
        # If we want to switch tab style:
        self.set_active_nav(btn)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = HomeWindow()
    window.show()
    sys.exit(app.exec_())
