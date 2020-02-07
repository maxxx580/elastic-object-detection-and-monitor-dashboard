from setuptools import find_packages, setup

setup(
    name='app',
    version='0.9.9',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'cffi',
        'Click',
        'dnspython',
        'Flask-Bcrypt',
        'gunicorn',
        'itsdangerous',
        'Jinja2',
        'MarkupSafe',
        'mysql-connector-python',
        'numpy',
        'opencv-contrib-python',
        'protobuf',
        'pycparser',
        'pylint',
        'six',
        'Werkzeug'
    ]
)
