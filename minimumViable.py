
from pyteal import *
import json
f = open("accounts.json")
jsonDict = json.load(f)
accounts = jsonDict["accounts"]
voteProtId = Int(jsonDict["voteid"])
AppParam.address
voteProtAddr = Addr("6YJ4ILMPCE7JAIMTNUF6HUZY5T2H3XC2Q3UCQ6DOZLJOIODDSTOHR4WXKI")
def preCreate():
    x=Seq(
    App.globalPut(Bytes("Users"),Int(0)),
    Int(1))
    return x
def create():
    x=Seq(
    InnerTxnBuilder.Begin(),
    InnerTxnBuilder.SetFields(
    {
    TxnField.type_enum: TxnType.ApplicationCall,
    TxnField.application_id: voteProtId,
    TxnField.application_args: [Bytes("NewApp"),Itob(Int(1)),Itob(Int(5))],
    TxnField.on_completion: OnComplete.NoOp,
    }
    ),
    InnerTxnBuilder.Submit(),
    
    Int(1)    
    )
    return x
def addContract():
    contract=Txn.application_args[1]
    addCont=Seq(
    InnerTxnBuilder.Begin(),
    InnerTxnBuilder.SetFields(
    {
        TxnField.type_enum: TxnType.ApplicationCall,
        TxnField.application_id: voteProtId,
        TxnField.application_args: [Bytes("AddVote"),contract],
        TxnField.on_completion: OnComplete.NoOp,
    }    
    ),
    InnerTxnBuilder.Submit(),
    Int(1)
    )
    return addCont
def checkContract():
    x=Seq(
    InnerTxnBuilder.Begin(),
    InnerTxnBuilder.SetFields(
    {
    TxnField.type_enum: TxnType.ApplicationCall,
    TxnField.application_id: voteProtId,
    TxnField.application_args: [Bytes("CheckVote"),App.globalGet(Bytes("Users")),Txn.approval_program()],
    TxnField.on_completion: OnComplete.NoOp,
    }
    ),
    InnerTxnBuilder.Submit(),
    Int(1)    
    )
    return x
def vote():
    contract=Txn.application_args[1]
    vot=Seq(
    InnerTxnBuilder.Begin(),
    InnerTxnBuilder.SetFields(
    {
        TxnField.type_enum: TxnType.ApplicationCall,
        TxnField.application_id: voteProtId,
        TxnField.application_args: [Bytes("Vote"),contract],
        TxnField.on_completion: OnComplete.NoOp,
        TxnField.accounts: [Txn.sender()],
        TxnField.applications: [Global.current_application_id()]
    }    
    ),
    InnerTxnBuilder.Submit(),
    Int(1)
    )
    return vot
def programMaker():
    program = Cond(
        [Txn.application_id() == Int(0), Return(preCreate())],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(checkContract())],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(0))],
        [Txn.on_completion() == OnComplete.OptIn, Return(Seq(App.globalPut(Bytes("Users"),App.globalGet(Bytes("Users"))+Int(1)),Int(1)))],
        [Txn.application_args[0] == Bytes("Vote"),    Return(vote())],
        [Txn.application_args[0] == Bytes("AddVote"), Return(addContract())],
        [Txn.application_args[0] == Bytes("Create"),  Return(create())]
    )
    return program

with open('voteProt.teal','w') as f:
    compiled = compileTeal(programMaker(),Mode.Application,version=8)
    f.write(compiled)