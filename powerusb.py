#!/usr/bin/python
"""
Control one or more PowerUSB power strips

* display the set of connected strips

* Turn a socket on or off
* Read the power state of a socket
* Set the default for a socket
* Turn an entire strip on or off
* read the cumulative power from a strip

* Assign a label to a strip

powerusb --strips

powerusb --status <strip>[:<socket>]

powerusb --socket <strip>:<socket> (-on|-off) [--default]

powerusb --meter <strip> [--cumulative|--reset]]

"""

import argparse
import re
import usb, pyudev

##############################################################################
#
# Argument Parsing
#
##############################################################################

class CommandAction(argparse.Action):
    """
    Parse one of the 5 command actions
    """
    def __call__(self, parser, namespace, values, option_string=None):
        namespace.command = re.sub("^--", "", option_string)
        namespace.socket = values

def parse_command_line():
    """Parse the command line arguments"""

    parser = argparse.ArgumentParser(description="Manage power strips")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--xml", "-x", action="store_true")
    parser.add_argument("--json", "-j", action="store_true")
    cmd_group = parser.add_mutually_exclusive_group()
    cmd_group.add_argument("--strips", "-l", action="store_true")
    cmd_group.add_argument("--status", '-s', metavar="SOCKETSPEC", 
                           action=CommandAction, dest="command", nargs="+")
    cmd_group.add_argument("--socket", "-p", metavar="SOCKETSPEC",
                           action=CommandAction, dest="command", nargs="+")
    cmd_group.add_argument("--meter", "-m", metavar="SOCKETSPEC",
                           action=CommandAction, dest="command", nargs="+")
    on_off = parser.add_mutually_exclusive_group()
    on_off.add_argument("--on", dest="on", action="store_true", default=None) 
    on_off.add_argument("--off", dest="on", action="store_false")
    parser.add_argument("--default", action="store_true")
    parser.add_argument("--cumulative", action="store_true")
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()

###############################################################################
#
# HID Device Library
#
###############################################################################


###############################################################################
#
# PowerUSB Objects
#
###############################################################################

class PowerUSBStrip(object):

    _vendor_id = "04d8"
    _product_id = "003f"
    _product = u'4d8/3f/2'
    
    def __init__(self, udev_device):
        self.udev_device = udev_device
        self.sockets = []
        for socket_num in range(1,4):
            self.sockets.append(PowerUSBSocket(self, socket_num))

    @property
    def device(self):
        return self.udev_device
    
    def open(self):
        print("opening file %s" % self.udev_device.device_links)
        self.fd = open(self.udev_device.device_node, 'rw+')
        return self.fd

    def close(self):
        print self.fd
        self.fd.close()
        self.fd = None

    def read(self):
        instr = self.fd.read()
        return instr

    def write(self, outstr):
        self.fd.write(outstr + chr(0xff) * (64 - len(outstr)))

    
    @property
    def manufacturer(self):
        return self.udev_device.attributes['manufacturer']
    
    @property
    def product(self):
        return self.udev_device.attributes['product']

    @staticmethod
    def strips():
        """
        Return the set of connected power strips
        """
        context = pyudev.Context()
        usb_devices = context.list_devices(
            subsystem="usb", PRODUCT=PowerUSBStrip._product
            )
        return [PowerUSBStrip(d) for d in usb_devices if "idVendor" in d.attributes]
        

class PowerUSBSocket(object):

    _on_cmd = ['A', 'C', 'E']
    _off_cmd = ['B', 'D', 'P']
    
    _defon_cmd = ['N', 'G', 'O']
    _defoff_cmd = ['F', 'Q', "H"]
    
    _state_cmd = [chr(0xa1), chr(0xa2), chr(0xac)]
    _defstate_cmd = [chr(0xa3), chr(0xa4), chr(0xad)]

    def __init__(self, strip, socket_num):
        self._strip = strip
        self._socket_num = socket_num

    def on(self):
        self._strip.write(PowerUSBSocket._on_cmd[self._socket_num - 1])

    def off(self):
        self._strip.write(PowerUSBSocket._off_cmd[self._socket_num - 1])

        
###############################################################################
#
# PowerUSB Commands
#
###############################################################################

def strips(strip_class):
    for strip in strip_class.strips():
        pass


###############################################################################
#
# MAIN
#
###############################################################################
if __name__ == "__main__":

    opts = parse_command_line()

    for strip in PowerUSBStrip.strips():
        print strip.device.device_path
        print strip.device.subsystem
        print strip.manufacturer
        strip.open()
        print strip.fd
        #strip.sockets[0].on()
        strip.close()

    print opts
