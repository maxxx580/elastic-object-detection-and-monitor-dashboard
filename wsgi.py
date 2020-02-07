import logging
from app import create_app

webapp = create_app()
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    webapp.run(debug=True)
