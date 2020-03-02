import logging

from manager import create_app


logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)

logging.getLogger('boto').setLevel(logging.INFO)
logging.getLogger('manager').setLevel(logging.INFO)

manager_app = create_app()

if __name__ == "__main__":
    manager_app.run(debug=True)
