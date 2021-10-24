from setuptools import setup

setup(
    name='BellBot',
    version='0.0.1',
    packages=['bellbot'],
    url='',
    license='',
    author='Itay',
    author_email='5647956+itay-sho@users.noreply.github.com',
    install_requires=[
        'python-telegram-bot',
        'fastapi',
        'uvicorn[standard]'
      ],
    description='BellBot'
)
