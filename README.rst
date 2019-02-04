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

Run
---

``./bin/build_report -c config.yaml``


Example of the output
---------------------

```
2019-02-04 12:27:57,934 INFO     Report time range: 2019-02-03 00:00:00+02:00 - 2019-02-03 23:59:59+02:00
2019-02-04 12:28:02,588 INFO     Got 1000 hits from total 1406 with offset 0: from 2019-02-03T00:01:52.541959+02:00 to 2019-02-03T18:44:00.515137+02:00
2019-02-04 12:28:02,588 INFO     New report file ./2019-02-03/test.quintagroup.com.csv
2019-02-04 12:28:02,589 INFO     New report file ./2019-02-03/ukrtender.com.ua.csv
2019-02-04 12:28:02,590 INFO     New report file ./2019-02-03/etorgy.ubiz.ua.csv
2019-02-04 12:28:02,591 INFO     New report file ./2019-02-03/zakupki.avi.net.ua.csv
2019-02-04 12:28:04,455 INFO     Got 406 hits from total 1406 with offset 1000: from 2019-02-03T18:44:21.915724+02:00 to 2019-02-03T23:59:14.186970+02:00
2019-02-04 12:28:04,456 INFO     New report file ./2019-02-03/public-bid.com.ua.csv
2019-02-04 12:28:04,458 INFO     Closing files..
Reports uploaded:
https://object-swift-np.dc.prozorro.gov.ua/v1/AUTH_fc6653767e90476b852a605e60295d03/doc-report-dev/public-bid.com.ua.csv?temp_url_sig=63208ac0b66ab55de2a8b164154a4f946a2f2c88&temp_url_expires=3098724980
https://object-swift-np.dc.prozorro.gov.ua/v1/AUTH_fc6653767e90476b852a605e60295d03/doc-report-dev/etorgy.ubiz.ua.csv?temp_url_sig=f26862887e73c0070a4ef921714ef8c16a368de9&temp_url_expires=3098724982
```
