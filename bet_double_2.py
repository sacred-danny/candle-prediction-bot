import logging.config
import os
import threading
import time
from datetime import datetime
import json

import requests
from web3 import Web3

from library.prediction import Token

if not os.path.exists('logs'):
    os.mkdir('logs')
today = datetime.today()
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "default",
            "filename": f"logs/debug-{today.year}-{today.month}-{today.day}.log",
            "mode": "a",
            "encoding": "utf-8"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "console",
            "file"
        ]
    }
})

LOGGER = logging.getLogger()


class PredictionBot:
    def __init__(self):
        self.current_id = 0
        self.previous_id = 0
        self.default_bet_amount = 0.01
        self.bet_amount = 0.01
        self.bet_increase = 0

        self.wallet_balance = 0
        self.current_price = 0
        self.locked_price = 0

        self.bet_time = 7.5
        self.pending_time = 15

        self.wallet = None

        self.wallet_address = ""
        self.private_key = ""

        self.provider = ""

        self.current_round = None
        self.current_prize = 0
        self.current_up_amount = 0
        self.current_down_amount = 0
        self.current_round_end = 0
        self.max_bet_amount = 5

        self.bnb_price = 0

        self.current_up_rate = 1
        self.current_down_rate = 1

        self.start_mempool = False

        self.remain_time = 300

        self.contract_address = "0x18b2a687610328590bc8f2e5fedde3b582a49cda"
        self.usdt = "0x55d398326f99059ff775485246999027b3197955"
        self.bull_method = "0x57fb096f"
        self.bear_method = "0xaa6b873a"
        self.wallet_balance_limit_down = 0
        self.wallet_balance_limit_up = 100

        self.up_or_down = ''
        self.bet_id = 0

        self.current_up_amount_p = 0
        self.current_down_amount_p = 0

    def read_config(self):
        try:
            with open('config.json') as f:
                data = json.load(f)
                self.provider = data['provider_bsc']
                self.wallet_address = data['address']
                self.private_key = data['private_key']
                self.bet_time = data['bet_time']
                self.pending_time = data['pending_time']
                self.default_bet_amount = data['bet_amount']
                self.wallet_balance_limit_down = data['limit_down']
                self.wallet_balance_limit_up = data['limit_up']
                self.max_bet_amount = data['max_bet_amount']
                self.bet_increase = data['bet_increase']
                print('Read Config Success')
        except Exception as e:
            print(e)
            print("Config file read failed...")

    def wallet_connect(self):
        self.read_config()
        try:
            self.wallet = Token(
                address=self.usdt,
                provider=self.provider,
            )
            self.wallet.connect_wallet(self.wallet_address, self.private_key)
            if self.wallet.is_connected():
                print("Wallet Connect!")
            else:
                exit()
        except Exception as e:
            print('Wallet Not Connected')
            print(e)
            exit()

    def get_price(self):
        current_price = round(self.wallet.price() / 10 ** 8, 3)
        return current_price

    def get_balance(self):
        wallet_address = self.wallet.web3.toChecksumAddress(self.wallet_address.lower())
        wallet_balance = self.wallet.web3.eth.get_balance(wallet_address) / 10 ** 18
        return wallet_balance

    def get_price_loop(self):
        while True:
            self.current_price = self.get_price()
            time.sleep(0.1)

    def get_remain_time(self):
        now = datetime.now().timestamp()
        remain_time = self.current_round_end - now
        return remain_time

    def get_remain_time_loop(self):
        while True:
            self.remain_time = round(self.get_remain_time(), 1)
            time.sleep(0.1)

    def new_event(self, event):
        try:
            transaction = self.wallet.web3.eth.get_transaction(event)
        except Exception as e:
            return
        if transaction and transaction.to:
            if transaction.to.lower() == self.contract_address.lower():
                if transaction.input[:10] == self.bull_method:
                    self.current_up_amount_p += transaction.value
                elif transaction.input[:10] == self.bear_method:
                    self.current_down_amount_p += transaction.value

    def new_entries(self, event_filter):
        try:
            new_entries = event_filter.get_new_entries()
        except Exception as e:
            return
        for event in new_entries:
            if self.start_mempool:
                threading.Thread(target=self.new_event, args=(event, )).start()

    def mempool(self):
        event_filter = self.wallet.web3.eth.filter("pending")
        while True:
            threads = []
            self.current_up_amount_p = 0
            self.current_down_amount_p = 0
            while self.start_mempool:
                try:
                    thread = threading.Thread(target=self.new_entries, args=(event_filter, ))
                    threads.append(thread)
                    thread.start()
                except Exception as e:
                    pass
            if threads:
                for thread in threads:
                    thread.join()
                print('End pending')

    def bet_bull(self):
        try:
            tx = self.wallet.bet_bull(amount=int(self.bet_amount * 10 ** 18), id=self.current_id)
            return tx
        except Exception as err:
            print(err)
        return None

    def bet_bear(self):
        try:
            tx = self.wallet.bet_bear(amount=int(self.bet_amount * 10 ** 18), id=self.current_id)
            return tx
        except Exception as err:
            print(err)
        return None

    def claim(self, bet_id):
        try:
            if self.wallet.claimAble(int(bet_id)):
                tx = self.wallet.claim(id=int(bet_id))
                return tx
        except Exception as e:
            print(e)
        return None

    def get_bnb_price(self):
        try:
            res = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT')
            res_json = res.json()
            self.bnb_price = round(float(res_json['price']), 3)
        except Exception as e:
            pass

    def get_bnb_price_loop(self):
        while True:
            self.get_bnb_price()
            time.sleep(0.1)

    def start_prediction(self):
        threading.Thread(target=self.get_price_loop).start()
        threading.Thread(target=self.get_remain_time_loop).start()
        threading.Thread(target=self.mempool).start()
        self.wallet_balance = self.get_balance()
        self.current_price = self.get_price()
        print('wallet balance:', self.wallet_balance)

        win = True
        round_count = 0
        while True:
            self.current_id = self.wallet.get_current_Epoch()
            previous_round = self.wallet.get_round(self.current_id - 1)
            self.locked_price = previous_round[4] / 10 ** 8
            self.current_round_end = previous_round[3]
            round_count += 1
            time.sleep(5)
            price = self.current_price
            while self.remain_time > self.pending_time:
                if price != self.current_price:
                    price = self.current_price
                    print('\n', end=' ')
                price_diff = round(self.current_price - self.locked_price, 3)
                bet_amount = self.bet_amount if self.up_or_down != "" else ""
                print(f'\rID: {self.current_id - 1} | remain: {self.remain_time}, '
                      f'Locked: {self.locked_price} | '
                      f'Current: {self.current_price} | {price_diff}| '
                      f'Bet: {self.up_or_down} {bet_amount}', end=' ')
                time.sleep(1)

            if round_count % 2 == 1:
                self.start_mempool = True

                while self.remain_time >= self.bet_time:
                    time.sleep(0.01)

                if win:
                    self.bet_amount = self.default_bet_amount
                else:
                    if self.bet_id != 0:
                        self.bet_amount *= self.bet_increase

                current_round = self.wallet.get_round(self.current_id)
                self.current_prize = current_round[8]
                self.current_up_amount = current_round[9] + self.current_up_amount_p
                self.current_down_amount = current_round[10] + self.current_down_amount_p

                self.start_mempool = False
                prize = self.current_up_amount + self.current_down_amount
                my_bet_amount = int(self.bet_amount * 10 ** 18)
                prize_of_mine = prize + my_bet_amount
                up_rate = prize / self.current_up_amount
                down_rate = prize / self.current_down_amount
                up_rate_1 = prize_of_mine / (self.current_up_amount + my_bet_amount)
                down_rate_1 = prize_of_mine / (self.current_down_amount + my_bet_amount)
                print('\n', up_rate, down_rate, up_rate_1, down_rate_1)
                if up_rate_1 > down_rate_1:
                    bet_res = self.bet_bull()
                    if bet_res:
                        self.up_or_down = 'UP'
                        self.bet_id = self.current_id
                    else:
                        self.up_or_down = ""
                        self.bet_id = 0
                else:
                    bet_res = self.bet_bear()
                    if bet_res:
                        self.up_or_down = 'DOWN'
                        self.bet_id = self.current_id
                    else:
                        self.up_or_down = ""
                        self.bet_id = 0

                time.sleep(10)
                previous_round = self.wallet.get_round(self.current_id)
                try:
                    previous_up_rate = round(previous_round[8] / previous_round[9], 2)
                    previous_down_rate = round(previous_round[8] / previous_round[10], 2)
                    if self.bet_id != 0:
                        print(f"ID: {self.current_id}, Up: {previous_up_rate}, Down: {previous_down_rate}, Bet: {self.up_or_down}")
                        print(f"Tx: {bet_res}")
                    else:
                        print(f"ID: {self.current_id}, Up: {previous_up_rate}, Down: {previous_down_rate}, Bet: FAIL")
                except Exception as e:
                    pass
            print('\nwait 15 secs...')
            time.sleep(30)

            wallet_balance = self.get_balance()
            if self.bet_id != 0 and round_count % 2 == 0:
                if self.wallet.claimAble(self.bet_id):
                    claim_tx = self.claim(self.bet_id)
                    wallet_balance_1 = self.get_balance()
                    claim_amount = wallet_balance_1 - wallet_balance
                    LOGGER.info(f"Win ID: {self.current_id - 1}, Bet: {self.bet_amount}, Profit: {claim_amount - self.bet_amount}")
                    print(f"tx: {claim_tx}")
                    win = True
                else:
                    LOGGER.info(f"Lose ID: {self.current_id - 1}, Bet: {self.bet_amount}")
                    win = False
                self.up_or_down = ""


if __name__ == '__main__':
    bot = PredictionBot()
    bot.wallet_connect()
    bot.start_prediction()
