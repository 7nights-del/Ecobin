from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserQuery(db.Model):
    __tablename__ = 'user_queries'
    
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    matched_item = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    tip = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserQuery {self.item_name} -> {self.category}>'

class Donation(db.Model):
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='KES')
    payment_method = db.Column(db.String(20), nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100))
    intasend_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Donation {self.email} - {self.amount} {self.currency}>'

class WasteItem(db.Model):
    __tablename__ = 'waste_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    tip = db.Column(db.Text, nullable=False)
    synonyms = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WasteItem {self.name} - {self.category}>'