from setuptools import setup

setup(
    name="spinn_breakout",
    version="0.1.0",
    packages=['spinn_breakout',],
    package_data={'spinn_breakout.model_binaries': ['*.aplx']},
    install_requires=['spynnaker']
)
