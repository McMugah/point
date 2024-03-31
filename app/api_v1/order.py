from flask import request
from . import api
from ..decorators import json
from..model import Product, Order, OrderItem
from app import db


# Route to create a new order
@api.route('/orders', methods=['POST'])
@json
def create_order():
    data = request.json
    user_id = data.get('user_id')
    items = data.get('items')
    order = Order(user_id=user_id)
    db.session.add(order)
    db.session.commit()
    for item_data in items:
        product_id = item_data.get('product_id')
        quantity = item_data.get('quantity')
        product = Product.query.get(product_id)
        OrderItem.create(order, product, quantity)
    return {}, 201, {"Location": order.get_url()}


# Route to get details of a specific order
@api.route('/orders/<int:id>', methods=['GET'])
@json
def get_order(id):
    order = Order.query.get_or_404(id)
    return order.export_data()


# Route to cancel an order
@api.route('/orders/<int:id>', methods=['DELETE'])
@json
def cancel_order(id):
    order = Order.query.get_or_404(id)
    order.cancel()
    return {}, 204


# Route to update status of an order
@api.route('/orders/<int:id>', methods=['PATCH'])
@json
def update_order_status(id):
    data = request.json
    new_status = data.get('status')
    order = Order.query.get_or_404(id)
    order.update_status(new_status)
    return order.export_data()


# Route to get all items of a specific order
@api.route('/orders/<int:id>/items', methods=['GET'])
@json
def get_order_items(id):
    order = Order.query.get_or_404(id)
    items = order.items
    return [item.export_data() for item in items]


# Route to add items to an order
@api.route('/orders/<int:id>/items', methods=['POST'])
@json
def add_order_items(id):
    order = Order.query.get_or_404(id)
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    product = Product.query.get_or_404(product_id)
    OrderItem.create(order, product, quantity)
    return {}, 201


# Route to remove an item from an order
@api.route('/orders/<int:order_id>/items/<int:item_id>', methods=['DELETE'])
@json
def delete_order_item(order_id, item_id):
    order_item = OrderItem.query.filter_by(order_id=order_id, id=item_id).first_or_404()
    order_item.delete()
    return {}, 204


@api.route('/order_items', methods=['POST'])
@json
def create_order_item():
    data = request.json
    order_id = data.get('order_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    order = Order.query.get(order_id)
    product = Product.query.get(product_id)
    if order and product:
        OrderItem.create(order, product, quantity)
        return {}, 201
    else:
        return {"message": "Order or product not found."}, 404


@api.route('/order_items/<int:id>', methods=['GET'])
@json
def get_order_item(id):
    order_item = OrderItem.query.get_or_404(id)
    return order_item.export_data()


@api.route('/order_items/<int:id>', methods=['PUT'])
@json
def update_order_item(id):
    order_item = OrderItem.query.get_or_404(id)
    data = request.json
    order_item.import_data(data)
    db.session.commit()
    return {}, 200
