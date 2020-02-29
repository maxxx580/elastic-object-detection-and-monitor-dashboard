import logging
from app import create_app, db


user_app = create_app()

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    user_app.run(debug=True)
