import json
import base64
from algosdk import account, mnemonic, constants
from algosdk.v2client import algod
from algosdk.future import transaction
from pyteal import compileTeal, Mode
from voteProt import clearProgram
from hashlib import sha256
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_client = algod.AlgodClient(algod_token, algod_address)
appID = 101
voteProt=99
params = algod_client.suggested_params()
params.fee=200000
def sendTxn(txn,private_key):
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()
    algod_client.send_transactions([signed_txn])
    try:
        confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)
    except Exception as err:
        print(err)
        return
        
    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))
def contract_optIn(private_key,app):
    #Make transaction
    
    sender = account.address_from_private_key(private_key)
    txn = transaction.ApplicationOptInTxn(sender, params, app)
    sendTxn(txn,private_key)
    

def createContract(private_key, contract):
    sender=account.address_from_private_key(private_key)
    txn= transaction.ApplicationNoOpTxn(sender,params,appID,
    foreign_apps=[voteProt],
    boxes=[[voteProt,"MinVia"], [voteProt,sha256(contract).digest()]],
    app_args=["AddVote",contract]
    )
    print(txn)
    sendTxn(txn,private_key)

def vote(private_key, contract):
    sender=account.address_from_private_key(private_key)
    txn= transaction.ApplicationNoOpTxn(sender,params,appID,
    foreign_apps=[voteProt],
    boxes=[[voteProt,"MinVia"], [voteProt,sha256(contract).digest()]],
    app_args=["Vote",sha256(contract).digest()]
    )
    sendTxn(txn,private_key)

def checkContract(private_key, contract):
    sender=account.address_from_private_key(private_key)
    txn=transaction.ApplicationUpdateTxn(sender,params,appID,
    approval_program=contract,
    clear_program=contract,
    foreign_apps=[voteProt],
    boxes=[[voteProt,"MinVia"], [voteProt,sha256(contract).digest()]],
    app_args=[contract]
    )
    print(txn)
    sendTxn(txn,private_key)
def main(): 
    f = open("accounts.json")
    jsonDict = json.load(f)

    private_key = jsonDict["accounts"][2]['key']

    programCompiled2= compileTeal(clearProgram(),mode=Mode.Application, version=8)
    bin2= algod_client.compile(programCompiled2)
    binaryProgram2 = base64.b64decode(bin2["result"])
    createContract(private_key,binaryProgram2)
    #contract_optIn(private_key,appID)
    #contract_optIn(private_key,voteProt)
    #checkContract(private_key,binaryProgram2)
    #vote(private_key,binaryProgram2)
main()