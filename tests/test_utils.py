from unittest.mock import patch, call
from ds_reports.utils import DirectoryLock
from time import sleep
import unittest
import os

test_pre_qualification_procedures = (
    'fake_qualification_pro',
)
test_qualification_procedures = (
    'fake_pre_qualification_pro',
)


class DirectoryLockTestCase(unittest.TestCase):

    def test_file_creation(self):
        lock_dir = "./lock_dir"

        with DirectoryLock(lock_dir) as l:
            self.assertTrue(os.path.exists(os.path.join(lock_dir, l.file_name)))

        self.assertFalse(os.path.exists(os.path.join(lock_dir, l.file_name)))

    @patch("ds_reports.utils.sleep")
    def test_conflict(self, sleep_mock):
        lock_dir = "./lock_dir"

        with DirectoryLock(lock_dir) as l:
            self.assertTrue(os.path.exists(os.path.join(lock_dir, l.file_name)))

            with self.assertRaises(IOError) as assertion:
                with DirectoryLock(lock_dir):
                    pass
            self.assertEqual(assertion.exception.args[0], "{} is locked".format(lock_dir))
            sleep_mock.assert_not_called()

            self.assertTrue(os.path.exists(os.path.join(lock_dir, l.file_name)))

        self.assertFalse(os.path.exists(os.path.join(lock_dir, l.file_name)))

    @patch("ds_reports.utils.sleep")
    def test_conflict_with_timeout(self, sleep_mock):
        sleep_mock.side_effect = sleep
        lock_dir = "./lock_dir"

        with DirectoryLock(lock_dir) as l:
            self.assertTrue(os.path.exists(os.path.join(lock_dir, l.file_name)))

            with self.assertRaises(IOError) as assertion:
                with DirectoryLock(lock_dir, timeout=1, retry_interval=.5):
                    pass
            self.assertEqual(assertion.exception.args[0], "{} is locked".format(lock_dir))
            self.assertEqual(
                sleep_mock.call_args_list,
                [
                    call(.5),
                    call(.5)
                ]
            )

            self.assertTrue(os.path.exists(os.path.join(lock_dir, l.file_name)))

        self.assertFalse(os.path.exists(os.path.join(lock_dir, l.file_name)))
