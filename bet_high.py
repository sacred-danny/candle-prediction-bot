import logging.config
import os
import threading
import time
from datetime import datetime
import json

from web3 import Web3

from library.prediction import Token
if not os.path.exists('logs'):
    os.mkdir('logs')
today = datetime.today()
logging.config.dictConfig({
    "version":                  1,
    "disable_existing_loggers": False,
    "formatters":               {
        "default": {
            "format": "%(asctime)s %(message)s"
        }
    },
    "handlers":                 {
        "console": {
            "class":     "logging.StreamHandler",
            "level":     "INFO",
            "formatter": "default",
            "stream":    "ext://sys.stdout"
        },
        "file":    {
            "class":     "logging.FileHandler",
            "level":     "INFO",
            "formatter": "default",
            "filename":  f"logs/debug-{today.year}-{today.month}-{today.day}.log",
            "mode":      "a",
            "encoding":  "utf-8"
        }
    },
    "root":                     {
        "level":    "INFO",
        "handlers": [
            "console",
            "file"
        ]
    }
})

LOGGER = logging.getLogger()


class PredictionBot:
    def __init__(self):
        self.get_pending = False
        self.bet_time = 10
        self.bet_amount = 0.01
        self.wallet = None
        self.w3 = None
        self.w3_wss = None
        self.wallet_connected = False
        self.wallet_address = ""
        self.private_key = ""
        self.prediction_address = "0x516ffd7D1e0Ca40b1879935B2De87cb20Fc1124b"
        self.usdt = "0x55d398326f99059ff775485246999027b3197955"
        self.provider = ""
        self.provider_wss = ""
        self.current_round = None
        self.current_id = 1
        self.current_bet_id = 1
        self.current_up_rate = 1
        self.current_down_rate = 1
        self.current_price = 0
        self.up_amount = 0
        self.down_amount = 0
        self.price = 0
        self.current_balance = 0
        self.balance = 0
        self.bet_amount = 0
        self.bet_increase = 1
        self.pending_time = 10

        self.current_prize = 0

        self.remain_time = 300

        self.contract_addr = "0x18b2a687610328590bc8f2e5fedde3b582a49cda"
        self.bull_method = "0x57fb096f"
        self.bear_method = "0xaa6b873a"
        self.balance_limit_down = 0
        self.balance_limit_up = 100
        self.total_profit = 0

    def read_config(self):
        try:
            with open('config.json') as f:
                data = json.load(f)
                self.provider = data['provider_bsc']
                self.wallet_address = data['address']
                self.private_key = data['private_key']
                # self.sale_address = data['sale_address']
                self.bet_time = data['bet_time']
                self.pending_time = data['pending_time']
                self.bet_amount = data['bet_amount']
                self.bet_increase = data['bet_increase']
                self.balance_limit_down = data['limit_down']
                self.balance_limit_up = data['limit_up']
                print('Read Config Success')
        except Exception as e:
            print(e)
            print("Config file read failed...")

    def wallet_connect(self):
        self.wallet_connected = False
        self.read_config()
        try:
            self.wallet = Token(
                address=self.usdt,
                provider=self.provider,
                provider_wss=self.provider_wss
            )
            self.wallet.connect_wallet(self.wallet_address, self.private_key)
            if self.wallet.is_connected():
                self.wallet_connected = True
                print("Wallet Connect!")
                self.w3 = self.wallet.web3
                # threading.Thread(target=self.set_price).start()
                # threading.Thread(target=self.start_prediction).start()
                # self.set_balance()
        except Exception as e:
            self.wallet_connected = False
            print('Wallet Not Connected')
            print(e)

    def get_price(self):
        self.current_price = round(self.wallet.price() / 10 ** 8, 3)
        return self.current_price

    def get_balance(self):
        wallet_address = self.wallet.web3.toChecksumAddress(self.wallet_address.lower())
        self.current_balance = self.wallet.web3.eth.get_balance(wallet_address) / 10 ** 18
        return self.current_balance

    def get_round(self):
        first_id = self.get_id()
        self.current_round = self.wallet.get_round(id=first_id)
        # print(self.current_round)
        self.current_prize = self.current_round[8]
        self.up_amount = self.current_round[9]
        self.down_amount = self.current_round[10]
        if self.up_amount > 0:
            self.current_up_rate = self.current_prize / self.up_amount
        else:
            self.current_up_rate = 0

        if self.down_amount > 0:
            self.current_down_rate = self.current_prize / self.down_amount
        else:
            self.current_down_rate = 0

        # print(self.current_up_rate, self.current_down_rate)

    def get_id(self):
        self.current_id = self.wallet.get_current_Epoch()
        return self.current_id

    def get_remain_time(self):
        now = datetime.now().timestamp()
        self.remain_time = int(self.current_round[2] - now)
        return self.remain_time

    def set_amount(self, amount):
        self.bet_amount = amount

    def bet_bull(self):
        try:
            print(f"Bet Up! Amount : {self.bet_amount}")
            tx = self.wallet.bet_bull(amount=int(self.bet_amount * 10 ** 18), id=self.current_id)
            print('tx:', tx)
            return tx
        except Exception as err:
            print(err)
        return None

    def bet_bear(self):
        try:
            print(f"Bet Down! Amount : {self.bet_amount}")
            tx = self.wallet.bet_bear(amount=int(self.bet_amount * 10 ** 18), id=self.current_id)
            print('tx:', tx)
            return tx
        except Exception as err:
            print(err)
        return None

    def claim(self, bet_id):
        try:
            tx = self.wallet.claim(id=int(bet_id))
            print('tx:', tx)
        except Exception as e:
            print(e)

    def get_tx_count(self, up_count, down_count, up_down_arr):
        try:
            event_filter = self.w3.eth.filter(
                {"address": Web3.toChecksumAddress("0x18b2a687610328590bc8f2e5fedde3b582a49cda")})
            entries = event_filter.get_all_entries()
            for entry in entries:
                try:
                    transaction = self.w3.eth.get_transaction(entry.transactionHash)
                    tx_input = transaction.input.lower()
                    if tx_input[:10] == '0x57fb096f':  # bull
                        up_count += 1
                        up_down_arr.append(1)
                    if tx_input[:10] == '0xaa6b873a':  # bear
                        down_count += 1
                        up_down_arr.append(0)
                except Exception as err2:
                    print('tx error', err2)
        except Exception as err1:
            print('filter error', err1)
        return up_count, down_count, up_down_arr

    def new_event(self, event):
        try:
            transaction = self.w3.eth.get_transaction(event)
        except Exception as e:
            return
        if transaction and transaction.to:
            if transaction.to.lower() == self.contract_addr.lower():
                if transaction.input[:10] == self.bull_method:
                    self.up_amount += transaction.value
                elif transaction.input[:10] == self.bear_method:
                    self.down_amount += transaction.value

    def new_entries(self, event_filter):
        try:
            new_entries = event_filter.get_new_entries()
        except Exception as e:
            return
        for event in new_entries:
            if not self.get_pending:
                break
            threading.Thread(target=self.new_event, args=(event, )).start()

    def get_tx_pending(self):
        event_filter = self.w3.eth.filter("pending")
        while self.get_pending:
            try:
                threading.Thread(target=self.new_entries, args=(event_filter, )).start()
            except Exception as e:
                pass
        print('End get pending')

    def get_locked_price(self):
        before_round = self.wallet.get_round(id=self.current_id - 1)
        return before_round[4] / 10 ** 8

    def start_prediction(self):

        initial_balance = self.get_balance()
        self.set_amount(max(initial_balance / 100, 0.01))

        bet = False
        win = False
        up_or_down = ''

        bet_count = 0

        while True:
            self.get_round()
            self.get_remain_time()
            price_1 = 0
            locked_price = self.get_locked_price()

            current_balance = self.get_balance()
            if current_balance < self.balance_limit_down:
                LOGGER.info('Balance reached to down limit, exit')
                exit()
            if current_balance > self.balance_limit_up:
                LOGGER.info('Balance reached to up limit, exit')
                exit()

            while self.remain_time > self.bet_time:
                self.get_remain_time()
                self.get_price()

                if price_1 != 0 and price_1 != self.current_price:
                    print('\n', end=" ")
                print('\rremain time:', self.remain_time, "bet:", up_or_down, 'locked price:', locked_price, 'price:', self.current_price, end=" ")
                price_1 = self.current_price
                time.sleep(1)
            print('\n')

            self.get_round()
            self.get_pending = True
            thread = threading.Thread(target=self.get_tx_pending)
            thread.start()

            while self.remain_time >= 8:
                self.get_remain_time()
                time.sleep(0.1)

            if win:
                self.set_amount(max(current_balance / 100, 0.01))
            if self.up_amount == 0:
                self.up_amount = 1
            if self.down_amount == 0:
                self.down_amount = 1

            up_rate = (self.up_amount + self.down_amount) / self.up_amount
            down_rate = (self.up_amount + self.down_amount) / self.down_amount
            if up_rate > down_rate:
                self.get_pending = False
                up_or_down = 'up'
                res = self.bet_bull()
            else:
                self.get_pending = False
                up_or_down = 'down'
                res = self.bet_bear()
            print('up rate:', up_rate, "down rate:", down_rate)

            thread.join()
            print(self.current_id, self.current_prize, self.current_up_rate, self.current_down_rate)

            time.sleep(20)

            wallet_balance = self.get_balance()

            if bet:
                if self.wallet.claimAble(self.current_id - 1):
                    print(self.current_id - 1, 'Win')
                    self.claim(self.current_id - 1)
                    wallet_balance_1 = self.get_balance()
                    claim_amount = wallet_balance_1 - wallet_balance - self.bet_amount
                    self.total_profit += claim_amount
                    LOGGER.info(f"Win ID: {self.current_id - 1}, Bet: {self.bet_amount}, Profit: {claim_amount}, total: {self.total_profit}")
                    win = True
                else:
                    print(self.current_id - 1, 'Lost')
                    self.total_profit -= self.bet_amount
                    LOGGER.info(f"Lose ID: {self.current_id - 1}, Bet: {self.bet_amount}, total: {self.total_profit}")
                    win = False
            if res is None:
                bet = False
            else:
                bet = True


if __name__ == '__main__':
    bot = PredictionBot()
    bot.wallet_connect()
    # print(bot.get_price())
    # print(bot.get_balance())
    # bot.get_round()
    # print(bot.get_remain_time())
    bot.start_prediction()
