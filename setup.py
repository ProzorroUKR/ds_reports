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
            'prepare_reports=report:prepare_reports',
            'sign_reports_from_tmp_and_send=report:sign_reports_from_tmp_and_send',
            'send_reports=report:send_reports',
        ],
    },
    package_data={'': ['config.yaml']},
)
