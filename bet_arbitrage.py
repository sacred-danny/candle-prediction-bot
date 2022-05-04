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


class PredictionBotArbitrage(PredictionBot):
    def __init__(self):
        super().__init__()
        self.diff = 0.7
        self.read_my_config()

    def read_my_config(self):
        try:
            with open('config.json') as f:
                data = json.load(f)
                self.diff = data['diff']
                self.bet_amount = data['arbitrage_bet_amount']
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

        self.current_price = self.get_price()
        bet_count = 0
        claim_count = 0
        bet_ids = []

        while True:
            self.current_id = self.wallet.get_current_Epoch()
            previous_round = self.wallet.get_round(self.current_id - 1)
            self.locked_price = previous_round[4] / 10 ** 8
            self.current_round_end = previous_round[3]

            for bet_id in range(self.current_id-1, self.current_id - 100, -1):
                wallet_balance = self.wallet_balance
                claim_res = self.claim(bet_id)
                if claim_res:
                    claim_count += 1
                    self.wallet_balance = self.get_balance()
                    profit = self.wallet_balance - wallet_balance
                    print(f'Win ID: {bet_id} | profit: {profit} | ({bet_count}/{claim_count})')
                    if bet_id in bet_ids:
                        bet_ids.remove(bet_id)
                elif bet_id in bet_ids:
                    print(f'Lose ID: {bet_id} | lost: {self.bet_amount} | ({bet_count}/{claim_count})')

            time.sleep(10)

            if self.remain_time < self.bet_time:
                continue
            else:
                while self.remain_time > self.bet_time:
                    time.sleep(1)
            # current_round = self.wallet.get_round(self.current_id)
            # self.current_prize = current_round[8]
            # self.current_up_amount = current_round[9]
            # self.current_down_amount = current_round[10]

            # diff1 = self.current_price - self.locked_price
            print('\nBet')
            arbitrage = self.bnb_price - self.current_price

            if abs(arbitrage) > self.diff:
                if arbitrage > 0:
                    bet_res = self.bet_bull()
                    self.up_or_down = "Up"
                else:
                    bet_res = self.bet_bear()
                    self.up_or_down = "Down"

                if bet_res:
                    bet_count += 1
                    self.bet_id = self.current_id
                    bet_ids.append(self.bet_id)
                    print(bet_res)
                else:
                    self.bet_id = 0
                    self.up_or_down = ""
            else:
                self.bet_id = 0
                self.up_or_down = ""
            time.sleep(50)


if __name__ == '__main__':
    bot = PredictionBotArbitrage()
    bot.wallet_connect("arbitrage")
    bot.start_prediction()
