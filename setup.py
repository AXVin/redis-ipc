from setuptools import setup

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='redis-ipc',
    description='A minimal multi producer single consumer IPC using redis pub/sub',
    author='AXVin',
    url='https://github.com/AXVin/redis-ipc',
    keywords=['redis', 'ipc'],
    install_requires=requirements,
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
    ],
    packages=['redisipc'],
)
