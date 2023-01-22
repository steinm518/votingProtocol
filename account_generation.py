#Based off first_trnx.py file from class

import json
import base64
from algosdk import account, mnemonic, constants
from algosdk.v2client import algod
from algosdk.future import transaction
import time

def generate_algorand_keypair():
    jsonArr=json.load(open('accounts.json'))
    
    jsonTemp = {}
    for x in range(1):
        private_key, address = account.generate_account()
        jsonTemp["address"]=address
        jsonTemp["key"]=private_key
        jsonArr["accounts"].append(jsonTemp)
        time.sleep(.1)
    with open('accounts.json', 'w') as outfile:
        json.dump(jsonArr,outfile)
    
    
generate_algorand_keypair()
