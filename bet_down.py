import json
import logging.config
import os
import threading
import time
from datetime import datetime

from bet_lib import PredictionBot

if not os.path.exists('logs-high2'):
    os.mkdir('logs-high2')
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
            "filename": f"logs-high2/debug-{today.year}-{today.month}-{today.day}.log",
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


class PredictionBotDown(PredictionBot):
    def __init__(self):
        super().__init__()
        self.diff = 0.5
        self.read_config_2()

    def read_config_2(self):
        try:
            with open('config.json') as f:
                data = json.load(f)
                self.diff = data['diff']
                self.bet_amount = data['bet_amount']
        except Exception as e:
            print(e)
            print("Config file read failed...")

    def display(self):
        price = self.current_price
        while True:
            if self.current_id > 0:
                current_id = self.wallet.get_current_Epoch()
                previous_round = self.wallet.get_round(current_id - 1)
                self.locked_price = previous_round[4] / 10 ** 8
                self.current_round_end = previous_round[3]
                if price != self.current_price:
                    price = self.current_price
                    print('\n', end=' ')
                price_diff = round(self.current_price - self.locked_price, 3)
                price_diff1 = round(self.bnb_price - self.current_price, 3)
                bet_amount = self.bet_amount if self.up_or_down != "" else ""
                if self.remain_time > 0:
                    print(f'\rID: {current_id - 1} | remain: {self.remain_time}, '
                          f'Locked: {self.locked_price} | '
                          f'Current: {self.current_price} | {price_diff}| '
                          f'BNB: {self.bnb_price} | {price_diff1}| {round(price_diff1 + price_diff, 3)}| '
                          f'Bet: {self.up_or_down} {bet_amount}', end=' ')

                else:
                    print(f'\rID: {current_id - 1} | remain: Closing, '
                          f'Locked: {self.locked_price} | '
                          f'Current: {self.current_price} | {price_diff}| '
                          f'BNB: {self.bnb_price} | {price_diff1}| '
                          f'Bet: {self.up_or_down} {bet_amount}', end=' ')
                time.sleep(0.8)

    def start_prediction(self):
        self.wallet_balance = self.get_balance()
        print('wallet balance:', self.wallet_balance)

        threading.Thread(target=self.get_price_loop).start()
        threading.Thread(target=self.get_remain_time_loop).start()
        threading.Thread(target=self.display).start()
        threading.Thread(target=self.get_bnb_price_loop).start()

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
                # self.start_mempool = True

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

                if self.bet_amount > self.max_bet_amount:
                  self.bet_amount = self.default_bet_amount
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
    bot = PredictionBotDown()
    bot.wallet_connect("down")
    bot.start_prediction()
