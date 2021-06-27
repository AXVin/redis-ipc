from setuptools import setup

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

setup(
    name='redis-ipc',
    description='A minimal multi producer single consumer IPC using redis pub/sub',
    author='AXVin',
    url='https://github.com/AXVin/redis-ipc',
    keywords=['aioredis', 'redis', 'ipc'],
    install_requires=requirements,
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
    ],
    packages=['redisipc'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8"
)
