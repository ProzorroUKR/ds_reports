from setuptools import setup, find_packages

setup(
    name="ds_reports",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-swiftclient==3.6.0',
        'python-keystoneclient==3.18.0',
        'requests',
        'pytz',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'build_report=report:main',
        ],
    },
    package_data={'': ['config.yaml']},
)
