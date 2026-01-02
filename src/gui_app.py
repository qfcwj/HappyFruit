import sys
import os
import datetime
import threading

# --- 路径修复 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    import keyboard
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                                 QPlainTextEdit, QLabel, QFrame, QLayout)
    from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPoint
    from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QMouseEvent
except ImportError as e:
    print(f"【严重错误】依赖包未安装: {e}")
    sys.exit(1)

try:
    from data_manager import save_record
    from parser import LogParser
    from config_manager import ConfigManager # <--- 新增导入
except ImportError:
    sys.exit(1)

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

class SignalBridge(QObject):
    show_window_signal = pyqtSignal()

class HappyLogApp(QWidget):
    def __init__(self):
        super().__init__()
        self.parser = LogParser()
        self.config_mgr = ConfigManager() # <--- 初始化配置管理器
        self.old_pos = None
        self.init_ui()
        self.setup_hotkey()

    def init_ui(self):
        self.setWindowTitle("HappyFruit")
        
        # 不再设置主窗口固定尺寸！self.setFixedSize(...) <--- 删掉这行
        # 我们只给高度一个建议值（虽然 SetFixedSize 策略下，高度也会由内容决定）
        # 但为了保证左侧输入框足够高，我们会在左侧容器上做限制

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 根布局
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        
        # 设置布局约束：让窗口大小永远等于内容大小
        # 这样右侧文字变长时，窗口会自动变宽；变短时自动收缩
        root_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        
        # 背景容器
        self.bg_frame = QFrame()
        self.bg_frame.setObjectName("BgFrame")
        root_layout.addWidget(self.bg_frame)

        # 内容布局
        content_layout = QHBoxLayout(self.bg_frame)
        content_layout.setContentsMargins(5, 5, 5, 5) # 5px 边框
        content_layout.setSpacing(0)

        # === 左侧区域 ===
        self.left_frame = QFrame()
        self.left_frame.setObjectName("LeftFrame")
        
        # 左侧定宽，左侧高度定死
        self.left_frame.setFixedWidth(460) 
        self.left_frame.setFixedHeight(340) 
        
        left_layout = QVBoxLayout(self.left_frame)
        left_layout.setContentsMargins(25, 25, 25, 15)
        left_layout.setSpacing(0)

        # 花花
        self.lbl_flower = QLabel("🌸 🌺 🌼 🌷 🌹 🌻 💐 🌸 🌺 🌼")
        self.lbl_flower.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_flower.setObjectName("FlowerLabel")
        
        # 提示语
        self.lbl_prompt = QLabel("快来写下你的最新一条成果吧！")
        self.lbl_prompt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.lbl_prompt.setObjectName("PromptLabel")
        self.lbl_prompt.setContentsMargins(0, 20, 0, 15) 

        # 输入框
        self.input_box = QPlainTextEdit()
        self.input_box.setPlaceholderText("在这里输入... \n(Enter 换行，Ctrl+S 保存)")
        self.input_box.setObjectName("InputBox")
        
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self.input_box)
        self.save_shortcut.activated.connect(self.submit_data)
        
        # 兔子
        self.lbl_rabbit = QLabel("🐇")
        self.lbl_rabbit.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.lbl_rabbit.setObjectName("RabbitLabel")

        left_layout.addWidget(self.lbl_flower)
        left_layout.addWidget(self.lbl_prompt)
        left_layout.addWidget(self.input_box, stretch=1)
        left_layout.addWidget(self.lbl_rabbit)

        # === 右侧区域 ===
        self.right_frame = QFrame()
        self.right_frame.setObjectName("RightFrame")
        
        # 右侧高度跟随左侧，宽度不设限（由文字撑开）
        self.right_frame.setFixedHeight(340)
        
        self.right_layout = QVBoxLayout(self.right_frame) # 改为成员变量以便刷新
        self.right_layout.setContentsMargins(20, 25, 20, 20)
        self.right_layout.setSpacing(5) 

        # 标题栏
        title_box = QHBoxLayout()
        lbl_leaf = QLabel("🍃") 
        lbl_leaf.setObjectName("LeafIcon")
        lbl_title = QLabel("语法备忘")
        lbl_title.setObjectName("HintTitle")
        title_box.addWidget(lbl_leaf)
        title_box.addWidget(lbl_title)
        title_box.addStretch() 
        self.right_layout.addLayout(title_box)
        self.right_layout.addSpacing(10)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setObjectName("HLine")
        self.right_layout.addWidget(line)
        self.right_layout.addSpacing(10)

        # 从 ConfigManager 获取提示内容
        self.refresh_hints()

        # # 旧的固定备忘内容+自动调整宽度设计
        # hints = [
        #     "## 学习 工作 游乐",
        #     "### 论文阅读 数据处理",
        #     "@ 统计 心理学 该死的量子计算",
        #     "$$ 可以备注所涉及资料来源以备后用！",
        #     "“” 留下一句将来的自己也许可以看了会心一笑的话吧"
        # ]
        
        # for h in hints:
        #     lbl = QLabel(h)
        #     lbl.setObjectName("HintLabel")
        #     # 【关键改动 5】取消自动换行，让文字撑开宽度
        #     # 如果你希望文字太长时自动换行而不撑开窗口，就把下面这行改为 True
        #     lbl.setWordWrap(False) 
        #     right_layout.addWidget(lbl)
        self.right_layout.addStretch()

        content_layout.addWidget(self.left_frame)
        content_layout.addWidget(self.right_frame)

        self.apply_styles()
        
        self.esc_action = QAction(self)
        self.esc_action.setShortcut("Esc")
        self.esc_action.triggered.connect(self.hide_window)
        self.addAction(self.esc_action)

    def refresh_hints(self):
        """刷新右侧提示文字（删除旧的，添加新的）"""
        # 清除旧的 HintLabel (保留标题和分割线)
        # 注意：Layout 中 item 的索引 0 是标题，1 是 spacing，2 是 line，3 是 spacing
        # 所以我们从 index 4 开始清除
        while self.right_layout.count() > 4:
            item = self.right_layout.takeAt(4)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem(): # 如果最后是 Stretch
                self.right_layout.removeItem(item)

        # 获取最新提示
        hints = self.config_mgr.get_display_hints()
        
        for h in hints:
            lbl = QLabel(h)
            lbl.setObjectName("HintLabel")
            lbl.setWordWrap(False) 
            self.right_layout.addWidget(lbl)
            
        self.right_layout.addStretch()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { 
                font-family: "Microsoft YaHei", "Segoe UI"; 
            }
            
            QFrame#BgFrame {
                /* 蓝绿渐变背景 */
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #81D4FA, stop:1 #A5D6A7);
                border-radius: 18px;
            }

            QFrame#LeftFrame { 
                background-color: white; 
                border-top-left-radius: 15px;
                border-bottom-left-radius: 15px;
            }
            
            QFrame#RightFrame { 
                background-color: #eeeeee;
                border-top-right-radius: 15px;
                border-bottom-right-radius: 15px;
            }

            QLabel#FlowerLabel { font-size: 18px; color: #ff80ab; }
            
            QLabel#PromptLabel { 
                font-size: 16px; 
                color: #4FC3F7; 
                font-weight: bold; 
                font-style: italic;
            }
            
            QLabel#RabbitLabel { font-size: 28px; }
            
            QLabel#LeafIcon { font-size: 20px; }
            QLabel#HintTitle { font-size: 16px; font-weight: bold; color: #666; } /* 字号加大 */
            QFrame#HLine { color: #ddd; }

            QPlainTextEdit {
                border: 2px dashed #B3E5FC;
                border-radius: 8px;
                padding: 10px;
                background-color: #F0F8FF;
                font-size: 16px; 
                color: #333;
                selection-background-color: #81D4FA;
            }
            QPlainTextEdit:focus {
                border: 2px solid #81D4FA;
                background-color: white;
            }

            QLabel#HintLabel { 
                color: #666; 
                font-size: 15px; /* 字号加大 */
                font-family: Consolas, "Microsoft YaHei"; 
                padding: 2px 5px 2px 1px; /* 边距 */
            }
        """)

    # --- 拖拽窗口逻辑 ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

    def setup_hotkey(self):
        self.bridge = SignalBridge()
        self.bridge.show_window_signal.connect(self.show_window_safe)
        def listen():
            log("开始监听快捷键 Ctrl+Space ...")
            try:
                keyboard.add_hotkey('ctrl+space', lambda: self.bridge.show_window_signal.emit())
                keyboard.wait()
            except Exception as e:
                log(f"快捷键监听失败: {e}")
            
        threading.Thread(target=listen, daemon=True).start()

    def show_window_safe(self):
        # 显示前先让布局重新计算一次大小，适应内容
        self.adjustSize()
        self.show()
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()
        if not self.isVisible():
            screen = QApplication.primaryScreen()
            if screen:
                rect = screen.availableGeometry()
                x = (rect.width() - self.width()) // 2
                y = (rect.height() - self.height()) // 2 - 120
                self.move(x, y)
        self.input_box.setPlainText("")
        self.input_box.setFocus()
        log("窗口已显示")

    def hide_window(self):
        self.hide()
        log("窗口已隐藏")

    def submit_data(self):
        text = self.input_box.toPlainText().strip()
        if text:
            # 1. 保存原始记录
            save_record(text)
            log(f"已保存: {text[:20]}...")
            
            # 2. 解析条目并更新配置
            try:
                # 解析 (时间戳用空，因为这里只为了提取元数据)
                entries = self.parser.parse(text, "")
                if entries:
                    # 【核心】调用 ConfigManager 更新配置
                    self.config_mgr.update_from_entry(entries)
                    # 刷新界面显示
                    self.refresh_hints()
                    
                    log(f"保存并解析成功，配置已检查更新")
            except Exception as e:
                log(f"解析/更新配置失败: {e}")
                
        self.hide_window()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = HappyLogApp()
    log("HappyFruit v5.0 (动态配置版) 已启动")
    sys.exit(app.exec())