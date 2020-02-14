from setuptools import find_packages, setup
try:
    # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:
    # for pip <= 9.0.3
    from pip.req import parse_requirements


def load_requirements(fname):
    reqs = parse_requirements(fname, session='installation')
    return [str(ir.req) for ir in reqs]


setup(
    name='ece1779-a1',
    version='1.0.0',
    zip_safe=False,
    install_requires=load_requirements('setup/requirements.txt')
)
