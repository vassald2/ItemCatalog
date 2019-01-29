# -*- coding: cp1252 -*-
from flask import Flask, render_template, url_for, request
from flask import redirect, flash, jsonify, make_response
from sqlalchemy import create_engine
from functools import wraps
from sqlalchemy.orm import sessionmaker
from database_setup import Base, ItemsDB, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json
import requests
import httplib2

app = Flask(__name__)


# Google client_id
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ItemsCatalog"

# Connect to database
engine = create_engine('sqlite:///ItemsDB.db?check_same_thread=False')
Base.metadata.bind = engine

# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# checking current user
def check_user():
    userEmail = login_session['email']
    return session.query(User).filter_by(email=userEmail).first()


# making login required for certain functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function

                  
# adds new user
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    userCheck = check_user()
    if userCheck is None:
        session.add(newUser)
        session.commit()
        user = session.query(User).filter_by(
            email=login_session['email']).first()
        return user.id
    else:
        user = session.query(User).filter_by(
            email=login_session['email']).first()
        return user.id


# Returns user id
def getUserID(email):
    user = session.query(User).filter_by(email=email).first()
    if user is None:
        return None
    else:
        return user.id


# Returns all items in database
def get_items():
    return session.query(ItemsDB).all()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# home page
@app.route('/')
@app.route('/items/')
def allItems():
    ItemValue = get_items()
    return render_template('index.html', items=ItemValue,
                           currentCategory='All Items',
                           login_session=login_session)


# returns all items in databse in json
@app.route('/items.json/')
def items_json():
    items = session.query(ItemsDB).all()
    return jsonify(Items=[item.serialize for item in items])


# adding new item
@app.route('/new/', methods=['GET', 'POST'])
@login_required
def newItem():
    if request.method == 'POST':
        itemName = request.form['name']
        description = request.form['description']
        category = request.form['category']
        user_id = check_user().id

        if itemName and description and category:
            newItem = ItemsDB(
                itemName=itemName,
                description=description,
                category=category,
                user_id=user_id,
                )
            session.add(newItem)
            session.commit()
            return redirect(url_for('allItems'))
        else:
            return render_template(
                'addItem.html',
                currentCategory='Add New Item',
                login_session=login_session,
                )
        session.commit()
        return redirect(url_for('allItems'))
    else:
        return render_template(
                'addItem.html',
                currentCategory='Fill out new Item',
                login_session=login_session,
                )


# To show the items in a category
@app.route('/category/<string:category>/')
def showItems(category):
    items = session.query(ItemsDB).filter_by(category=category).all()
    return render_template(
        'index.html',
        items=items,
        currentCategory=category,
        login_session=login_session)


# To show details of item detail
@app.route('/category/<string:category>/<int:itemId>/')
def itemDetail(category, itemId):
    item = session.query(ItemsDB).filter_by(id=itemId,
                                            category=category).first()
    if item:
        return render_template('itemDetail.html', items=item,
                               currentCategory='Detail',
                               login_session=login_session)
    else:
        error = "No Item Found with this Category and Item Id"
        return render_template('index.html', items=get_items(),
                               currentCategory='All Items',
                               error=error,
                               login_session=login_session)


# To edit the item
@app.route('/category/<string:category>/<int:itemId>/edit/',
           methods=['GET', 'POST'])
@login_required
def editItem(category, itemId):
    item = session.query(ItemsDB).filter_by(id=itemId,
                                            category=category).first()
    if item.user_id != login_session['user_id']:
        error = "You can only edit items you created."
        return render_template('index.html', items=get_items(),
                               currentCategory='All Items',
                               error=error,
                               login_session=login_session)
    if request.method == 'POST':
        if request.form['name']:
            item.itemName = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category']:
            item.category = request.form['category']
        session.add(item)
        session.commit()
        flash('Successfully Edited %s' % item.itemName)
        return redirect(url_for('allItems'))
    else:
        return render_template('editItem.html',
                               currentCategory='Edit',
                               item=item,
                               login_session=login_session,)


# To delete items
@app.route('/category/<string:category>/<int:itemId>/delete/')
@login_required
def deleteItem(category, itemId):
    item = session.query(ItemsDB).filter_by(category=category,
                                            id=itemId).one()
    if item:
        if login_session['user_id'] != item.user_id:
            error = "Error Deleting Item! You must own an item to delete it"
            return render_template('index.html', items=get_items(),
                                   currentCategory='All Items',
                                   error=error,
                                   login_session=login_session)
        session.delete(item)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('allItems'))
    else:
        error = "Error Deleting Item! No Item Found"
        return render_template('index.html', items=get_items(),
                               currentCategory='All Items',
                               error=error,
                               login_session=login_session)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user \
                                 is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print(data)
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: \
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# used to logout of google account
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        print response
        return redirect(url_for('allItems'))
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        print response
        return redirect(url_for('allItems'))
    else:
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        response = make_response(json.dumps('Failed to revoke token for \
                                            given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        print response
        return redirect(url_for('allItems'))

if __name__ == '__main__':
    app.secret_key = 'sosecretverywow'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
