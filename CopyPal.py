from re import M
import sys
from tkinter.tix import Tree
import pyperclip as pc
import translators as tsl
from PySide6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QCheckBox, QPlainTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QRadioButton, QButtonGroup
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap, QGuiApplication

alfabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,!?:;'

engine_dic = {'Google': tsl.google, 'Bing': tsl.bing, '有道': tsl.youdao, '百度': tsl.baidu}


def process_break(text: str):
    text = text
    if '\r\n' in text or '\n' in text:
        break_count = text.count('\r\n')
        for i in range(break_count):
            break_index = text.find('\r\n')
            if break_index != 0 and text[break_index - 1] in alfabet:
                text = text[:break_index] + ' ' + text[break_index + 2:]
        break_count = text.count('\n')
        for i in range(break_count):
            break_index = text.find('\n')
            if break_index != 0 and text[break_index - 1] in alfabet:
                text = text[:break_index] + ' ' + text[break_index + 1:]
        text = text.replace('\r\n', '')
        text = text.replace('\n', '')
    return text


def process_num(text: str):
    text = text
    for i in range(10):
        text = text.replace(str(i), '')
    return text


class Translator(QThread):
    def __init__(self):
        super().__init__()

    def run(self, engine: str, is_en_to_cn: bool, text: str):
        translated_text = self.translate(engine, is_en_to_cn, text)
        return translated_text

    def translate(self, engine: str, is_en_to_cn: bool, text: str):
        if is_en_to_cn is True:
            translated_text = engine_dic[engine](text, from_language='en', to_language='zh-CN', if_use_cn_host=True)
        else:
            translated_text = engine_dic[engine](text, from_language='zh-CN', to_language='en', if_use_cn_host=True)
        return translated_text


class PicButton(QLabel):
    pressed_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)

    def mouseReleaseEvent(self, event):
        self.pressed_signal.emit()


class SideBar(QLabel):
    show_main_win = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(4, 60)

    def enterEvent(self, e):
        self.show_main_win.emit()


class TopBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title_label = QLabel('CopyPal |', self)
        self.exit_button = PicButton(self)

        self.set_ui()

    def set_ui(self):
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignCenter)
        self.exit_button.setPixmap(QPixmap('./img/exit.png'))

        main_box = QHBoxLayout()
        main_box.addStretch(1)
        main_box.addWidget(self.title_label)
        main_box.addWidget(self.exit_button)
        main_box.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_box)


class EngineBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.button_box = QButtonGroup(self)
        self.google = QRadioButton('Google', self)
        self.bing = QRadioButton('Bing', self)
        self.youdao = QRadioButton('有道', self)
        self.baidu = QRadioButton('百度', self)

        self.set_ui()
        self.init_widgets()

    def set_ui(self):
        main_box = QHBoxLayout()
        main_box.addStretch(1)
        main_box.addWidget(self.google)
        main_box.addWidget(self.bing)
        main_box.addWidget(self.youdao)
        main_box.addWidget(self.baidu)

        self.setLayout(main_box)

    def init_widgets(self):
        self.google.setChecked(True)

        self.button_box.addButton(self.google)
        self.button_box.addButton(self.bing)
        self.button_box.addButton(self.youdao)
        self.button_box.addButton(self.baidu)

        self.button_box.setExclusive(True)


