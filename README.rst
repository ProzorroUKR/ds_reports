DS Upload Reports
=================

Setup
-----

1.
``python3 -m venv .``

2.
``./bin/pip install -e .``

3.
See config.yaml and modify

4.
JOURNAL_PREFIX env var should be the same as in openprocurement.documentservice

Three commands are available
----------------------------

``./bin/prepare_reports -c config.yaml``

``./bin/sign_reports_from_tmp_and_send -c config.yaml``

``./bin/send_reports -c config.yaml``


The last one has additional args

``
./bin/send_reports -c .config.yaml -f 2019-02-01
2019-02-11 16:10:07,962 INFO     Send reports: 2019-02-01 - 2019-02-28
``

or

```
./bin/send_reports -c .config.yaml -f 2019-02-01 -t 2019-02-02
2019-02-11 16:18:54,047 INFO     Send reports: 2019-02-01 - 2019-02-02
``