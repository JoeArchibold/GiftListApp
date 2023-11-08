from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort
from pymongo import MongoClient
import json, hashlib, os, secrets
import bson

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

devmode = True

if(devmode) :
    with open('secrets/devpassword.txt') as f:
        password = f.read()

    connection_string = f'mongodb+srv://jarchibold:{password}@giftlistdevdb.edublop.mongodb.net/?retryWrites=true&w=majority'
else:
    with open('secrets/passwords.txt') as f:
        password = f.read()

    connection_string = f'mongodb+srv://jarchibold:{password}@giftlistprod.zsqr6ad.mongodb.net/?retryWrites=true&w=majority'

client = MongoClient(connection_string)


db = client["GiftListDevDB"]

def generateLists():
    returnList = []

    db.lists.delete_many({})
    for i in range(10):
        listToAdd = {
            "_id": i,
            "name": f'List {i}', 
            "items": [],
            "owner": "randomUser"
        }
        for j in range(5):
            itemToAdd = {
                "name": f'Item {j}',
                "isChecked": False,
                "rank": j + 1,
                "id": j
            }
            listToAdd['items'].append(itemToAdd)
        returnList.append(listToAdd)
    
    db.lists.insert_many(returnList) 

    return returnList

def fixItems():
    documents = list(db.lists.find())
    response = jsonify(documents)
    lists = json.loads(response.data)

    for curlist in lists:
        for i, item in enumerate(curlist['items']):
            # item['checkedBy'] = None
            item['rank'] = i + 1

        db.lists.update_one({'_id': int(curlist['_id'])}, {'$set': curlist})
    
    print("Done!")



def getList(listId):
    listId = int(listId)
    documents = db.lists.find_one({'_id': listId})
    response = jsonify(documents)
    curList = json.loads(response.data)
    return curList

@app.route("/login", methods=["GET", "POST"])
def login():
    if(request.method == "POST"):
        username = request.form['username'].lower()
        password = request.form['password']

        user = db.users.find_one({'username': username})
        
        if not user:
            return render_template("login.html", failed=True)

        salt = user['salt']

        saltedPass = password.encode('utf-8') + salt
        hashedPass = hashlib.sha256(saltedPass).hexdigest()

        if(hashedPass == user['password']):
            session['loggedIn'] = True
            session['userId'] = str(user['_id'])
            return redirect(url_for('home'))
        else:
            return render_template("login.html", failed=True)

    return render_template("login.html", failed=False)

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session['loggedIn'] = None
    session['userId'] = None

    return redirect(url_for('login'))

@app.route("/")
def index():
    if session.get('loggedIn') != None:
        return redirect(url_for('home'))
    return redirect(url_for("login"))

@app.route('/create-account', methods=["GET", "POST"])
def createAccount():
    if(request.method == "POST"):
        username = request.form['username'].lower()

        if(db.users.find_one({'username': username})):
            return render_template("create-account.html", username_exists=True)

        password = request.form['password']

        if(password != request.form['password-confirm']):
            return render_template("create-account.html", password_mismatch=True)

        salt = os.urandom(32)

        saltedPass = password.encode('utf-8') + salt
        hashedPass = hashlib.sha256(saltedPass).hexdigest()

        user = {
            "username": username,
            "password": hashedPass,
            "salt": salt,
            "name": {
                "first": request.form['first-name'],
                "last": request.form['last-name']
            }
        }

        db.users.insert_one(user)

        return redirect(url_for('login'))

    return render_template("create-account.html")

@app.route("/lists")
def home():
    if session.get('loggedIn') == None:
        return redirect(url_for("login"))
    
    user = db.users.find_one({'_id': bson.ObjectId(session['userId'])})

    documents = list(db.lists.find())
    response = jsonify(documents)
    lists = json.loads(response.data)

    userLists = []
    otherLists = []
    for curlist in lists:
        if curlist['owner'] == user['username']:
            userLists.append(curlist)
        else:
            otherLists.append(curlist)
    
    userLists = sorted(userLists, key=lambda x: x['name'])
    otherLists = sorted(otherLists, key=lambda x: x['name'])

    return render_template("home.html", userLists=userLists, otherLists=otherLists, name=user['name']['first'])

@app.route('/lists/create', methods=["GET", "POST"])
def create():
    if session.get('loggedIn') == None:
        return redirect(url_for("login"))

    if request.method == "POST":
        user = db.users.find_one({'_id': bson.ObjectId(session['userId'])})

        listName = request.form.get("listName")
        inString = [str.strip() for str in request.form.get("textAdd").split(',')]

        itemsToAdd = []

        for item in inString:
            if item == "":
                continue

            itemsToAdd.append({
                "name": item,
                "isChecked": False,
                "rank": 0,
                "id": len(itemsToAdd)
            })

        new_id = -1
        try:
            new_id = db.lists.find().sort("_id", -1).limit(1).next()["_id"] + 1
        except:
            new_id = 0

        db.lists.insert_one({'_id': int(new_id),'name': listName , 'items': itemsToAdd, 'owner': user['username']})

        return home()

    return render_template("create.html")

@app.route('/lists/<listId>/choose')
def choose(listId):
    if session.get('loggedIn') == None:
        return redirect(url_for("login"))
    
    user = db.users.find_one({'_id': bson.ObjectId(session['userId'])})
    curList = getList(listId)

    if curList['owner'] != user['username']:
        return redirect(f'/lists/{listId}/guest')
    else:
        return redirect(f'/lists/{listId}/owner')


@app.route('/lists/<listId>/owner', methods=['GET', 'POST'])
def listOwner(listId):
    if session.get('loggedIn') == None:
        return redirect(url_for("login"))
    
    user = db.users.find_one({'_id': bson.ObjectId(session['userId'])})
    curList = getList(listId)

    if curList['owner'] != user['username']:
        return redirect(f'/lists/{listId}/guest')
    
    if request.method == 'POST':
        data = request.json
        tempList = data.get('list', {})
        
        items = tempList['items']

        curList['name'] = tempList['name']
        curList['items'] = items

        curList['items'] = sorted(curList['items'], key=lambda x: int(x['rank']) if int(x['rank']) > 0 else 1000000)

        db.lists.update_one({'_id': int(listId)}, {'$set': curList})

        return jsonify({'message': 'Data received successfully'})

    return render_template("listOwner.html", list=curList)

@app.route('/lists/<listId>/guest', methods=["GET", "POST"])
def listGuest(listId):
    if session.get('loggedIn') == None:
        return redirect(url_for("login"))

    user = db.users.find_one({'_id': bson.ObjectId(session['userId'])})
    curList = getList(listId)

    if curList['owner'] == user['username']:
        return redirect(f'/lists/{listId}/owner')

    if request.method == "POST":
        data = request.json
        change = data.get('change', {})

        change['id'] = int(change['id'])

        for item in curList['items']:
            if(item['id'] == change['id']):
                if item['checkedBy'] != user['username'] and item['checkedBy']:
                    abort(401)

                if change['nowChecked']:
                    item['checkedBy'] = user['username']
                    item['isChecked'] = True
                else:
                    item['checkedBy'] = None
                    item['isChecked'] = False

        db.lists.update_one({'_id': int(listId)}, {'$set': curList})

        return jsonify({'message': 'Data received successfully'})

    copylist = curList.copy()

    for item in copylist['items']:
        item['locked'] = (item["isChecked"] and item["checkedBy"] != user['username'])

    return render_template("listGuest.html", list=copylist)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=False, debug=True)
