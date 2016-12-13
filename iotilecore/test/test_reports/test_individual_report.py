import unittest
import os
import pytest
from iotile.core.exceptions import *
from iotile.core.hw.reports.individual_format import IndividualReadingReport
from iotile.core.hw.reports.report import IOTileReading
import struct
import datetime

def make_report(uuid, stream, value, timestamp, sent_time):
    return struct.pack("<BBHLLLL", 0, 0, stream, uuid, sent_time, timestamp, value)

def test_parsing_str():
    """Make sure we can parse a report as a string
    """

    report_data = make_report(10, 1, 2, 3, 4)
    received_time = datetime.datetime.utcnow()

    report = IndividualReadingReport(str(report_data), received_time=received_time)

    assert report.decoded is True
    assert len(report.visible_readings) == 1
    assert report.signed is False
    assert report.encrypted is False
    assert report.origin == 10

    reading = report.visible_readings[0]

    assert reading.stream == 1
    assert reading.value == 2
    assert reading.raw_time == 3
    assert reading.reading_time is not None

    reading_time = received_time + datetime.timedelta(seconds=-1)
    assert reading.reading_time == reading_time

def test_parsing_bytearray():
    """Make sure we can parse a report as a bytearray
    """

    report_data = make_report(10, 1, 2, 3, 4)
    received_time = datetime.datetime.utcnow()

    report = IndividualReadingReport(bytearray(report_data), received_time=received_time)

    assert report.decoded is True
    assert len(report.visible_readings) == 1
    assert report.signed is False
    assert report.encrypted is False
    assert report.origin == 10

    reading = report.visible_readings[0]

    assert reading.stream == 1
    assert reading.value == 2
    assert reading.raw_time == 3
    assert reading.reading_time is not None

    reading_time = received_time + datetime.timedelta(seconds=-1)
    assert reading.reading_time == reading_time

def test_encoding():
    report_data = make_report(10, 1, 2, 3, 4)
    received_time = datetime.datetime.utcnow()

    report_data = bytearray(report_data)
    report = IndividualReadingReport(report_data, received_time=received_time)

    report_data2 = report.encode()
    assert report_data2 == report_data

def test_fromreadings():
    """Make sure we can create this report dynamically from a list of readings
    """
    report = IndividualReadingReport.FromReadings(10, [IOTileReading(3, 1, 2)])

    assert report.decoded is True
    assert len(report.visible_readings) == 1
    assert report.signed is False
    assert report.encrypted is False
    assert report.origin == 10

    reading = report.visible_readings[0]

    assert reading.stream == 1
    assert reading.value == 2
    assert reading.raw_time == 3
    assert reading.reading_time is not None

def test_serialization():
    """Make sure we can turn this report into a dictionary object without losing data
    """

    report_data = make_report(10, 1, 2, 3, 4)
    received_time = datetime.datetime.utcnow()

    report = IndividualReadingReport(report_data, received_time=received_time)

    ser = report.serialize()
    assert ser['received_time'] == received_time
    assert ser['origin'] == 10
    assert ser['report_format'] == IndividualReadingReport.ReportType