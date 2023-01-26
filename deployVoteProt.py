import base64

from algosdk.future import transaction
from algosdk import account, mnemonic
from algosdk.v2client import algod
import algosdk
from pyteal import compileTeal, Mode
from voteProt import programMaker, clearProgram
from pyteal import *
import json
import subprocess 





f = open("accounts.json")
jsonDict = json.load(f)
accounts = jsonDict["accounts"]
voteid = jsonDict["voteid"]

# user declared algod connection parameters
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_client = algod.AlgodClient(algod_token, algod_address)

params = algod_client.suggested_params()
params.fee = 10000
def create_application():
    
    #make sender
    local_ints = 8
    local_bytes = 8
    global_ints = 1
    global_bytes = 0
    on_complete = transaction.OnComplete.NoOpOC.real
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)
    programCompiled = compileTeal(programMaker(),mode=Mode.Application,version=8)
    programCompiled2= compileTeal(clearProgram(),mode=Mode.Application, version=8)
    bin = algod_client.compile(programCompiled)
    bin2= algod_client.compile(programCompiled2)
    binaryProgram = base64.b64decode(bin["result"])
    binaryProgram2 = base64.b64decode(bin2["result"])
    sender = accounts[0]['address']
    print(sender)
    pk = accounts[0]['key']
    print(pk)
    txn = transaction.ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        binaryProgram,
        binaryProgram2,
        global_schema,
        local_schema
    )
    signedtxn=txn.sign(pk)
    txid = signedtxn.transaction.get_txid()
    algod_client.send_transactions([signedtxn])
    wait_for_confirmation(algod_client, txid)
    transaction_response = algod_client.pending_transaction_info(txid)
    app_id = transaction_response["application-index"]
    app_address=transaction_response["logs"][0]
    print(app_address)
    jsonDict["voteid"]=app_id
    
    #Must manually update app_address
    
    print("Created new app-id:", app_id)
    print(transaction_response)
    sandbox='/home/stein/Desktop/CS598/sandbox/./sandbox'
    args = [sandbox,'goal','app', 'info','--app-id',str(app_id)]
    output = subprocess.check_output(args)
    output=output.splitlines()[1]
    output=output.split()[2]
    address=output.decode()
    print(address)
    jsonDict["vote_addr"]=address
    with open('accounts.json', 'w') as outfile:
        json.dump(jsonDict,outfile)

def wait_for_confirmation(client, txid):
    last_round = client.status().get("last-round")
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get("confirmed-round") and txinfo.get("confirmed-round") > 0):
        print("Waiting for confirmation...")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print(
        "Transaction {} confirmed in round {}.".format(
            txid, txinfo.get("confirmed-round")
        )
    )
    return txinfo

create_application()