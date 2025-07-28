from flask import Flask
from models.sql import db, create_tables
from controllers.routes import main_routes

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = 'devkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main_routes)

    # Create tables and admin
    with app.app_context():
        create_tables()

    return app

# Run the app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
