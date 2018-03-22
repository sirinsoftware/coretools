from __future__ import (unicode_literals, print_function, absolute_import)
from builtins import str
import time
from iotile.core.hw.hwmanager import HardwareManager
from iotile.core.exceptions import ArgumentError

class VerifyDeviceStep(object):
    """A Recipe Step used to verify that a device is setup as expected

    Args:
        port (str) : Port used to connect with device
        connect_direct () : Optional arg. Connection string to connect to target
            controller. Defaults to connect_direct 1
        connect (int) : Optional arg. Old UUID to connect to POD to. Defaults
            to using connect_direct 1
        os_tag (int): Optional. Expected os tag to check against in cloud
        os_version (str): Optional. Expected os version to check against in cloud.
            format is "X.Y"
        app_tag (int): Optional. Expected app tag to check against in cloud
        app_version (str): Optional. Expected app version to check against in cloud.
            format is "X.Y"
        realtime_streams (list of int): Optional. List of expected realtime streams variables
            that should be expected upon streaming enabling. If entered in hex, should have 
            the format 0x1XXX. Example: 0x100F
        tile_versions (dict of int: str): Optional. Dictionary of addresses to expection version 
            strings with format "(X, Y, Z)". Example:  8: "(2, 11, 0)"
    """
    def __init__(self, args):
        if args.get('port') is None:
            raise ArgumentError("VerifyDeviceStep Parameter Missing", parameter_name='port')
        self._port              = args['port']
        self._connect           = args.get('connect')
        self._connect_direct    = args.get('connect_direct', 1)

        self._os_tag            = args.get('os_tag')
        self._os_version        = args.get('os_version')
        self._app_tag           = args.get('app_tag')
        self._app_version       = args.get('app_version')

        self._realtime_streams  = args.get('realtime_streams')
        self._tile_versions     = args.get('tile_versions')

    def _verify_tile_versions(self, hw):
        """Verify that the tiles have the correct versions
        """
        for tile, expected_tile_version in self._tile_versions.items():
            actual_tile_version = str(hw.get(tile).tile_version())
            if expected_tile_version != actual_tile_version:
                raise ArgumentError("Tile has incorrect firmware", tile=tile, \
                    expected_version=expected_tile_version, actual_version=actual_tile_version)

    def _verify_os_app_settings(self, hw):
        """Change os and app tags/versions and verify that they've been changed
        """
        con = hw.controller()
        rb = con.remote_bridge()
        rb.create_script()
        if self._os_tag is not None:
            rb.add_setversion_action('os', self._os_tag, self._os_version)
        if self._app_tag is not None:
            rb.add_setversion_action('app', self._app_tag, self._app_version)
        info = con.test_interface().get_info()
        rb.send_script()
        rb.wait_script()

        info = con.test_interface().get_info()
        if self._os_tag is not None:
            if info['os_tag'] != self._os_tag:
                raise ArgumentError("Incorrect os_tag", actual_os_tag=info['os_tag'],\
                        expected_os_tag=self._os_tag)
        if self._app_tag is not None:
            if info['app_tag'] != self._app_tag:
                raise ArgumentError("Incorrect app_tag", actual_os_tag=info['app_tag'],\
                        expected_os_tag=self._app_tag)
        if self._os_version is not None:
            if info['os_version'] != self._os_version:
                raise ArgumentError("Incorrect os_version", actual_os_version=info['os_version'],\
                        expected_os_version=self._os_version)
        if self._app_version is not None:
            if info['app_version'] != self._app_version:
                raise ArgumentError("Incorrect app_version", actual_os_version=info['app_version'],\
                        expected_os_version=self._app_version)

    def _verify_realtime_streams(self, hw):
        """Check that the realtime streams are being produced
        """
        hw.enable_streaming()
        print("--> Testing realtime data (takes 2 seconds)")
        time.sleep(2.1)
        reports = [x for x in hw.iter_reports()]
        reports_seen = {key: 0 for key in self._realtime_streams}

        for report in reports:
            stream_value = report.visible_readings[0].stream
            print(stream_value)
            if reports_seen.get(stream_value) is not None:
                reports_seen[stream_value] += 1

        for stream in reports_seen.keys():
            if reports_seen[stream] < 2:
                raise ArgumentError("Realtime Stream not pushing any reports", stream=reports_seen)

    def run(self):
        with HardwareManager(port=self._port) as hw:
            if self._connect is not None:
                hw.connect(self._connect)
            else:
                hw.connect_direct(self._connect_direct)

            if self._tile_versions is not None:
                print('--> Verifying tile versions')
                self._verify_tile_versions(hw)

            if self._os_tag is not None or self._app_tag is not None:
                print('--> Verifying os/app tags and versions')
                self._verify_os_app_settings(hw)

            if self._realtime_streams is not None:
                print('--> Verifying realtime streams')
                self._verify_realtime_streams(hw)