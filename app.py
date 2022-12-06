from flask import Flask, render_template, request, escape, jsonify
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb+srv://jarchibold:6TeruB45RowBDB9d@giftlistdevdb.edublop.mongodb.net/?retryWrites=true&w=majority")

db = client["GiftListDevDB"]

lists = []

class List:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.items = []

class Item:
    def __init__(self, name):
        self.name = name
        self.isChecked = False


def generateLists():
    returnList = []
    # for i in range(100):
    #     listToAdd = List(i, f'List {i}')
    #     for j in range(5):
    #         itemToAdd = Item(f'Item {i*5+j}')
    #         listToAdd.items.append(itemToAdd)
    #     returnList.append(listToAdd)
    
    # db.create_collection("lists")
    # for i,list in enumerate(returnList):
    #     db.lists.insert_one(
    #         {"name": list.name, 
    #         "id": i}
    #     ) 

    return returnList

@app.route("/")
def home():
    documents = list(db.lists.find())
    lists = jsonify(documents)
    return lists#render_template("index.html", name="Joe", data=lists)

@app.route('/lists/<listId>/owner')
def listOwner(listId):
    lists = generateLists()
    return render_template("listOwner.html", name="Joe", list=lists[int(listId)])

@app.route('/lists/<listId>/add', methods=["GET", "POST"])
def listOwnerAdd(listId):
    lists = generateLists()
    curlist = lists[int(listId)]
    if request.method == "POST":
        inString = request.form.get("textAdd").split(',')

        for item in inString:
            curlist.items.append(Item(escape(item).strip()))

        return render_template("listOwner.html", name="Joe", list=curlist)

    return render_template("listItemAdd.html", name="Joe", list=curlist)

@app.route('/lists/<listId>/remove', methods=["GET", "POST"])
def listOwnerRemove(listId):
    lists = generateLists()
    curlist = lists[int(listId)]
    if request.method == "POST":
        for val,item in enumerate(curlist.items):
            if request.form.get(item.name) == 'on':
                curlist.items[val] = None

        curlist.items = list(filter(None, curlist.items))

        return render_template("listOwner.html", name="Joe", list=curlist)

    return render_template("listItemRemove.html", name="Joe", list=curlist)


@app.route('/lists/<listId>/guest')
def listGuest(listId):
    lists = generateLists()
    return render_template("listGuest.html", name="Joe", list=lists[int(listId)])

if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    app.run()