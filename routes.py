from flask import Flask, render_template, session, redirect, url_for, request, flash, jsonify
from connection import get_connection
import os
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import numpy as np

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')

model = MobileNetV2(weights='imagenet')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/products')
def products():
    try:
        conn = get_connection()
        if conn is None:
            return "Database connection error", 500
        cur = conn.cursor()
        cur.execute('SELECT * FROM products')
        products = cur.fetchall()
        print("products fetched:", products)  
        cur.close()
        conn.close()
        return render_template('products.html', items=products)
    except Exception as e:
        print("Error fetching data:", e)
        return "Error fetching data", 500

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id = request.form.get('item_id')
    if not item_id:
        flash("No item selected to add to cart.")
        return redirect(url_for('products'))

    try:
        conn = get_connection()
        if conn is None:
            flash("Database connection error.")
            return redirect(url_for('products'))
        cur = conn.cursor()
        cur.execute('SELECT * FROM products WHERE id = %s', (item_id,))
        product = cur.fetchone()
        cur.close()
        conn.close()

        if not product:
            flash("Product not found.")
            return redirect(url_for('products'))
        if 'cart' not in session:
            session['cart'] = {}

        cart = session['cart']

        if item_id in cart:
            cart[item_id]['quantity'] += 1
        else:
            cart[item_id] = {
                'name': product[1],
                'description': product[2],
                'price': float(product[3]),
                'image': product[4],  
                'date': product[5],
                'quantity': 1
            }

        session['cart'] = cart  
        flash(f"Added {product[1]} to cart.")
        return redirect(url_for('products'))

    except Exception as e:
        print("Error adding to cart:", e)
        flash("An error occurred while adding the item to the cart.")
        return redirect(url_for('products'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    item_id = request.form.get('item_id')
    if not item_id:
        flash("No item specified for removal.")
        return redirect(url_for('cart'))
    
    cart = session.get('cart', {})
    if item_id in cart:
        removed_item = cart.pop(item_id)
        session['cart'] = cart  
        flash(f"Removed {removed_item['name']} from cart.")
    else:
        flash("Item not found in cart.")

    return redirect(url_for('cart'))
@app.route('/identify_fruit')
def identify_fruit_page():
    return render_template('identify_fruit.html')

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, total=total)

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

@app.route('/identify-fruit', methods=['POST'])
def identify_fruit():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join("temp", file.filename)
    file.save(filepath)

    img = image.load_img(filepath, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    predictions = model.predict(img_array)
    decoded = decode_predictions(predictions, top=1)[0][0]

    os.remove(filepath)

    return jsonify({
        "name": decoded[1],  
        "probability": float(decoded[2])  
    })

if __name__ == '__main__':
    os.makedirs("temp", exist_ok=True)
    app.run(debug=True)
