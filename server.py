
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
# accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, abort, request, render_template, g, redirect, Response, url_for

tmpl_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "kz2437"
DATABASE_PASSWRD = "5539"
# change to 34.28.53.86 if you used database 2 for part 2
DATABASE_HOST = "34.148.107.47"
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/project1"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI, future=True)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request 
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
    """
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
	"""


# main page
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/redirect_to_order_payment', methods=['POST'])
def redirect_to_order_payment():
    order_id = request.form['order_id']
    return redirect(url_for('order_payment', orderID=order_id))


@app.route('/redirect_to_order_status', methods=['POST'])
def redirect_to_order_status():
    order_id = request.form['order_id']
    return redirect(url_for('order_status', orderID=order_id))


@app.route('/redirect_to_customer_order_status', methods=['POST'])
def redirect_to_customer_order_status():
    current_status = request.form['current_status']
    return redirect(url_for('customer_order_status', current_status=current_status))


@app.route('/redirect_to_search_product', methods=['POST'])
def redirect_to_search_product():
    price_low = request.form['price_low']
    price_high = request.form['price_high']
    return redirect(url_for('search_product', price_low=price_low, price_high=price_high))


@app.route('/redirect_to_add_product', methods=['POST'])
def redirect_to_add_product():
    productID = request.form['productID']
    product_name = request.form['product_name']
    price = request.form['price ']
    description = request.form['description']
    return redirect(url_for('add_product',productID=productID, product_name=product_name, price=price, description=description))


'''
check for the status of an order
'''


@app.route('/order_status', methods=['GET'])
def order_status():
    orderID = request.args.get('orderID')
    select_query1 = "SELECT o.orderID, o.placing_date, o.shipping_date, o.current_status, p.product_name, p.price from orders o natural join product p where o.orderID = \'{}\'".format(
        orderID)
    cursor = g.conn.execute(text(select_query1))
    orderdetails = [result for result in cursor]
    cursor.close()
    context = dict(data=orderdetails)

    return render_template("order_status.html", **context)


'''
check for the transaction info of an order
'''


@app.route('/order_payment', methods=['GET'])
def order_payment():
    orderID = request.args.get('orderID')
    select_query2 = "SELECT * from transaction where orderID = \'{}\';".format(
        orderID)
    cursor = g.conn.execute(text(select_query2))
    paymentdetails = [result for result in cursor]
    cursor.close()
    context = dict(data=paymentdetails)

    return render_template("order_payment.html", **context)


'''
show all the possible customers who currently have have at least one order of a specific status(ex."cancelled")
'''


@app.route('/customer_order_status', methods=['GET'])
def customer_order_status():
    current_status = request.args.get('current_status', 'cancelled')
    select_query3 = "SELECT DISTINCT customerID, first_name, last_name FROM customer NATURAL JOIN address NATURAL JOIN orders WHERE current_status =\'{}\';".format(
        current_status)
    cursor = g.conn.execute(text(select_query3))
    listofcustomers = [result for result in cursor]
    cursor.close()
    context = dict(data=listofcustomers, current_status=current_status)

    return render_template("customer_order_status.html", **context)


'''
search for a product with a price range
'''


@app.route('/search_product')
def search_product():
    price_low = request.args.get('price_low', '0')
    price_high = request.args.get('price_high', '100000')
    select_query4 = "SELECT * from product where price>=\'{}\' and price<= \'{}\' ".format(
        price_low, price_high)
    cursor = g.conn.execute(text(select_query4))
    products = [c for c in cursor]
    cursor.close()
    context = dict(data=products)

    return render_template("search_product.html", **context)


'''
add new product
'''

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        # accessing form inputs from user
        productID = request.form['productID']
        product_name = request.form['product_name']
        price = request.form['price']
        description = request.form['description']
        # passing params in for each variable into query
        g.conn.execute(text('INSERT INTO product VALUES (\'{}\',\'{}\',\'{}\',\'{}\')'.format(
            productID, product_name, price, description)))
        g.conn.commit()
        return redirect(url_for('add_product_success'))
    else:
        return render_template('index.html')


@app.route('/add_product_success')
def add_product_success():
    return render_template("add_product_success.html")










@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using:

                python server.py

        Show the help text using:

                python server.py --help

        """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
