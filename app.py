from flask import Flask, render_template, request, escape, jsonify
from pymongo import MongoClient
import json

app = Flask(__name__, static_folder='static')


with open('secrets/passwords.txt') as f:
    password = f.read()

connection_string = f'mongodb+srv://jarchibold:{password}@giftlistdevdb.edublop.mongodb.net/?retryWrites=true&w=majority'

client = MongoClient(connection_string)


db = client["GiftListDevDB"]

def generateLists():
    returnList = []

    # for i in range(10):
    #     listToAdd = {
    #         "_id": i,
    #         "name": f'List {i}', 
    #         "items": []
    #     }
    #     for j in range(5):
    #         itemToAdd = {
    #             "name": f'Item {j}',
    #             "isChecked": False
    #         }
    #         listToAdd['items'].append(itemToAdd)
    #     returnList.append(listToAdd)
    
    # db.lists.insert_many(returnList) 

    return returnList

def getList(listId):
    listId = int(listId)
    documents = db.lists.find_one({'_id': listId})
    response = jsonify(documents)
    curList = json.loads(response.data)
    return curList

@app.route("/")
def home():
    documents = list(db.lists.find())
    response = jsonify(documents)
    lists = json.loads(response.data)
    return render_template("index.html", data=lists)

@app.route('/lists/create', methods=["GET", "POST"])
def create():
    if request.method == "POST":
        listName = request.form.get("listName")
        inString = request.form.get("textAdd").split(',')

        itemsToAdd = [];
        for item in inString:
            itemsToAdd.append({
                "name": item,
                "isChecked": False
            })

        new_id = db.lists.find().sort("_id", -1).limit(1).next()["_id"] + 1

        db.lists.insert_one({'_id': int(new_id),'name': listName , 'items': itemsToAdd})

        return home()

    return render_template("create.html")

@app.route('/lists/<listId>/choose')
def choose(listId):
    return render_template("choose.html", listId=listId)

@app.route('/lists/<listId>/owner')
def listOwner(listId):
    curList = getList(listId)
    return render_template("listOwner.html", list=curList)

@app.route('/lists/<listId>/add', methods=["GET", "POST"])
def listOwnerAdd(listId):
    curList = getList(listId)
    if request.method == "POST":
        inString = request.form.get("textAdd").split(',')

        for item in inString:
            curList['items'].append({
                "name": item,
                "isChecked": False
            })

        db.lists.update_one({'_id': int(listId)}, {'$set': curList})

        return render_template("listOwner.html", list=curList)

    return render_template("listItemAdd.html", list=curList)

@app.route('/lists/<listId>/remove', methods=["GET", "POST"])
def listOwnerRemove(listId):
    curList = getList(listId)
    if request.method == "POST":
        for val,item in enumerate(curList['items']):
            if request.form.get(item['name']) == 'on':
                curList['items'][val] = None

        curList['items'] = list(filter(None, curList['items']))

        db.lists.update_one({'_id': int(listId)}, {'$set': curList})

        return render_template("listOwner.html", list=curList)

    return render_template("listItemRemove.html", list=curList)


@app.route('/lists/<listId>/guest', methods=["GET", "POST"])
def listGuest(listId):
    curList = getList(listId)
    if request.method == "POST":
        for val,item in enumerate(curList['items']):
            if request.form.get(item['name']) == 'on':
                curList['items'][val]['isChecked'] = True
            else:
                curList['items'][val]['isChecked'] = False

        db.lists.update_one({'_id': int(listId)}, {'$set': curList})

    return render_template("listGuest.html", list=curList)

if __name__ == '__main__':
    app.run()
