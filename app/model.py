from datetime import datetime
from flask import url_for
from flask_login import UserMixin
from . import bcrypt, db, login_manager
from .exceptions import ValidationError


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="customer", lazy=True)


    def __repr__(self):
        return f"<User id={self.id}, username={self.username}>"

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_url(self):
        return url_for('api.get_user', id=self.id, _external=True)

    def export_data(self):
        user_data = {
            'self_url': self.get_url(),
            'username': self.username,
            'email': self.email,
            'orders_url': url_for('api.get_user_orders', id=self.id, _external=True),
            'orders': []
        }
        for order in self.orders:
            order_data = {
                'id': order.id,
                'status': order.status,
                'total_amount': order.total_amount,
                'created_at': order.created_at.isoformat()
            }
            user_data['orders'].append(order_data)
        return user_data

    def import_data(self, data):
        try:
            self.username = data['username']
            self.email = data['email']
        except KeyError as e:
            raise ValidationError('Invalid customer: missing ' + e.args[0])
        return self


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False)  # Quantity in stock
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship("OrderItem", backref="product", lazy=True)
    cart_items = db.relationship("CartItem", backref="product", lazy=True)


    def __repr__(self):
        return f"<Product {self.name}>"

    def get_url(self):
        return url_for('api.get_product', id=self.id, _external=True)


    def export_data(self):
        product_data = {
            'self_url': self.get_url(),
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'quantity': self.quantity,
            'created_at': self.created_at,
        }
        product_data['order_items_url'] = url_for('api.get_product_order_items', id=self.id, _external=True)
        product_data['cart_url'] = url_for('api.get_cart_products', id=self.id, _external=True)
        if self.order_items:
            product_data['order_items'] = [item.export_data() for item in self.order_items]
        if self.cart_items:
            product_data['cart_items'] = [item.export_data() for item in self.cart_items]
        return product_data

    def import_data(self, data):
        try:
            if 'name' in data:
                self.name = data['name']
            if 'price' in data:
                self.price = data['price']
            if 'description' in data:
                self.description = data['description']
            if 'quantity' in data:
                self.quantity = data['quantity']
        except KeyError as e:
            raise ValidationError('Invalid product: missing ' + e.args[0])
        return self


    def reduce_quantity(self, quantity):
        if self.quantity >= quantity:
            self.quantity -= quantity
            db.session.commit()
        else:
            raise ValidationError("Insufficient quantity in stock.")

    def increase_quantity(self, quantity):
        self.quantity += quantity
        db.session.commit()


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    total_amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True)

    def __repr__(self):
        return f"<Order id={self.id}, total_amount={self.total_amount}>"


    def get_total_price(self):
        return sum(item.product.price * item.quantity for item in self.items)


    def update_status(self, new_status):
        self.status = new_status
        db.session.commit()

    @staticmethod
    def get_orders_by_user(user_id):
        return Order.query.filter_by(user_id=user_id).all()

    @classmethod
    def create(cls, order, product, quantity):
        if product.quantity >= quantity:
            order_item = cls(order=order, product=product, quantity=quantity)
            product.reduce_quantity(quantity)
            db.session.add(order_item)
            db.session.commit()
        else:
            raise ValidationError("Insufficient quantity in stock.")

    def cancel(self):
        for item in self.items:
            item.product.increase_quantity(item.quantity)
        db.session.delete(self)
        db.session.commit()


    def import_data(self, data):
        try:
            if 'status' in data:
                self.status = data['status']
            if 'total_amount' in data:
                self.total_amount = data['total_amount']
        except KeyError as e:
            raise ValidationError('Invalid order: missing ' + e.args[0])
        return self


    def export_data(self):
        order_data = {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'total_amount': self.total_amount,
            'created_at': self.created_at.isoformat(),
            'items': []
        }
        for item in self.items:
            item_data = {
                'product_id': item.product.id,
                'quantity': item.quantity,
                'product_name': item.product.name,
                'product_price': item.product.price,
            }
            order_data['items'].append(item_data)
        return order_data


