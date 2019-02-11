#!/usr/local/bin/python
from utils import (
    send_mail,
    get_swift_connection,
    get_files_from_swift_container,
    get_doc_logs_from_es,
    ensure_dir_exists,
    ReportFilesManager,
    upload_files_to_swift,
)
from datetime import datetime, timedelta
import tempfile
import argparse
import urllib3
import logging
import logging.config
import requests
import zipfile
import shutil
import pytz
import yaml
import os
import re


urllib3.disable_warnings()
logger = logging.getLogger("DocReportsLogger")


def get_config():
    parser = argparse.ArgumentParser(description="Openprocurement Billing")
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-f', '--send_from')
    parser.add_argument('-t', '--send_to')
    args = parser.parse_args()
    with open(args.config) as f:
        config = yaml.load(f)

    logging.config.dictConfig(config["logging"])

    # dates for report logs
    current_timezone = config["main"].get("timezone", "Europe/Kiev")
    now = datetime.now(tz=pytz.timezone(current_timezone))
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=1)
    end = today - timedelta(seconds=1)
    config["main"]["start"] = start
    config["main"]["end"] = end

    # get the dates to save report for
    send_to = (today.replace(day=1) - timedelta(seconds=1)).date()
    send_from = send_to.replace(day=1)
    if args.send_to:
        send_to = datetime.strptime(args.send_to, "%Y-%m-%d").date()
        if not args.send_from:
            # set the beginning of the month
            send_from = send_to.replace(day=1)
    if args.send_from:
        send_from = datetime.strptime(args.send_from, "%Y-%m-%d").date()
        if not args.send_to:
            # set the end of the month
            send_to = (send_from.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    assert send_to > send_from, "Valid time interval"
    assert send_to.year == send_from.year and send_to.month == send_from.month, "Send reports within a month!"
    config["main"]["send_from"] = send_from
    config["main"]["send_to"] = send_to
    config["main"]["send_month"] = str(send_from)[:7]

    # data containers
    if config["main"].get("directory") is None:
        config["main"]["directory"] = os.path.join(
            tempfile.gettempdir(),
            config["main"]["temp_dir_name"]
        )
    if config["swift"].get("put_container") is None:
        config["swift"]["put_container"] = "{}-{}".format(
            config["swift"]["container_prefix"], str(start.date())[:7]
        )
    if config["swift"].get("get_container") is None:
        config["swift"]["get_container"] = "{}-{}".format(
            config["swift"]["container_prefix"], config["main"]["send_month"]
        )
    return config


def prepare_reports():
    config = get_config()
    main_config = config["main"]
    logger.info("Report time range: {} - {}".format(main_config["start"], main_config["end"]))

    # fill the directory with report files
    es_host, es_index = config["es"]["host"], config["es"]["index"]
    with ReportFilesManager(main_config["directory"], str(main_config["start"].date())) as rf_manager:
        for hit in get_doc_logs_from_es(es_host, es_index, main_config["start"], main_config["end"]):
            rf_manager.write(hit["_source"])

    sign_reports_from_tmp_and_send()


def sign_reports_from_tmp_and_send(config=None):
    config = config or get_config()
    directory = config["main"]["directory"]

    if os.path.isdir(directory):
        upload_zip_files = set()
        logger.info("Looking for csv files in {}".format(directory))
        for name in os.listdir(directory):
            file_name = os.path.join(directory, name)
            if os.path.isfile(file_name):
                if name.endswith(".csv"):
                    zip_file_name = sign_and_zip_file(file_name, config["sign_api"])
                    if zip_file_name:
                        upload_zip_files.add(zip_file_name)
                elif name.endswith(".zip"):
                    upload_zip_files.add(file_name)

        for file_path in upload_files_to_swift(upload_zip_files, config["swift"]):
            os.remove(file_path)  # file is uploaded

    else:
        logger.info("{} not found".format(directory))


def sign_and_zip_file(file_name, sign_api_config):
    zip_file_name = "{}.zip".format(file_name[:-4])
    sign_file_name = "{}.p7s".format(file_name)

    if not os.path.isfile(zip_file_name):
        if not os.path.isfile(sign_file_name):
            try:
                response = requests.post(
                    sign_api_config["sign_file_url"],
                    files=dict(file=open(file_name)),
                    auth=(sign_api_config["username"], sign_api_config["password"]),
                )
            except requests.exceptions.RequestException as e:
                logger.exception(e)
                return
            else:
                if response.status_code != 200:
                    logger.error(
                        "Signing has failed: {} {}".format(response.status_code, response.text)
                    )
                    return

                with open(sign_file_name, "wb") as f:
                    f.write(response.content)

        # zipping two files in a single .zip
        with zipfile.ZipFile(zip_file_name, "w") as zip:
            with zip.open(file_name.split("/")[-1], "w") as f:
                f.write(open(file_name, "rb").read())
            with zip.open(sign_file_name.split("/")[-1], "w") as f:
                f.write(open(sign_file_name, "rb").read())

    # removing initial files
    os.remove(file_name)
    if os.path.isfile(sign_file_name):
        os.remove(sign_file_name)

    return zip_file_name


FILE_REGEX = re.compile(r"(?P<broker>.*)-(?P<date>\d{4}-\d{2}-\d{2})\.zip")


def send_reports():
    config = get_config()
    main_config = config["main"]
    send_from, send_to = str(main_config["send_from"]), str(main_config["send_to"])
    logger.info("Send reports: {} - {}".format(send_from, send_to))

    options = config["swift"]
    connection = get_swift_connection(options)
    files = get_files_from_swift_container(connection, options["get_container"])
    if files:
        with tempfile.TemporaryDirectory(prefix="send_data_", dir=config["main"]["directory"]) as tmp_dir:
            # get reports
            for data in files:
                match = FILE_REGEX.match(data["name"])
                if match:
                    if send_from <= match.group("date") <= send_to:
                        _, file_data = connection.get_object(options["get_container"], data["name"])
                        broker_dir_name = os.path.join(tmp_dir, match.group("broker"))
                        ensure_dir_exists(broker_dir_name)
                        with open(os.path.join(broker_dir_name, data["name"]), 'wb') as f:
                            f.write(file_data)

            # zip reports and send emails
            brokers_emails = config["brokers_emails"]
            for name in os.listdir(tmp_dir):
                full_name = os.path.join(tmp_dir, name)
                if os.path.isdir(full_name):
                    if name in brokers_emails:
                        archive_name = "{}-{}".format(full_name, main_config["send_month"])
                        shutil.make_archive(archive_name, 'zip', full_name)
                        send_mail(
                            to=brokers_emails[name],
                            config=config["email"],
                            subject="DS Uploads Report for {}".format(main_config["send_month"]),
                            file_name="{}.zip".format(archive_name)
                        )
                        logger.info("Email is sent to {}".format(name))
                    else:
                        logger.warning("Email address not found for {}".format(name))


if __name__ == "__main__":
    prepare_reports()
    # sign_reports_from_tmp_and_send()
    send_reports()
