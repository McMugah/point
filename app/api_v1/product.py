from flask import request,jsonify
from flask_login import login_required
from ..decorators import json
from app import db
from ..model import Product
from . import api


@api.route('/products', methods=['POST'])
@login_required
@json
def new_product():
    product = Product()
    product.import_data(request.json)
    db.session.add(product)
    db.session.commit()
    return {}, 201, {"Location": product.get_url()}


# Route to get all products
@api.route('/products', methods=['GET'])
@login_required
@json
def get_products():
    products = Product.query.all()
    return jsonify([product.export_data() for product in products])


# Route to get a specific product by ID
@api.route('/products/<int:id>', methods=['GET'])
@login_required
@json
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(product.export_data())


# Route to update a product by ID
@api.route('/products/<int:id>', methods=['PUT'])
@login_required
@json
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json
    product.import_data(data)
    db.session.commit()
    return jsonify(product.export_data())


# Route to delete a product by ID
@api.route('/products/<int:id>', methods=['DELETE'])
@login_required
@json
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return '', 204


# Route to get order items associated with a product
@api.route('/products/<int:id>/order_items', methods=['GET'])
@login_required
@json
def get_product_order_items(id):
    product = Product.query.get_or_404(id)
    order_items = product.order_items
    return jsonify([item.export_data() for item in order_items])


# Route to get cart items associated with a product
@api.route('/products/<int:id>/cart_items', methods=['GET'])
@login_required
@json
def get_product_cart_items(id):
    product = Product.query.get_or_404(id)
    cart_items = product.cart_items
    return jsonify([item.export_data() for item in cart_items])