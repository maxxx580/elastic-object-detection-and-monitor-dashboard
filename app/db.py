import click
import mysql.connector
from flask import current_app, g
from flask.cli import with_appcontext

config = {
        'username':'root',
        'password':'password',
        'host':"127.0.0.1",
        'port':3306,
        'db':'ece1779'
}

def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db = mysql.connector.connect(
                user=config['username'],
                password=config['password'],
                host=config['host'],
                database=config['db'],
                port=config['port'])
    return g.db

def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_db():
    """Clear existing data and create new tables."""
    db = get_db()
    cur = db.cursor()
    with current_app.open_resource("setup.sql") as f:
        cur.execute(f.read().decode("utf8"), multi=True)

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
