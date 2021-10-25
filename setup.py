from setuptools import setup

setup(
    name='BellBot',
    version='0.0.1',
    packages=['bellbot', 'intercom-agi'],
    url='',
    license='',
    author='Itay',
    author_email='5647956+itay-sho@users.noreply.github.com',
    install_requires=[
        'pyTelegramBotAPI',
        'fastapi',
        'uvicorn[standard]',
        'pyst2',
        'ffmpeg-python'
      ],
    description='BellBot'
)