class MainWin(QFrame):
    show_bar = Signal()
    copy_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.top_bar = TopBar(self)
        self.upper_title = QLabel('英文', self)
        self.lower_title = QLabel('中文', self)
        self.input_box = QPlainTextEdit(self)
        self.result_box = QPlainTextEdit(self)
        self.trans_btn = QPushButton('翻译', self)
        self.switch_btn = QPushButton('↑↓', self)
        self.trans_check = QCheckBox('复制翻译', self)
        self.del_break_check = QCheckBox('去除换行符', self)
        self.del_num_check = QCheckBox('去除数字', self)
        self.engine_bar = EngineBar(self)

        self.engine = 'Google'
        self.current_text = ''
        self.is_en_to_cn = True

        self.timer = QTimer(self)
        self.timer.start(200)
        self.timer.timeout.connect(self.cycle_task)

        self.translator = Translator()
        self.translator.start()

        self.set_ui()
        self.init_widgets()

    def set_ui(self):

        # 设置中间切换中英文布局
        middle_box = QHBoxLayout()
        middle_box.addWidget(self.lower_title, 0, Qt.AlignLeft)
        middle_box.addStretch(1)
        middle_box.addWidget(self.trans_btn)
        middle_box.addStretch(1)
        middle_box.addWidget(self.switch_btn)
        # 下方开关布局
        check_box = QHBoxLayout()
        check_box.addStretch(1)
        check_box.addWidget(self.trans_check)
        check_box.addWidget(self.del_break_check)
        check_box.addWidget(self.del_num_check)
        # 总体布局
        main_box = QVBoxLayout()
        main_box.addWidget(self.top_bar)
        main_box.addWidget(self.upper_title, 0, Qt.AlignLeft)
        main_box.addWidget(self.input_box, 1)
        main_box.addLayout(middle_box)
        main_box.addWidget(self.result_box, 1)
        main_box.addLayout(check_box)
        main_box.addWidget(self.engine_bar)
        self.setLayout(main_box)

        self.setFixedSize(350, 600)
        self.setContentsMargins(0, 0, 0, 0)

    def init_widgets(self):
        # 设置控件基本属性
        self.result_box.setReadOnly(True)
        self.trans_check.setChecked(True)
        self.del_break_check.setChecked(True)
        self.del_num_check.setChecked(False)

        self.trans_btn.clicked.connect(self.trans_input)

        self.switch_btn.setFixedWidth(30)
        self.switch_btn.clicked.connect(self.switch_en_cn)

        self.engine_bar.button_box.buttonClicked.connect(self.change_engine)

        self.del_break_check.stateChanged.connect(self.del_break_slot)
        self.del_num_check.stateChanged.connect(self.del_num_slot)

    def check_copy(self):
        temp_text = ''
        temp_text = pc.paste()

        if temp_text != self.current_text:
            self.current_text = temp_text
            return True
        else:
            return False

    def switch_en_cn(self):
        if self.is_en_to_cn is True:
            self.is_en_to_cn = False
            self.upper_title.setText('中文')
            self.lower_title.setText('英文')
        else:
            self.is_en_to_cn = True
            self.upper_title.setText('英文')
            self.lower_title.setText('中文')
        self.trans_input()

    def cycle_task(self):
        temp_text = pc.paste()
        if self.check_copy() is True and self.trans_check.isChecked() is True:
            self.current_text = temp_text
            if self.del_break_check.isChecked() is True:
                temp_text = process_break(temp_text)
            if self.del_num_check.isChecked() is True:
                temp_text = process_num(temp_text)
            self.input_box.setPlainText(temp_text)
            self.result_box.setPlainText(self.translator.run(self.engine, self.is_en_to_cn, temp_text))
            self.current_text
            self.copy_changed.emit()

    def trans_input(self):
        input_text = self.input_box.toPlainText()
        if self.del_break_check.isChecked() is True:
            input_text = process_break(input_text)
        if self.del_num_check.isChecked() is True:
            input_text = process_num(input_text)
        self.result_box.setPlainText(self.translator.run(self.engine, self.is_en_to_cn, input_text))

    def leaveEvent(self, e):
        self.show_bar.emit()

    def change_engine(self, button):
        engine_name = button.text()
        self.engine = engine_name
        self.trans_input()
    
    def del_break_slot(self, state: int):
        if state == 2:
            input_text = self.input_box.toPlainText()
            input_text = process_break(input_text)
            self.input_box.setPlainText(input_text)
            self.trans_input()

    def del_num_slot(self, state: int):
        if state == 2:
            input_text = self.input_box.toPlainText()
            input_text = process_num(input_text)
            self.input_box.setPlainText(input_text)
            self.trans_input()
 

class CopyPal(QWidget):
    main_qss = '''
        QFrame{
            background-color: white;
        }
        SideBar{
            background-color: rgb(78, 205, 196);
            border-radius: 2px;
        }
        QPlainTextEdit{
            font-size: 14px;
            border: 2px solid rgb(51, 51, 51);
        }
        QPushButton{
            font-size:14px;
        }
        QLabel{
            font-size: 16px;
        }
        MainWin{
            border: 2px solid rgb(51, 51, 51);
        }
        QPushButton {
            background-color: white;
            color: black;
            font-size: 16px;
            height: 25px;
            width: 100px;
            border: 2px solid rgb(51, 51, 51);
            }
        QPushButton:pressed {
            border: 0px;
            border-top: 2px solid gray;
            border-left: 2px solid gray;
            border-right: 1px solid gray;
            border-bottom: 1px solid gray;
            }
        QCheckBox{
            font-size: 14px;
        }
        QScrollBar:vertical{
            width: 8px;
            background: #DDD;
            padding-bottom: 8px;
        }
        QScrollBar::handle:vertical{
            background: rgb(51, 51, 51);
        }
        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical{
            width: 0;
            height: 0;
        }
        EngineBar {
            border-top: 2px solid rgb(51, 51, 51);
        }

    '''

    def __init__(self):
        super().__init__()

        self.side_bar = SideBar(self)
        self.main_win = MainWin(self)

        self.set_ui()
        self.init_widgets()

    def set_ui(self):
        self.main_win.hide()

        bar_box = QVBoxLayout()
        bar_box.addStretch(1)
        bar_box.addWidget(self.side_bar)
        bar_box.stretch(1)
        bar_box.setContentsMargins(0, 0, 0, 0)

        main_box = QHBoxLayout()
        main_box.addWidget(self.main_win)
        main_box.addLayout(bar_box)
        main_box.setSpacing(0)
        main_box.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_box)
        self.setStyleSheet(self.main_qss)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(4, 60)
        self.move(0, screen_hight / 2 - 30)

    def init_widgets(self):
        self.side_bar.show_main_win.connect(self.show_main_win)
        self.main_win.show_bar.connect(self.hide_main_win)
        self.main_win.copy_changed.connect(self.show_main_win)
        self.main_win.top_bar.exit_button.pressed_signal.connect(self.exit_app)

    def show_main_win(self):
        self.setFixedSize(350, 600)
        self.move(0, screen_hight / 2 - 300)
        self.side_bar.hide()
        self.main_win.show()

    def hide_main_win(self):
        self.setFixedSize(4, 60)
        self.move(0, screen_hight / 2 - 30)
        self.side_bar.show()
        self.main_win.hide()

    def exit_app(self):
        self.close()
        QApplication.instance().exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    screen_rect = QGuiApplication.primaryScreen().geometry()
    screen_width = screen_rect.width()
    screen_hight = screen_rect.height()
    screen_pixel_ratio = QGuiApplication.primaryScreen().devicePixelRatio()

    main_win = CopyPal()
    main_win.setWindowTitle('CopyPal')
    main_win.show()
    sys.exit(app.exec())
