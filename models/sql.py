from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


 User (Admin + Regular)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False)  
    reservations = db.relationship('Reservation', backref='user', lazy=True, cascade='all, delete-orphan')

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    floor = db.Column(db.String(10))  
    price_per_hour = db.Column(db.Float, nullable=False)
    total_spots = db.Column(db.Integer, nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade='all, delete-orphan')


class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), default='A')  
    reservations = db.relationship('Reservation', backref='spot', lazy=True, cascade='all, delete-orphan')


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    parking_time = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_time = db.Column(db.DateTime, nullable=True)
    cost = db.Column(db.Float, nullable=True)


def create_tables():
    db.create_all()

    # Create a default admin if not exists
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()


def create_parking_lot_with_spots(name, address, floor, price_per_hour, total_spots):
    new_lot = ParkingLot(
        name=name,
        address=address,
        floor=floor,
        price_per_hour=price_per_hour,
        total_spots=total_spots
    )
    db.session.add(new_lot)
    db.session.commit()


    
    for i in range(1, total_spots + 1):
        spot = ParkingSpot(
            lot_id=new_lot.id,
            spot_number=i,
            status='A'
        )
        db.session.add(spot)

    db.session.commit()
