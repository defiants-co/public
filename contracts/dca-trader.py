config = {
  "secret_key": "secret-key-goes-here",
  "send_to": "send-to-this-address-after-trades",
  "asset_from": {
    "code": "AQUA",
    "issuer": "GBNZILSTVQZ4R7IKQDGHYGY2QXL5QOFJYQMXPKWRRM5PAV7Y4M67AQUA",
    "amount_per_hour": 5000
  },
  "asset_to": [
    {
      "code": "BTC",
      "issuer": "GDPJALI4AZKUU2W426U5WKMAT6CN3AJRPIIRYR2YM54TL2GDWO5O2MZM",
      "percent": 50
    },
    {
      "code": "ETH",
      "issuer": "GBFXOHVAS43OIWNIO7XLRJAHT3BICFEIKOJLZVXNT572MISM4CMGSOCC",
      "percent": 50
    },
    {
      "code": "USDC",
      "issuer": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
      "percent": 0
    },
    {
      "code": "GOLD",
      "issuer": "GBC5ZGK6MQU3XG5Y72SXPA7P5R5NHYT2475SNEJB2U3EQ6J56QLVGOLD",
      "percent": 0
    }
  ]
}

from requests import get
from stellar_sdk import (
            Asset, 
            Keypair, 
            Network, 
            Server, 
            TransactionBuilder
        )

def get_balance(balances):
    for balance in balances:
        if balance['asset_type'] != "native" and balance['asset_code'] == config['asset_from']['code'] and balance['asset_issuer'] == config['asset_from']['issuer']:
            return balance

def lambda_handler(event,context):
    print("starting...")
    server = Server("https://horizon.stellar.org")
    source_keypair = Keypair.from_secret(secret=config['secret_key'])

    balances = get('https://horizon.stellar.org/accounts/' + source_keypair.public_key).json()['balances']
    balance = get_balance(balances)
    print(f"you have {balance['balance']} {config['asset_from']['code']}")
    print(f"you are trading {config['asset_from']['amount_per_hour']} {config['asset_from']['code']}")
    source_account = server.load_account(source_keypair.public_key)
    transaction = TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
            base_fee=5000
        )
    for asset in config['asset_to']:
      if asset['percent'] != 0:
        transaction.append_path_payment_strict_send_op(
            send_asset = Asset(config['asset_from']['code'],config['asset_from']['issuer']),
            send_amount = str(round(asset['percent']*0.01*config['asset_from']['amount_per_hour'],7)),
            dest_asset = Asset(asset['code'],asset['issuer']),
            dest_min = "0.0000001",
            destination = config['send_to'],
            path = [Asset.native()],
            )
        print(f"added trade: from {config['asset_from']['code']}:{config['asset_from']['issuer'][0:10]} to {asset['code']}:{asset['issuer'][0:10]}")
    print("building transaction...")
    completed = transaction.build()
    print("built transaction.")
    print("signing transaction...")
    completed.sign(source_keypair)
    print("signed transaction.")
    a = None
    try:
        print("submitting transaction...")
        a = server.submit_transaction(completed)['hash']
        print(a)
    except:
        print("transaction submission failed... trying again.")
        a = server.submit_transaction(completed)['hash']
    if a == None:
        print("couldn't submit transaction :(")

lambda_handler("a","a")