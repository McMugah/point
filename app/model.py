from datetime import datetime
from flask_login import UserMixin
from flask import url_for
from .exceptions import ValidationError
from . import bcrypt, db, login_manager




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
        return {
            'self_url': self.get_url(),
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'quantity': self.quantity,
            'created_at': self.created_at,
            'order_items_url': url_for('api.get_product_order_items', id=self.id,
                                      _external=True),
            'cart_url': url_for('api.get_cart_products', id=self.id)
        }

    def import_data(self, data):
        try:
            self.name = data['name']
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


class OrderItem(db.Model):
    __tablename__ = "order_item"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<OrderItem {self.id}>"

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


class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("CartItem", backref="cart", lazy=True)


    def __repr__(self):
        return f"<Cart {self.id}>"

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
