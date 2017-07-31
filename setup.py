from setuptools import setup

setup(
    name='alex2',
    packages=['alex2'],
    include_package_data=True,
    install_requires=[
        'flask','flask-socketio'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)