import pathlib
import threading

import pkg_resources
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QPushButton, QHBoxLayout, QMessageBox, QFileDialog, QWidget, QLabel, QMainWindow,
    QVBoxLayout, QLineEdit, QGridLayout, QTextEdit
)
import sys
from mt3.inference import InferenceHandler
class WaitDialog(QDialog):
    def __init__(self, parent=None,stopSignal=None):
        super().__init__(parent)
        self.stopSignal = stopSignal
        self.setWindowTitle('转换中,请稍候...')
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint)
        layout = QVBoxLayout()
        self.button_stop = QPushButton('停止', self)

        layout.addWidget(self.button_stop)
        self.button_stop.clicked.connect(self.stopProc)

        self.setLayout(layout)
        self.setFixedSize(200, 100)
    def stopProc(self):
        self.stopSignal.emit()
        self.accept()
class WorkerThread(QThread):
    finished = pyqtSignal()  # 自定义信号，用于传递结果
    result = pyqtSignal(str)  # 自定义信号，用于传递结果
    stopSignal = pyqtSignal()
    def __init__(self, fileDialog):
        super().__init__()
        self.fileDialog = fileDialog
        resource_path = pkg_resources.resource_filename('mt3', 'pretrained/')
        self.handler = InferenceHandler(resource_path)
        self.stopSignal.connect(self.handler.stopProc)

    def run(self):
        filename = self.fileDialog.selected_file_edit.text().split('/')[-1].split('.')[0]
        outpath = self.fileDialog.selected_folder_edit.text()+f'/{filename}.mid'

        fin = self.handler.inference(self.fileDialog.selected_file_edit.text(), outpath,text_edit=self.fileDialog.full_window_edit)
        self.fileDialog.convert_button.setEnabled(True)
        if fin != False:
            self.result.emit('转换完成:'+outpath)  # 发射信号，将结果传递给主线程
        else:
            self.result.emit('转换终止')
        self.finished.emit()  # 发射信号，将结果传递给主线程

class FileDialog(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('MTT')

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()
        # 创建水平布局用于放置文件路径编辑框和按钮
        file_layout = QHBoxLayout()
        homedir = str(pathlib.Path.home())
        self.selected_file_edit = QLineEdit(homedir+'/Documents/Martian Love - In Motion.mp3', self)
        self.selected_file_edit.setReadOnly(True)  # 设置为只读
        file_layout.addWidget(self.selected_file_edit)
        self.button_file = QPushButton('选择音频路径', self)

        file_layout.addWidget(self.button_file)
        self.button_file.clicked.connect(self.showFileDialog)

        #输出文件夹选择
        folder_layout = QHBoxLayout()

        self.selected_folder_edit = QLineEdit(homedir+'/Documents/', self)
        self.selected_folder_edit.setReadOnly(True)  # 设置为只读
        folder_layout.addWidget(self.selected_folder_edit)

        self.button_folder = QPushButton('选择输出路径', self)
        self.button_folder.clicked.connect(self.showFolderDialog)
        folder_layout.addWidget(self.button_folder)

        # 将文件路径的水平布局和文件夹选择的水平布局添加到主垂直布局中
        layout.addLayout(file_layout)
        layout.addLayout(folder_layout)

        # 将文件路径的水平布局和文件夹选择的水平布局添加到主垂直布局中
        layout.addLayout(file_layout)
        layout.addLayout(folder_layout)

        # 创建一个新的垂直布局用于"转换"按钮
        convert_layout = QVBoxLayout()

        # 创建独占两行的按钮
        self.convert_button = QPushButton('转换', self)
        self.convert_button.setStyleSheet('font-size: 18px;')  # 增加按钮的字体大小

        self.convert_button.clicked.connect(self.convert)
        convert_layout.addWidget(self.convert_button)
        # 添加一个占位符以实现按钮独占两行的效果
        convert_layout.addStretch(1)
        layout.addLayout(convert_layout)


        # 创建多行文本编辑框用于填充剩余的窗口空间
        self.full_window_edit = QTextEdit('', self)
        self.full_window_edit.setReadOnly(True)  # 设置为只读

        layout.addWidget(self.full_window_edit, 1)  # 使用伸缩因子填充剩余空间


        self.central_widget.setLayout(layout)

    def showFileDialog(self):


        file_dialog = QFileDialog()

        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)  # 允许选择现有文件
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)  # 显示详细信息
        file_dialog.setDirectory(str(pathlib.Path.home()))
        file_names, _ = file_dialog.getOpenFileNames(self, '音频文件选择', '', 'All Files (*)')
        if file_names:
            selected_file = file_names[0]
            self.selected_file_edit.setText(selected_file)
            self.full_window_edit.setPlainText('音频文件选择:'+selected_file)
    def showFolderDialog(self):


        folder_dialog = QFileDialog()

        folder_dialog.setFileMode(QFileDialog.FileMode.Directory)  # 允许选择文件夹
        folder_dialog.setDirectory(str(pathlib.Path.home()))
        folder_path = folder_dialog.getExistingDirectory(self, '文件夹选择', '')
        if folder_path:
            self.selected_folder_edit.setText(folder_path)
            self.full_window_edit.setPlainText('文件夹选择:'+folder_path)
    def convert(self):
        # 禁用按钮
        self.convert_button.setEnabled(False)
        # 创建并启动后台线程执行耗时操作
        self.worker_thread = WorkerThread(self)


        # 创建等待框
        wait_dialog = WaitDialog(self,self.worker_thread.stopSignal)
        wait_dialog.setModal(True)  # 将对话框设置为模态
        self.full_window_edit.setPlainText('')

        self.worker_thread.result.connect(self.onOperationFinished)  # 连接信号到槽函数
        self.worker_thread.finished.connect(wait_dialog.accept)  # 连接信号到对话框的关闭

        # self.worker_thread.finished.connect(self.convert_button.setEnabled)  # 启用按钮
        self.worker_thread.start()
        # 显示等待框
        wait_dialog.exec()
    def onOperationFinished(self,result):
        # 子线程操作完成后的回调函数
        self.full_window_edit.setPlainText(result)
        self.convert_button.setEnabled(True)
def main():
    app = QApplication(sys.argv)
    resource_path = pkg_resources.resource_filename('mt3', 'pretrained/')
    QApplication.setWindowIcon(QtGui.QIcon(resource_path+'/logo.png'))
    fdialog = FileDialog()
    fdialog.setWindowIcon(QtGui.QIcon(resource_path+'/logo.png'))
    fdialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()





