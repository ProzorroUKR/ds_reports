from unittest.mock import patch
from ds_reports.utils import send_reports_to_broker, REPORT_EMAIL_SUBJECT
import unittest


class SendReportsTestCase(unittest.TestCase):

    kwargs = dict(
        email="aleksey.stryukov@raccoongang.com",
        name="test_broker",
        email_config=dict(
            smtp_server="smtp.gmail.com",
            smtp_port="587",
            verified_email="aleksey.stryukov@gmail.com",
            use_tls=True,
            use_auth=True,
            username="aleksey.stryukov@gmail.com",
            password="dopleroopick",
        ),
        directory="./ds_reports",
        report_month="2019-07",
        max_bytes_limit=2e+3,
    )

    @patch("ds_reports.utils.send_mail")
    def test_send_multiple_reports(self, send_mail_mock):
        send_reports_to_broker(**self.kwargs)
        self.assertGreater(len(send_mail_mock.call_args_list), 2)
        first, second, *_ = send_mail_mock.call_args_list

        self.assertEqual(first[1]["subject"], "DS Uploads Report for {} part 1".format(self.kwargs["report_month"]))
        self.assertEqual(second[1]["subject"], "DS Uploads Report for {} part 2".format(self.kwargs["report_month"]))

        kwargs = first[1]
        kwargs.pop("subject")
        self.assertEqual(
            kwargs,
            dict(
                to=self.kwargs["email"],
                config=self.kwargs["email_config"],
                file_name="{}-{}-part-1.zip".format(self.kwargs["directory"], self.kwargs["report_month"])
            )
        )

    @patch("ds_reports.utils.send_mail")
    def test_single_reports(self, send_mail_mock):
        kwargs = dict(**self.kwargs)
        kwargs["max_bytes_limit"] = 5e+7
        send_reports_to_broker(**kwargs)

        send_mail_mock.assert_called_once_with(
            to=self.kwargs["email"],
            config=self.kwargs["email_config"],
            subject=REPORT_EMAIL_SUBJECT.format(month=self.kwargs["report_month"]),
            file_name="{}-{}.zip".format(self.kwargs["directory"], self.kwargs["report_month"])
        )


