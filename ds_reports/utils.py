from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, COMMASPACE
from swiftclient.service import SwiftService, SwiftUploadObject, Connection
from swiftclient.exceptions import ClientException
from os.path import basename
from time import sleep
import logging
import smtplib
import requests
import json
import os


logger = logging.getLogger("DocReportsLogger")


def send_mail(to, config, subject, file_name):

    msg = MIMEMultipart()
    msg['From'] = config["verified_email"]
    if isinstance(to, list):
        to = COMMASPACE.join(to)
    msg['To'] = to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText("Please find the attached file"))
    with open(file_name, "rb") as f:
        part = MIMEApplication(
            f.read(),
            Name=basename(file_name)
        )
    part['Content-Disposition'] = 'attachment; filename="%s"' % basename(file_name)
    msg.attach(part)

    conn = smtplib.SMTP(
        host=config["smtp_server"],
        port=config["smtp_port"],
    )
    if config.get('use_tls', True):
        conn.starttls()
    if config.get('use_auth'):
        conn.login(
            config["username"],
            config["password"],
        )
    conn.sendmail(config["verified_email"], to, msg.as_string())
    conn.close()


def get_swift_connection(options):
    connection = Connection(
        authurl=options["os_auth_url"],
        auth_version=options["auth_version"],
        user=options["os_username"],
        key=options["os_password"],
        os_options={
            'user_domain_name': options["os_user_domain_name"],
            'project_domain_name': options["os_project_domain_name"],
            'project_name': options["os_project_name"]
        },
        insecure=options["insecure"]
    )
    return connection


def get_files_from_swift_container(connection, container_name):
    try:
        _, files = connection.get_container(container_name)
    except ClientException as e:
        if e.http_status == 404:
            logger.warning("Container '{}' not found".format(container_name))
        else:
            raise
    else:
        return files


def upload_files_to_swift(files, config):
    upload_objects = []
    for file_name in files:
        upload_objects.append(
            SwiftUploadObject(
                file_name,
                object_name=basename(file_name)
            )
        )
    if upload_objects:
        with SwiftService(options=config) as swift:
            for r in swift.upload(config["put_container"], upload_objects):
                if r['success']:
                    if 'object' in r:
                        yield r["path"]  # file is uploaded
                else:
                    logger.error(r)


def get_doc_logs_from_es(es_host, es_index, start, end, limit=1000, wait_sec=10):
    total = 1
    offset = 0

    while offset < total:
        total = 0
        request_body = (
            {
                "index": [es_index],
            },
            {
                "query": {
                    "bool": {
                        "must": [
                            {"match_phrase": {"MESSAGE_ID": {"query": "uploaded_document"}}},
                            {"range": {"@timestamp": {
                                "gte": int(start.timestamp() * 1000),
                                "lte": int(end.timestamp() * 1000),
                                "format": "epoch_millis"
                            }}}
                        ],
                    }
                },
                "from": offset,
                "size": limit,
                "sort": [{"@timestamp": {"order": "asc", "unmapped_type": "boolean"}}],
                "_source": {"includes": [
                    "USER", "REMOTE_ADDR", "DOC_ID", "DOC_HASH", "TIMESTAMP", "@timestamp",
                ]},
            }
        )
        headers = {
            "kbn-version": "5.6.2",
        }
        response = requests.post("{}/_msearch".format(es_host),
                                 data="\n".join(json.dumps(e) for e in request_body) + "\n",
                                 headers=headers)
        if response.status_code != 200:
            logger.error("Unexpected response {}:{}".format(response.status_code, response.text))
            sleep(wait_sec)
            continue
        else:
            resp_json = response.json()
            response = resp_json["responses"][0]
            hits = response["hits"]
            total = hits["total"]
            logger.info(
                "Got {} hits from total {} with offset {}: from {} to {}".format(
                    len(hits["hits"]), total, offset,
                    hits["hits"][0]["_source"]["TIMESTAMP"],
                    hits["hits"][-1]["_source"]["TIMESTAMP"]
                )
            )
            offset += limit
            yield from hits["hits"]


def ensure_dir_exists(name):
    if not os.path.exists(name):
        os.makedirs(name)


class ReportFilesManager:

    def __init__(self, directory,  suffix):
        self.directory = directory
        self.suffix = suffix
        self.descriptors = {}
        self.fields = ("TIMESTAMP", "DOC_ID", "DOC_HASH", "REMOTE_ADDR")

        ensure_dir_exists(self.directory)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        logger.info("Closing files..")
        for d in self.descriptors.values():
            try:
                d.close()
            except IOError as e:
                logger.exception(e)

    def write(self, data):
        file_name = "{}-{}.csv".format(data["USER"], self.suffix)
        if file_name not in self.descriptors:
            full_name = os.path.join(self.directory, file_name)
            logger.info("New report file {}".format(full_name))
            if os.path.exists(full_name):
                logger.info("Removing stale data from {}".format(full_name))
                os.remove(full_name)

            report_file = open(full_name, "a")
            report_file.write(",".join(k for k in self.fields) + "\n")

            self.descriptors[file_name] = report_file
        else:
            report_file = self.descriptors[file_name]

        report_file.write(
            ",".join(data[k] for k in self.fields) + "\n"
        )
