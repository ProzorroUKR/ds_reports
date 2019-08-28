from setuptools import setup

setup(
    name='ds_reports',
    version='0.1.8',
    packages=['ds_reports'],
    install_requires=[
        'python-swiftclient==3.6.0',
        'python-keystoneclient==3.18.0',
        'requests',
        'pytz',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'prepare_reports=ds_reports.report:prepare_reports',
            'sign_reports_from_tmp_and_send=ds_reports.report:sign_reports_from_tmp_and_send',
            'send_reports=ds_reports.report:send_reports',
        ],
    },
)
