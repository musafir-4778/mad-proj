from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from markupsafe import Markup
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from models.sql import db, User, ParkingLot, ParkingSpot, Reservation, create_parking_lot_with_spots

# Blueprint setup
main_routes = Blueprint('main_routes', __name__)



@main_routes.route('/')
def redirect_home():
    return redirect(url_for('main_routes.login'))

@main_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already taken.')
            return redirect(url_for('main_routes.register'))

        new_user = User(username=username, password=generate_password_hash(password), role='user')
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('main_routes.login'))

    return render_template('register.html')

@main_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Default admin (hardcoded)
        if username == 'admin' and password == 'admin123':
            session['user'] = 'admin'
            session['role'] = 'admin'
            return redirect(url_for('main_routes.admin_dashboard'))

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session.update({'user': user.username, 'role': user.role, 'user_id': user.id})
            return redirect(url_for('main_routes.user_dashboard'))

        flash('Login failed. Check credentials.')

    return render_template('login.html')

@main_routes.route('/logout')
def logout():
    session.clear()
    flash("You've been logged out.")
    return redirect(url_for('main_routes.login'))




@main_routes.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('main_routes.login'))

    all_lots = ParkingLot.query.all()
    return render_template('admin_dashboard.html', lots=all_lots)

@main_routes.route('/admin/create_lot', methods=['GET', 'POST'])
def create_lot():
    if session.get('role') != 'admin':
        return redirect(url_for('main_routes.login'))

    if request.method == 'POST':
        data = request.form
        create_parking_lot_with_spots(
            name=data['name'],
            address=data['address'],
            floor=data['floor'],
            price_per_hour=float(data['price']),
            total_spots=int(data['spots'])
        )
        flash("New lot created successfully.")
        return redirect(url_for('main_routes.admin_dashboard'))

    return render_template('create_lot.html')

@main_routes.route('/admin/view_lots')
def view_lots():
    if session.get('role') != 'admin':
        return redirect(url_for('main_routes.login'))

    lots = ParkingLot.query.all()
    return render_template('view_lots.html', lots=lots)

@main_routes.route('/admin/lots/<int:lot_id>/edit', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == 'POST':
        data = request.form
        lot.name = data['name']
        lot.address = data['address']
        lot.floor = int(data['floor'])
        lot.price_per_hour = float(data['price_per_hour'])
        db.session.commit()
        flash("Lot details updated.")
        return redirect(url_for('main_routes.view_lots'))

    return render_template('edit_lot.html', lot=lot)

@main_routes.route('/admin/lots/<int:lot_id>/delete', methods=['POST'])
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()
    flash("Lot deleted successfully.")
    return redirect(url_for('main_routes.view_lots'))

@main_routes.route('/admin/lots/<int:lot_id>/spots')
def admin_view_spots(lot_id):
    if session.get('role') != 'admin':
        return redirect(url_for('main_routes.login'))

    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()
    return render_template('admin_view_spots.html', lot=lot, spots=spots)




@main_routes.route('/user/dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        return redirect(url_for('main_routes.login'))
    return render_template('user_dashboard.html')

@main_routes.route('/user/lots')
def user_view_lots():
    if session.get('role') != 'user':
        return redirect(url_for('main_routes.login'))

    lots = ParkingLot.query.all()
    return render_template('user_lots.html', lots=lots)

@main_routes.route('/user/lots/<int:lot_id>/spots', methods=['GET', 'POST'])
def view_spots(lot_id):
    if session.get('role') != 'user':
        return redirect(url_for('main_routes.login'))

    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()

    if request.method == 'POST':
        spot_id = request.form.get('spot_id')
        spot = ParkingSpot.query.get_or_404(spot_id)

        if spot.status != 'A':
            flash("Selected spot is already occupied.")
            return redirect(url_for('main_routes.view_spots', lot_id=lot_id))

        spot.status = 'O'
        reservation = Reservation(
            user_id=session['user_id'],
            spot_id=spot.id,
            parking_time=datetime.now()
        )
        db.session.add(reservation)
        db.session.commit()
        flash(f"Spot {spot.spot_number} booked.")
        return redirect(url_for('main_routes.user_dashboard'))

    return render_template('view_spots.html', lot=lot, spots=spots)

@main_routes.route('/user/vacate', methods=['GET', 'POST'])
def vacate_spot():
    if session.get('role') != 'user':
        return redirect(url_for('main_routes.login'))

    uid = session.get('user_id')
    active = Reservation.query.filter_by(user_id=uid, leaving_time=None).all()

    if not active:
        flash("No active reservations found.")
        return redirect(url_for('main_routes.user_dashboard'))

    if request.method == 'POST':
        res_id = request.form.get('reservation_id')
        res = Reservation.query.get(res_id)

        if not res or res.user_id != uid:
            flash("Invalid reservation.")
            return redirect(url_for('main_routes.vacate_spot'))

        res.leaving_time = datetime.now()
        duration_hours = (res.leaving_time - res.parking_time).total_seconds() / 3600
        res.cost = round(duration_hours * res.spot.lot.price_per_hour, 2)
        res.spot.status = 'A'
        db.session.commit()

        flash(Markup(f"Spot vacated. Cost: ₹<strong>{res.cost}</strong>"))
        return redirect(url_for('main_routes.user_dashboard'))

    return render_template('vacate_spot.html', reservations=active)

@main_routes.route('/user/history')
def view_user_history():
    if session.get('role') != 'user':
        return redirect(url_for('main_routes.login'))

    uid = session.get('user_id')
    past_reservations = Reservation.query.filter_by(user_id=uid).order_by(Reservation.parking_time.desc()).all()
    return render_template('user_history.html', reservations=past_reservations)
