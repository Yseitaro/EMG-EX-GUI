import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressBar,QPushButton,QVBoxLayout,QWidget,QSizePolicy,QHBoxLayout,QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5 import QtTest
import time
from EMGsignal import EMGsignal
from reader_chart import RaderChartWindow
from progress import Progress
from picture import ImageSlider
from src.delsys import DataHandle
import pandas as pd
from plot_emg import PlotWindow
import shutil
import os

class Intermittently_Experiment_reader(QWidget):
    closed = pyqtSignal()
    """メインウィンドウ"""
    def __init__(self,ch,class_n,trial_n,sec_mes,sec_class_break,parent=None):
        super().__init__(parent)
        shutil.rmtree('./data/raw/')
        os.mkdir('./data/raw')
        self.ch = ch
        # 試行数とクラス数の数値を定義
        self.trial_n = trial_n
        self.class_n = class_n
        self.sec_mes = sec_mes
        self.sec_class_break = sec_class_break
        self.dh = DataHandle(self.ch)
        self.dh.initialize_delsys()
        # ラベルの初期化
        self.trial_ = 0
        self.class_ = 0
        # 現在の試行数とクラス数を求めるための変数
        self.tmp = 0    
        self.EMGsinal_object = EMGsignal(self.dh,self.trial_n,self.class_n,self.sec_class_break,self.sec_mes)
        self.initUI()
        self.EMGsinal_object.timer.start()
        # 初期はBreakからスタートする
        self.EMGsinal_object.tick.connect(self.progress.handleTimer)
        # レーダーチャートの更新
        self.EMGsinal_object.array_signal.connect(self.reader_chart.updatePaintEvent)
        # EMGデータの保存
        self.EMGsinal_object.array_signal.connect(self.save_emg)
        # EMGのプロット
        # self.EMGsinal_object.array_signal.connect(self.plot_emg.update)
        # プログレスバーの更新
        self.EMGsinal_object.finished_class.connect(self.progress.update_display)
        # ラベルの更新
        self.EMGsinal_object.finished_class.connect(self.update_label)
        # 画像の更新
        self.EMGsinal_object.finished_class.connect(self.image.next_image)
        # Breakの表示
        self.EMGsinal_object.finished_class.connect(self.display_break)
        # 全ての試行が終了したとき
        self.EMGsinal_object.finished_all_trial.connect(self.close)


    
    def initUI(self):
        self.setWindowTitle("計測中")
        self.setGeometry(0,0,1920,1080)        

        self.reader_chart = RaderChartWindow(self.dh,self.ch,self)
        self.progress = Progress(self.sec_mes,self.sec_class_break,self)
        image_path = [f'./images/motion{c+1}' for c in range(self.class_n)]
        self.image = ImageSlider(image_path,self)
        self.Breaking_label = QLabel(self)
        self.Class_label = QLabel(self)
        self.display_break(False)
       

        self.progress.setGeometry(230, 900, 1500, 1000)
        self.Breaking_label.setGeometry(950, 300, 900, 300)
        self.Class_label.setGeometry(160, 70, 800, 200)
        self.reader_chart.setGeometry(780, 10, 900, 900)
        self.image.setGeometry(350, 10, 900, 900)

        
    def closeEvent(self, event):
        # ウィンドウが閉じられたときにシグナルを送信
        self.EMGsinal_object.timer.stop()
        self.dh.stop_delsys()
        self.closed.emit()
        event.accept()
        
    def save_emg(self,rawEMG):
        pd.DataFrame(rawEMG).to_csv(f'./data/raw/trial{self.trial_}class{self.class_}.csv', mode='a', index = False, header=False)
    
    def update_label(self,flag):
        if flag:
            self.class_ = ((self.tmp) % (self.class_n)) + 1
            self.trial_ = 1 + (self.tmp//self.class_n)
            self.tmp += 1

            print(f'trial{self.trial_}')


    
    def display_break(self,flag):
        if flag == False:
            self.reader_chart.hide()
            self.Breaking_label.show()
            font_rest = QFont()
            font_image = QFont()
            font_rest.setPointSize(100)
            font_image.setPointSize(50)
            self.Breaking_label.setFont(font_rest)
            self.Class_label.setFont(font_image)
            self.Breaking_label.setText('Breaking')
            self.Class_label.setText('Next Motion')
            self.Class_label.setAlignment(Qt.AlignCenter)
        else:
            self.reader_chart.show()
            self.Breaking_label.hide()
            font = QFont()
            font.setPointSize(50)
            self.Class_label.setFont(font)
            self.Class_label.setText(f'Class{self.class_}')
    
    def closeEvent(self, event):
        # ウィンドウが閉じられたときにシグナルを送信
        print('before closed')
        self.EMGsinal_object.timer.stop()
        self.dh.stop_delsys()
        self.closed.emit()
        event.accept()
        print('after close')
           
    