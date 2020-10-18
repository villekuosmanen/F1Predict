import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='F1Predict',
    version='1.0dev',
    author="Ville Kuosmanen",
    description="Tools for predicting Formula 1 Grand Prix results",
    long_description=long_description,
    url="https://github.com/villekuosmanen/F1Predict",
    packages=['f1predict', ],
)
