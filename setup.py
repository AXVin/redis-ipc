import re
from setuptools import setup

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

long_description = ''
with open("README.md") as f:
    long_description = f.read()

version = ''
with open('redisipc/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

setup(
    name='redis-ipc',
    description='A minimal multi producer single consumer IPC using redis pub/sub',
    author='AXVin',
    version=version,
    license='AGPL v3',
    url='https://github.com/AXVin/redis-ipc',
    keywords=['aioredis', 'redis', 'ipc'],
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: OS Independent',
        'Topic :: Communications',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Typing :: Typed',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)'
    ],
    packages=['redisipc'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
)
