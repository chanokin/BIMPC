from setuptools import setup

# **HACK** spynnaker doesn't have __version__ set properly
# therefore >= 3.0.0, < 4.0.0 doesn't work correctly
setup(
    name="spinn_breakout",
    version="0.1.0",
    packages=['spinn_breakout',],
    package_data={'spinn_breakout.model_binaries': ['*.aplx']},
    install_requires=['spynnaker']
)
