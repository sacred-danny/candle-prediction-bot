import requests
from web3 import Web3
import os
import json
from functools import wraps


class Token:
    # bnb
    ETH_ADDRESS = Web3.toChecksumAddress('0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c')
    USDT_ADDRESS = Web3.toChecksumAddress('0x55d398326f99059ff775485246999027b3197955')
    MAX_AMOUNT = int('0x' + 'f' * 64, 16)

    def __init__(self, address, provider=None, provider_wss="wss://bsc-ws-node.nariox.org:443"):
        self.address = Web3.toChecksumAddress(address)
        self.provider = os.environ['PROVIDER'] if not provider else provider
        self.provider_wss = provider_wss
        adapter = requests.adapters.HTTPAdapter(pool_connections=1000, pool_maxsize=1000)
        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        self.i = 0
        self.j = 0
        self.web3 = Web3(Web3.HTTPProvider(self.provider, session=session))
        self.web3_wss = Web3(Web3.WebsocketProvider(self.provider_wss))
        self.wallet_address = None

        # bnb
        self.router = self.web3.eth.contract(
            address=Web3.toChecksumAddress('0x10ed43c718714eb63d5aa57b78b54704e256024e'),
            abi=json.load(open("library/abi_files_bnb/" + "router.abi")))
        self.prediction_router = self.web3.eth.contract(
            address=Web3.toChecksumAddress('0xF9120F473a3B3Ef24855Cd172cf741726E36eBF0'),
            abi=json.load(open("library/abi_files_bnb/" + "prediction.abi")))
        self.oracle_router = self.web3.eth.contract(
            address=Web3.toChecksumAddress('0xD276fCF34D54A926773c399eBAa772C12ec394aC'),
            abi=json.load(open("library/abi_files_bnb/" + "oracle.abi")))
        self.erc20_abi = json.load(
            open("library/abi_files_bnb/" + "erc20.abi"))

        self.gas_limit = 500000
        # self.gas_limit = 297255
        # self.gas_limit = 500000

    def decimals(self, address=None):
        address = self.wallet_address if not address else Web3.toChecksumAddress(address)
        if not address:
            raise RuntimeError('Please provide the wallet address!')
        erc20_contract = self.web3.eth.contract(address=self.address, abi=self.erc20_abi)
        return erc20_contract.functions.decimals().call()

    def connect_wallet(self, wallet_address='', private_key=''):
        self.wallet_address = Web3.toChecksumAddress(wallet_address)
        self.private_key = private_key

    def is_connected(self):
        return False if not self.wallet_address else True

    def require_connected(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.is_connected():
                raise RuntimeError('Please connect the wallet first!')
            return func(self, *args, **kwargs)

        return wrapper

    def create_transaction_params(self, value=0, gas_price=None, gas_limit=None):
        if not self.is_connected():
            raise RuntimeError('Please connect the wallet first!')
        if not gas_price:
            gas_price = self.web3.eth.gasPrice
        if not gas_limit:
            gas_limit = self.gas_limit
        return {
            "from": self.wallet_address,
            "value": value,
            'gasPrice': gas_price,
            "gas": gas_limit,
            "nonce": self.web3.eth.getTransactionCount(self.wallet_address)
        }

    def send_transaction(self, func, params):
        tx = func.buildTransaction(params)
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx = tx_hash.hex()
        res = self.web3.eth.waitForTransactionReceipt(tx)
        if res.status == 1:
            return tx
        else:
            return None

    def price(self):
        data = self.oracle_router.functions.latestRoundData().call()
        return int(data[1])

    def bnb_price(self, amount=int(1e18)):
        try:
            res = self.router.functions.getAmountsOut(amount, [self.address, self.ETH_ADDRESS]).call()
            return round(res[0] / res[1], 3)
        except:
            return None

    def balance(self, address=None):
        address = self.wallet_address if not address else Web3.toChecksumAddress(address)
        if not address:
            raise RuntimeError('Please provide the wallet address!')
        erc20_contract = self.web3.eth.contract(address=self.address, abi=self.erc20_abi)
        return erc20_contract.functions.balanceOf(self.wallet_address).call()

    @require_connected
    def get_round(self, id=0):
        round = self.prediction_router.functions.Rounds(id).call()
        if int(round[8]) == 0:
            self.i = 0
            self.j = self.j+1
        else:
            self.i = self.i+1
            self.j = 0
        return round

    def get_current_Epoch(self):
        return self.prediction_router.functions.currentEpoch().call()

    def bet_bull(self, amount=0, id=0):
        func = self.prediction_router.functions.BetBull(id)
        params = self.create_transaction_params(value=amount)
        return self.send_transaction(func, params)

    def bet_bear(self, amount=0, id=0):
        func = self.prediction_router.functions.BetBear(id)
        params = self.create_transaction_params(value=amount)
        return self.send_transaction(func, params)

    def claim(self, id=0):
        func = self.prediction_router.functions.Claim([id])
        params = self.create_transaction_params()
        return self.send_transaction(func, params)

    def claimAble(self, claim_id=1):
        return self.prediction_router.functions.claimable(claim_id, self.wallet_address).call()