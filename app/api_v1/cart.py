from flask import jsonify, request, url_for
from flask_login import login_required
from . import api
from ..model import Cart,CartItem,Checkout,Product,Order,OrderItem
from app import db
from ..decorators import json


@api.route('/carts', methods=['POST'])
@login_required
@json
def create_cart():
    data = request.json
    cart = Cart()
    cart.import_data(data)
    db.session.add(cart)
    db.session.commit()
    return jsonify({'message': 'Cart created successfully', 'cart_id': cart.id}), 201


@api.route('/carts/<int:cart_id>', methods=['GET'])
@login_required
@json
def get_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    return jsonify(cart.export_data())


@api.route('/carts/<int:cart_id>', methods=['PUT'])
@login_required
@json
def update_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    data = request.json
    cart.import_data(data)
    db.session.commit()
    return jsonify({'message': 'Cart updated successfully', 'cart_id': cart.id})


@api.route('/carts/<int:cart_id>', methods=['DELETE'])
@login_required
@json
def delete_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    db.session.delete(cart)
    db.session.commit()
    return jsonify({'message': 'Cart deleted successfully', 'cart_id': cart_id})
from flask import request, jsonify



# Route to add an item to the cart
@api.route('/cart/<int:cart_id>/items', methods=['POST'])
@login_required
@json
def add_to_cart(cart_id):
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    if not product_id or not quantity:
        return jsonify({'error': 'Product ID and quantity are required'}), 400
    cart = Cart.query.get_or_404(cart_id)
    product = Product.query.get_or_404(product_id)
    cart_item = CartItem(cart=cart, product=product, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()
    return jsonify({'message': 'Item added to cart successfully'}), 201


# Route to update the quantity of an item in the cart
@api.route('/cart/<int:cart_id>/items/<int:item_id>', methods=['PUT'])
@login_required
@json
def update_cart_item(cart_id, item_id):
    data = request.json
    quantity = data.get('quantity')
    if not quantity:
        return jsonify({'error': 'Quantity is required'}), 400
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart_id).first_or_404()
    cart_item.quantity = quantity
    db.session.commit()
    return jsonify({'message': 'Cart item quantity updated successfully'})


@api.route('/cart/<int:cart_id>/items/<int:item_id>', methods=['DELETE'])
@login_required
@json
def remove_from_cart(cart_id, item_id):
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart_id).first_or_404()
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Item removed from cart successfully'})


# Route to create a new checkout
@api.route('/checkout', methods=['POST'])
@login_required
def create_checkout():
    data = request.json
    user_id = data.get('user_id')
    order_items = data.get('order_items', [])
    if not user_id or not order_items:
        return jsonify({'error': 'User ID and order items are required'}), 400
    order = Order(user_id=user_id)
    for item in order_items:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        if not product_id or not quantity:
            return jsonify({'error': 'Product ID and quantity are required for each order item'}), 400
        product = Product.query.get_or_404(product_id)
        order_item = OrderItem(order=order, product=product, quantity=quantity)
        db.session.add(order_item)
    checkout = Checkout(user_id=user_id, order=order)
    db.session.add(checkout)
    db.session.commit()
    return jsonify({'message': 'Checkout created successfully', 'checkout_id': checkout.id}), 201


# Route to retrieve checkout details by ID
@api.route('/checkout/<int:checkout_id>', methods=['GET'])
def get_checkout(checkout_id):
    checkout = Checkout.query.get_or_404(checkout_id)
    return jsonify(checkout.export_data())


# Route to update checkout information
@api.route('/checkout/<int:checkout_id>', methods=['PUT'])
def update_checkout(checkout_id):
    data = request.json
    checkout = Checkout.query.get_or_404(checkout_id)
    checkout.import_data(data)
    db.session.commit()
    return jsonify({'message': 'Checkout updated successfully'})


# Route to delete a checkout
@api.route('/checkout/<int:checkout_id>', methods=['DELETE'])
def delete_checkout(checkout_id):
    checkout = Checkout.query.get_or_404(checkout_id)
    db.session.delete(checkout)
    db.session.commit()
    return jsonify({'message': 'Checkout deleted successfully'})