class OrderItem(db.Model):
    __tablename__ = "order_item"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<OrderItem {self.id}>"

    def get_url(self):
        order = Order.query.get(self.order_id)
        if order:
            return url_for('api.get_order', id=order.id, _external=True)
        else:
            return None 

    @classmethod
    def create(cls, order, product, quantity):
        if product.quantity >= quantity:
            order_item = cls(order=order, product=product, quantity=quantity)
            product.reduce_quantity(quantity)
            db.session.add(order_item)
            db.session.commit()
        else:
            raise ValidationError("Insufficient quantity in stock.")

    def cancel(self):
        self.product.increase_quantity(self.quantity)
        db.session.delete(self)
        db.session.commit()

    def get_total_price(self):
        return self.product.price * self.quantity

    def update_status(self, new_status):
        self.status = new_status
        db.session.commit()

    def import_data(self, data):
        try:
            if 'quantity' in data:
                self.quantity = data['quantity']
        except KeyError as e:
            raise ValidationError('Invalid order item: missing ' + e.args[0])
        return self


    def export_data(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_price': self.get_total_price()
        }


class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("CartItem", backref="cart", lazy=True)

    def __repr__(self):
        return f"<Cart {self.id}>"

    def get_url(self):
        return url_for('api.get_cart', id=self.id, _external=True)

    def calculate_total_cost(self):
        return sum(item.product.price * item.quantity for item in self.items)

    @staticmethod
    def update_quantity(session, cart_id, product_id, quantity):
        cart_item = CartItem.query.filter_by(
            cart_id=cart_id, product_id=product_id
        ).first()
        if cart_item:
            cart_item.quantity = quantity
            session.commit()

    @staticmethod
    def remove_item(session, cart_id, product_id):
        cart_item = CartItem.query.filter_by(
            cart_id=cart_id, product_id=product_id
        ).first()
        if cart_item:
            session.delete(cart_item)
            session.commit()

    def import_data(self, data):
        try:
            if 'user_id' in data:
                self.user_id = data['user_id']
            if 'created_at' in data:
                self.created_at = data['created_at']
        except KeyError as e:
            raise ValidationError('Invalid cart: missing ' + e.args[0])
        return self

    def export_data(self):
        cart_data = {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'total_cost': self.calculate_total_cost(),
            'items': []
        }
        for item in self.items:
            item_data = {
                'product_id': item.product_id,
                'quantity': item.quantity,
                'product_name': item.product.name,
                'product_price': item.product.price,
            }
            cart_data['items'].append(item_data)
        return cart_data


class CartItem(db.Model):
    __tablename__ = "cart_item"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<CartItem {self.id}>"

    @property
    def price(self):
        return self.product.price if self.product else None

    def get_url(self):
        return url_for('api.get_cart_item', id=self.id, _external=True)

    def import_data(self, data):
        try:
            if 'cart_id' in data:
                self.cart_id = data['cart_id']
            if 'product_id' in data:
                self.product_id = data['product_id']
            if 'quantity' in data:
                self.quantity = data['quantity']
        except KeyError as e:
            raise ValidationError('Invalid cart item: missing ' + e.args[0])
        return self


    def export_data(self):
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'total_price': self.price * self.quantity,
            'url': self.get_url()
        }


class Checkout(db.Model):
    __tablename__ = "checkout"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    checkout_date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    order = db.relationship("Order")

    def __repr__(self):
        return f"<Checkout {self.id}>"

    def get_url(self):
        return url_for('api.get_checkout', id=self.id, _external=True)

    def import_data(self, data):
        try:
            if 'user_id' in data:
                self.user_id = data['user_id']
            if 'order_id' in data:
                self.order_id = data['order_id']
            if 'checkout_date' in data:
                self.checkout_date = data['checkout_date']
        except KeyError as e:
            raise ValidationError('Invalid checkout: missing ' + e.args[0])
        return self

    def export_data(self):
        user_data = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email
        }
        order_data = {
            'id': self.order.id,
            'status': self.order.status,
            'total_amount': self.order.total_amount
        }
        return {
            'id': self.id,
            'user': user_data,
            'order': order_data,
            'checkout_date': self.checkout_date.isoformat(),
            'url': self.get_url()
        }
