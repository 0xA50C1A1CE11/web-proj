from setuptools import setup

setup(
    name='yafr-utils',
    version='0.1',
    py_modules=['utils'],
    packages=['yafr'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        utils=utils:cli
    ''',
)
