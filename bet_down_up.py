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


class PredictionBotRate(PredictionBot):
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

        self.current_price = self.get_price()
        bet_count = 0
        claim_count = 0
        bet_ids = []

        bet_odd = 0
        bet_even = 0
        bet_odd_amount = self.default_bet_amount
        bet_even_amount = self.default_bet_amount
        bet_amount = self.default_bet_amount

        bet_odd_win = True
        bet_even_win = True

        while True:
            self.current_id = self.wallet.get_current_Epoch()
            previous_round = self.wallet.get_round(self.current_id - 1)
            self.locked_price = previous_round[4] / 10 ** 8
            self.current_round_end = previous_round[3]

            time.sleep(10)

            if self.remain_time < self.bet_time:
                continue
            else:
                while self.remain_time > self.bet_time:
                    time.sleep(0.1)

            current_round = self.wallet.get_round(self.current_id)
            self.current_prize = current_round[8]
            self.current_up_amount = current_round[9]
            self.current_down_amount = current_round[10]
            bet_count += 1
            if bet_count % 2 == 1:
                bet_to = 1
            else:
                bet_to = 2
            if bet_to == 1:
                if bet_odd != 0:
                    bet_amount = bet_odd_amount
                    if bet_odd_win:
                        bet_amount = self.default_bet_amount
                    else:
                        bet_amount *= self.bet_increase
            else:
                if bet_even != 0:
                    bet_amount = bet_even_amount
                    if bet_even_win:
                        bet_amount = self.default_bet_amount
                    else:
                        bet_amount *= self.bet_increase

            self.bet_amount = bet_amount
            if self.bet_amount > self.max_bet_amount:
              self.bet_amount = self.default_bet_amount
            if  bet_to == 2:
                print("BULL BETTING!")
                bet_res = self.bet_bull()
            else:
                print("BEAR BETTING!")
                bet_res = self.bet_bear()
            if bet_res:
                print(f"Bet ID: {self.current_id} Amount: {bet_amount}")
                if bet_to == 1:
                    bet_odd = self.current_id
                    bet_odd_amount = bet_amount
                else:
                    bet_even = self.current_id
                    bet_even_amount = bet_amount
            else:
                print(f"Bet Failed ID: {self.current_id} Amount: {bet_amount}")
                if bet_to == 1:
                    bet_odd = 0
                else:
                    bet_even = 0

            time.sleep(50)
            wallet_balance = self.get_balance()

            if bet_to == 1 and bet_even != 0:
                claim_res = self.claim(bet_even)
                if claim_res:
                    wallet_balance_1 = self.get_balance()
                    print(f'Win Even ID: {bet_even} Amount:{bet_even_amount} Profit: {round(wallet_balance_1 - wallet_balance, 3)}')
                    bet_even_win = True
                else:
                    print(f'Lose Even ID: {bet_even} Amount:{bet_even_amount}')
                    bet_even_win = False
            if bet_to == 2 and bet_odd != 0:
                claim_res = self.claim(bet_odd)
                if claim_res:
                    wallet_balance_1 = self.get_balance()
                    print(f'Win Odd ID: {bet_odd} Amount:{bet_odd_amount} Profit: {round(wallet_balance_1 - wallet_balance, 3)}')
                    bet_odd_win = True
                else:
                    print(f'Lose Odd ID: {bet_odd} Amount:{bet_odd_amount}')
                    bet_odd_win = False


if __name__ == '__main__':
    bot = PredictionBotRate()
    bot.wallet_connect("down_up")
    bot.start_prediction()
