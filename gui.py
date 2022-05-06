# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'uiokjKSQ.ui'
##
## Created by: Qt User Interface Compiler version 5.14.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
import json
import sys
import threading
import time
from datetime import datetime

import requests
from PySide2 import QtWidgets
from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
                            QRect, QSize, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
                           QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap,
                           QRadialGradient)
from PySide2.QtWidgets import *

from library.prediction import Token


class PredictionBot(QObject):
    def __init__(self):
        super().__init__()
        self.bet_amount = 10000000
        self.provider = ""
        self.wallet_address = ""
        self.private_key = ""
        self.wallet = None

        self.usdt = "0x55d398326f99059ff775485246999027b3197955"
        self.prediction_address = "0x516ffd7D1e0Ca40b1879935B2De87cb20Fc1124b"
        self.contract_addr = "0x18b2a687610328590bc8f2e5fedde3b582a49cda"
        self.bull_method = "0x57fb096f"
        self.bear_method = "0xaa6b873a"

        self.current_id = 0
        self.wallet_balance = 0
        self.current_price = 0
        self.locked_price = 0
        self.bnb_price = 0
        self.remain_time = 300
        self.up_or_down = ''
        self.bet_id = 0
        self.bet_ids = []
        self.current_round_end = 0

        self.show_balance = False

        self.read_config()
        self.wallet_connect()

        self.qtWidget = QtWidgets
        self.MainWindow = QtWidgets.QMainWindow()
        self.setup_ui(self.MainWindow)
        self.retranslate_ui(self.MainWindow)
        self.setup_actions()

        self.MainWindow.show()

    def setup_ui(self, bet_bot):
        if bet_bot.objectName():
            bet_bot.setObjectName(u"bet_bot")
        bet_bot.setEnabled(True)
        bet_bot.resize(587, 453)
        self.centralwidget = QWidget(bet_bot)
        self.centralwidget.setObjectName(u"centralwidget")
        self.bet_up_c = QPushButton(self.centralwidget)
        self.bet_up_c.setObjectName(u"bet_up_c")
        self.bet_up_c.setGeometry(QRect(310, 350, 241, 41))
        self.bet_down_c = QPushButton(self.centralwidget)
        self.bet_down_c.setObjectName(u"bet_down_c")
        self.bet_down_c.setGeometry(QRect(310, 400, 241, 41))
        self.history_c = QTextEdit(self.centralwidget)
        self.history_c.setObjectName(u"history_c")
        self.history_c.setGeometry(QRect(10, 70, 281, 431))
        self.history_c.setReadOnly(True)
        self.bet_amount_c = QTextEdit(self.centralwidget)
        self.bet_amount_c.setObjectName(u"bet_amount_c")
        self.bet_amount_c.setGeometry(QRect(310, 310, 241, 31))
        self.bet_remain_c = QLabel(self.centralwidget)
        self.bet_remain_c.setObjectName(u"bet_remain_c")
        self.bet_remain_c.setGeometry(QRect(310, 60, 241, 31))
        font = QFont()
        font.setPointSize(12)
        self.bet_remain_c.setFont(font)
        self.locked_price_c = QLabel(self.centralwidget)
        self.locked_price_c.setObjectName(u"locked_price_c")
        self.locked_price_c.setGeometry(QRect(310, 100, 241, 31))
        self.locked_price_c.setFont(font)
        self.current_price_c = QLabel(self.centralwidget)
        self.current_price_c.setObjectName(u"current_price_c")
        self.current_price_c.setGeometry(QRect(310, 140, 241, 31))
        self.current_price_c.setFont(font)
        self.bnb_price_c = QLabel(self.centralwidget)
        self.bnb_price_c.setObjectName(u"bnb_price_c")
        self.bnb_price_c.setGeometry(QRect(310, 180, 241, 31))
        self.bnb_price_c.setFont(font)
        self.rate_up_c = QLabel(self.centralwidget)
        self.rate_up_c.setObjectName(u"rate_up_c")
        self.rate_up_c.setGeometry(QRect(310, 220, 241, 31))
        self.rate_up_c.setFont(font)
        self.rate_down_c = QLabel(self.centralwidget)
        self.rate_down_c.setObjectName(u"rate_down_c")
        self.rate_down_c.setGeometry(QRect(310, 260, 241, 31))
        self.rate_down_c.setFont(font)
        self.bet_id_c = QLabel(self.centralwidget)
        self.bet_id_c.setObjectName(u"bet_id_c")
        self.bet_id_c.setGeometry(QRect(310, 20, 241, 31))
        self.bet_id_c.setFont(font)
        self.wallet_c = QLabel(self.centralwidget)
        self.wallet_c.setObjectName(u"wallet_c")
        self.wallet_c.setGeometry(QRect(10, 20, 241, 31))
        self.wallet_c.setFont(font)
        self.wallet_show_c = QPushButton(self.centralwidget)
        self.wallet_show_c.setObjectName(u"wallet_show_c")
        self.wallet_show_c.setGeometry(QRect(252, 20, 40, 41))
        bet_bot.setCentralWidget(self.centralwidget)

        self.retranslate_ui(bet_bot)

        QMetaObject.connectSlotsByName(bet_bot)

    def retranslate_ui(self, bet_bot):
        bet_bot.setWindowTitle(QCoreApplication.translate("bet_bot", u"Prediction", None))
        self.bet_up_c.setText(QCoreApplication.translate("bet_bot", u"Bull", None))
        self.bet_down_c.setText(QCoreApplication.translate("bet_bot", u"Bear", None))
        self.bet_remain_c.setText(QCoreApplication.translate("bet_bot", u"Time: ", None))
        self.locked_price_c.setText(QCoreApplication.translate("bet_bot", u"Locked: ", None))
        self.current_price_c.setText(QCoreApplication.translate("bet_bot", u"Current: ", None))
        self.bnb_price_c.setText(QCoreApplication.translate("bet_bot", u"BNBUSDT: ", None))
        self.rate_up_c.setText(QCoreApplication.translate("bet_bot", u"Up: ", None))
        self.rate_down_c.setText(QCoreApplication.translate("bet_bot", u"Down: ", None))
        self.bet_id_c.setText(QCoreApplication.translate("bet_bot", u"ID: ", None))
        self.wallet_c.setText(QCoreApplication.translate("bet_bot", u"Balance: ", None))
        self.wallet_show_c.setText(QCoreApplication.translate("bet_bot", u"*", None))

    def setup_actions(self):
        self.bet_up_c.clicked.connect(self.start_bet_bull)
        self.bet_down_c.clicked.connect(self.start_bet_bear)
        self.wallet_show_c.clicked.connect(self.toggle_show_balance)

        self.bet_amount_c.setText("0.05")
        threading.Thread(target=self.get_round_loop).start()
        threading.Thread(target=self.get_price_loop).start()
        threading.Thread(target=self.get_bnb_price_loop).start()
        threading.Thread(target=self.get_remain_time_loop).start()
        threading.Thread(target=self.check_claimable).start()

    def read_config(self):
        try:
            with open('config.json') as f:
                data = json.load(f)
                self.provider = data['provider_bsc']
                self.wallet_address = data['address']
                self.private_key = data['private_key']
                # self.sale_address = data['sale_address']
                print('Read Config Success')
        except Exception as e:
            print(e)
            print("Config file read failed...")

    def wallet_connect(self):
        try:
            self.wallet = Token(
                address=self.usdt,
                provider=self.provider,
            )
            self.wallet.connect_wallet(self.wallet_address, self.private_key)
            if self.wallet.is_connected():
                print("Wallet Connected")
        except Exception as e:
            print('Wallet Not Connected')
            print(e)

    def toggle_show_balance(self):
        self.show_balance = not self.show_balance
        self.get_balance()

    def get_price(self):
        current_price = round(self.wallet.price() / 10 ** 8, 3)
        return current_price

    def get_bnb_price(self):
        try:
            res = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT')
            res_json = res.json()
            self.bnb_price = round(float(res_json['price']), 3)
        except Exception as e:
            pass

    def get_balance(self):
        wallet_address = self.wallet.web3.toChecksumAddress(self.wallet_address.lower())
        wallet_balance = self.wallet.web3.eth.get_balance(wallet_address) / 10 ** 18
        if self.show_balance:
            self.wallet_c.setText(f"Balance: {round(wallet_balance, 4)} BNB | ${round(wallet_balance * self.bnb_price, 1)}")
        else:
            self.wallet_c.setText(f"Balance: *** BNB | $***")
        return wallet_balance

    def get_remain_time(self):
        now = datetime.now().timestamp()
        remain_time = self.current_round_end - now
        return remain_time

    def get_id(self):
        self.current_id = self.wallet.get_current_Epoch()
        return self.current_id

    def get_round_loop(self):
        self.get_balance()
        while True:
            first_id = self.get_id()
            current_round = self.wallet.get_round(id=first_id - 1)
            self.current_round_end = current_round[3]
            current_prize = current_round[8]
            up_amount = current_round[9]
            down_amount = current_round[10]
            if up_amount > 0:
                current_up_rate = current_prize / up_amount
            else:
                current_up_rate = 0

            if down_amount > 0:
                current_down_rate = current_prize / down_amount
            else:
                current_down_rate = 0
            self.bet_id_c.setText(f"ID: {self.current_id - 1}")
            self.rate_up_c.setText(f"Up: {round(current_up_rate,2)}")
            self.rate_down_c.setText(f"Down: {round(current_down_rate, 2)}")
            self.locked_price = current_round[4] / 10 ** 8
            self.locked_price_c.setText(f"Locked: {round(self.locked_price, 3)}")
            time.sleep(0.5)

    def get_price_loop(self):
        while True:
            self.current_price = self.get_price()
            self.current_price_c.setText(f"Current: {round(self.current_price, 2)}|{round(self.current_price - self.locked_price, 2)}")
            time.sleep(0.5)

    def get_bnb_price_loop(self):
        while True:
            self.get_bnb_price()
            self.bnb_price_c.setText(f"BNBUSDT: {round(self.bnb_price, 2)}|{round(self.bnb_price - self.current_price, 2)}|{round(self.bnb_price - self.locked_price, 2)}")
            time.sleep(0.5)

    def get_remain_time_loop(self):
        while True:
            self.remain_time = self.get_remain_time()
            if self.remain_time > 0:
                self.bet_remain_c.setText(f"Time: {int(self.remain_time)}")
            else:
                self.bet_remain_c.setText(f"Time: Closed")
            time.sleep(0.5)

    def check_claimable(self):
        while True:
            if self.current_id > 0:
                for bet_id in range(self.current_id, self.current_id - 20, -1):
                    tx = self.claim(bet_id)
                    if tx:
                        self.history_c.append(f"{bet_id}| Claimed")

            time.sleep(10)

    def set_bet_amount(self):
        try:
            self.bet_amount = float(self.bet_amount_c.toPlainText())
        except Exception as e:
            print(e)
            self.bet_amount = 10000000

    def start_bet_bull(self):
        threading.Thread(target=self.bet_bull).start()

    def start_bet_bear(self):
        threading.Thread(target=self.bet_bear).start()

    def bet_bull(self):
        self.set_bet_amount()
        self.bet_up_c.setEnabled(False)
        tx = None
        self.bet_id = self.current_id
        if self.bet_id not in self.bet_ids:
            try:
                tx = self.wallet.bet_bull(amount=int(self.bet_amount * 10 ** 18), id=self.bet_id)
            except Exception as err:
                print(err)
            if tx:
                self.bet_ids.append(self.bet_id)
                self.history_c.append(f"{self.bet_id}| Bet Bull | {self.bet_amount}")
            else:
                self.history_c.append(f"{self.bet_id}| Bet Bull Failed | {self.bet_amount}")
        self.bet_up_c.setEnabled(True)
        self.get_balance()
        return tx

    def bet_bear(self):
        self.set_bet_amount()
        self.bet_down_c.setEnabled(False)
        tx = None
        self.bet_id = self.current_id
        if self.bet_id not in self.bet_ids:
            try:
                tx = self.wallet.bet_bear(amount=int(self.bet_amount * 10 ** 18), id=self.bet_id)
            except Exception as err:
                print(err)
            if tx:
                self.bet_ids.append(self.bet_id)
                self.history_c.append(f"{self.bet_id}| Bet Bear | {self.bet_amount}")
            else:
                self.history_c.append(f"{self.bet_id}| Bet Bear Failed | {self.bet_amount}")
        self.bet_down_c.setEnabled(True)
        self.get_balance()
        return tx

    def claim(self, bet_id):
        try:
            if self.wallet.claimAble(bet_id):
                tx = self.wallet.claim(id=int(bet_id))
                self.get_balance()
                return tx
        except Exception as e:
            print(e)
        return None


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = PredictionBot()
    sys.exit(app.exec_())
