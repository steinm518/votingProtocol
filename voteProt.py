import json
import base64
from algosdk.v2client import algod
from algosdk import mnemonic
from algosdk import account
from algosdk.future.transaction import *
from pyteal import *


f = open("accounts.json")
jsonDict = json.load(f)
# user declared algod connection parameters

votedApp=Itob(Global.caller_app_id())
voter=Txn.accounts[1]
appSize=Int(8)
btoiIntSize=Int(8)
callType=Txn.application_args[0]
diff=ScratchVar()
#Check optin into both contracts
optInCheck=And(
App.optedIn(voter,App.id()),
App.optedIn(voter,Global.caller_app_id())
)
checkAppAllowed=Seq(
    length:=App.box_length(votedApp),
    length.hasValue()
    )

def on_creation():
    x=Seq(App.globalPut(Bytes("prevBal"),Balance(Global.current_application_address())),
    Log(Global.current_application_address()),
    Int(1)
    )
    return x
 
def checkDiff():
    x=Seq(
        diff.store(Minus(Balance(Global.current_application_address()),App.globalGet(Bytes("prevBal")))),
        App.globalPut(Bytes("prevBal"),Balance(Global.current_application_address())),
        Int(1)    
    )
    return x 
def vote():
    s = ScratchVar(TealType.bytes)
    contractVote=Txn.application_args[1]
    #Check that the vote already exists and corresponds with the app
    voteExistsCheck=Seq(
    Assert(
    Seq(
    box:=App.box_get((contractVote)),
    box.hasValue()
    )
    ),
    s.store(App.box_extract(contractVote,Int(0),appSize)),
    Assert(Eq(s.load(),votedApp)),
    Int(1)
    )
    #Check that they havent already voted for that block 
    notVoted=Not(App.localGet(Int(1),contractVote))  

    #Check that the App opted in
    
    tempvote = ScratchVar(TealType.uint64)
    #Change the vote count
    updateVote=Seq(
    Assert(
    box.hasValue()),
    tempvote.store(Btoi(App.box_extract(contractVote,appSize,btoiIntSize))),
    tempvote.store(Add(tempvote.load(),Int(1))),
    App.box_replace(contractVote,appSize,
    Itob(tempvote.load())),
    Int(1)
    )

    vote=Seq(Assert(And(
    optInCheck,
    checkAppAllowed,
    voteExistsCheck,
    notVoted,
    checkDiff(),
    )),
    Pop(voteCost:=App.box_extract(votedApp,Int(0),btoiIntSize)),
    Assert(Ge(diff.load(),Btoi(voteCost))),
    App.localPut(Int(1),contractVote,Int(1)),
    Assert(updateVote),
    Int(1)
    )
    return vote

def addApp():
    #Box should be: [voteCost, voteCountReq, lastCompletedVote]
    voteCost=Txn.application_args[1]
    voteCountReq=Txn.application_args[2]
    addApp=Seq(
    Assert(Not(checkAppAllowed)),
    Assert((Btoi(votedApp))),
    Pop(App.box_create(votedApp,Mul(btoiIntSize,Int(2)))),
    App.box_replace(votedApp, Int(0), Concat(voteCost,voteCountReq)),
    Int(1)
    )
    return addApp

def addVote():
    contract=Txn.application_args[1]
    len=Add(Len(contract),Int(128))
    name=Sha256(contract)
    addVote= Seq(
    Assert(checkAppAllowed),
    Assert(checkDiff()),
    Assert(App.box_create(name,len)),
    App.box_replace(name,Int(0),Concat(votedApp,Itob(Int(0)),contract)),
    Assert(Ge(diff.load(),Int(2500) + Int(400) * (len+Int(32)) )),
    Log(votedApp),
    Int(1)
    )
    return addVote
def sameContract():
    contract=Txn.application_args[1]
    len=Len(contract)
    name=Sha256(contract)
    currentPart=ScratchVar(TealType.uint64)
    offset=btoiIntSize+appSize
    section=Int(64)
    finalPart=Mod(len,Int(64))
    sameCont =Seq(
    box:=App.box_get(name),
    Assert(box.hasValue()),
    Pop(len2:=Minus(Len(box.value()),offset)),
    Assert(Eq(len2,len)),
    currentPart.store(Int(0)),
    #Assert(Eq(votedApp,Extract(box.value(),Int(0),Int(32)))),
    While(Ge(len2+offset,currentPart.load()+section)).Do(
        Pop(tempBox:=App.box_extract(name,currentPart.load(),section)),
        Pop(contractPart:=Extract(contract,Minus(currentPart.load(),offset),section)),
        Assert(BytesEq(tempBox,contractPart)),
        currentPart.store(Add(currentPart.load(),section))
    ),
    #Check last incomplete section of 64. 
    Pop(tempbox:= App.box_extract(name,currentPart.load(),finalPart)),
    Pop(contractPart:=Extract(contract,Minus(currentPart.load(),offset),finalPart)),
    Assert(BytesEq(tempbox,contractPart)),
    Int(1)
    )
    return sameCont

def checkVote():
    contract=Txn.application_args[2]
    numUsers=Btoi(Txn.application_args[1])
    name=Sha256(contract)
    voteCount=ScratchVar()
    percentReq=ScratchVar()
    voteCheck=Seq(
    Assert(sameContract()),
    voteCount.store(Btoi(App.box_extract(name,appSize,btoiIntSize*Int(2)))),
    percentReq.store(Btoi(App.box_extract(votedApp,appSize+btoiIntSize,appSize+btoiIntSize*Int(2)))),
    Assert(Ge(((voteCount.load()*Int(100))/numUsers),percentReq.load())),
    Pop(App.box_delete(name)),
    Int(1)
    )

    return voteCheck

def programMaker():
    program = Cond(
        [Txn.application_id() == Int(0), Return(on_creation())],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(1))],
        [Txn.on_completion() == OnComplete.OptIn, Return(Int(1))],
        [Txn.application_args[0] == Bytes("Vote"), Return(vote())],
        [Txn.application_args[0] == Bytes("NewApp"), Return(addApp())],
        [Txn.application_args[0] == Bytes("CheckVote"), Return(checkVote())],
        [Txn.application_args[0] == Bytes("AddVote"), Return(addVote())],
        [Txn.application_args[0] == Bytes("Address"), Return(Seq(Log(Concat(Bytes("Address "),Global.creator_address())), Int(1)))]
    )
    return program

with open('voteProt.teal','w') as f:
    compiled = compileTeal(programMaker(),Mode.Application,version=8)
    f.write(compiled)
def clearProgram():
    return (Return(Int(1)))