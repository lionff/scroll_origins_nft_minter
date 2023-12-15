import json
import random
from web3 import Web3
import requests
import time

# Значение газа, выше которого ждем
GAS = 60

SLEEP = (100, 300)  # Диапазон задержки междку кошельками

w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/scroll'))
eth_w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))

abi = json.load(open('abi.json'))  # ABI
mint_address = w3.to_checksum_address(
    '0x74670A3998d9d6622E32D0847fF5977c37E0eC91')
mint_cotract = w3.eth.contract(address=mint_address, abi=abi)

headers = {
    'authority': 'nft.scroll.io',
    'accept': '*/*',
    'accept-language': 'en,ru;q=0.9,fr;q=0.8,ru-RU;q=0.7,en-US;q=0.6',
    'dnt': '1',
    'origin': 'https://scroll.io',
    'referer': 'https://scroll.io/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


def check_eligible(address):
    params = {
        'timestamp': int(time.time()),
    }
    response = requests.get(
        f'https://nft.scroll.io/p/{address}.json',
        params=params,
        headers=headers,
    )
    if response.json():
        return True

    return False


def mint(private):
    params = {
        'timestamp': int(time.time()),
    }

    response = requests.get(
        f'https://nft.scroll.io/p/{address}.json',
        params=params,
        headers=headers,
    )

    meta = tuple(response.json()['metadata'].values())
    mod_tuple = meta[:-1] + (int(meta[-1], 16),)
    proof = response.json()['proof']

    tx = {
        "chainId": w3.eth.chain_id,
        "value": 0,
        "from": address,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(address)
    }

    tx_claim = mint_cotract.functions.mint(address, mod_tuple, proof).build_transaction(tx)

    claim_txn = w3.eth.account.sign_transaction(tx_claim, private)
    claim_txn_hash = w3.eth.send_raw_transaction(claim_txn.rawTransaction)
    print(f"Claim TX: https://scrollscan.com/tx/{claim_txn_hash.hex()}")


with open("priv.txt", "r") as f:
    keys_list = [row.strip() for row in f if row.strip()]
    numbered_keys = list(enumerate(keys_list, start=1))
    random.shuffle(numbered_keys) # Перемешивание кошельков

for wallet_number, private in numbered_keys:
    #
    account = w3.eth.account.from_key(private)
    address = account.address
    print(address)

    try:

        gas_flag = False
        # Чек газа в основной сети
        while True:
            if eth_w3.eth.gas_price > w3.to_wei(GAS, 'gwei') and not gas_flag:
                gas_flag = True
                print(f"Газ выше {GAS} gwei - ждем")

            if eth_w3.eth.gas_price > w3.to_wei(GAS, 'gwei'):
                time.sleep(random.randint(50, 60))
            else:
                break
        # Если газ в поряде - начинаем работать

        balance = w3.from_wei(w3.eth.get_balance(address), 'ether')

        if check_eligible(address):
            mint(private) # Минтим НФТ

            time.sleep(random.randint(*SLEEP))

        else:
            print(f'{address} not eligible to mint')

    except Exception as err:
        print(err)
