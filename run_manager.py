import logging
from manager import create_app

manager_app = create_app()
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    manager_app.run(debug=True)
