# -*- coding: utf-8 -*-
# vim: ts=4 
###
#
# Copyright (c) 2010 J. Félix Ontañón
#
# Almost based on arista.inputs module:
# Copyright 2008 - 2010 Daniel G. Taylor <dan@programmer-art.org>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors : J. Félix Ontañón <fontanon@emergya.es>
# 

import gobject
import gudev

class Device(object):
    """A simple object representing a device."""
    
    def __init__(self, device):
        """Create a new input device
            
        @type device: gudev.Device
        @param device: The device we are using
        """
        self.device = device

    @property
    def nice_label(self):
        return self.device.get_sysfs_attr('name')

    def get_props(self):
        print "subsystem", self.device.get_subsystem()
        print "devtype", self.device.get_devtype()
        print "name", self.device.get_name()
        print "number", self.device.get_number()
        print "sysfs_path:", self.device.get_sysfs_path()
        print "driver:", self.device.get_driver()
        print "action:", self.device.get_action()
        print "seqnum:", self.device.get_seqnum()
        print "device type:", self.device.get_device_type()
        print "device number:", self.device.get_device_number()
        print "device file:", self.device.get_device_file()
        print "device file symlinks:", ", ".join(self.device.get_device_file_symlinks())
        print "device keys:", ", ".join(self.device.get_property_keys())
        for device_key in self.device.get_property_keys():
            print "   device property %s: %s"  % (device_key, self.device.get_property(device_key))
    
    @property
    def path(self):
        """Get the sysfs_path for this device
            
        @rtype: string
        @return: The sysfs path
        """
        return self.device.get_sysfs_path()

    def __repr__(self):
        return self.device.get_name() or '??'
        
class DeviceFinder(gobject.GObject):
    """
    An object that will find and monitor Wiimote devices on your 
    machine and emit signals when are connected / disconnected
    """
    
    __gsignals__ = {
        'connected': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
            (gobject.TYPE_PYOBJECT,)),
        'disconnected': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
            (gobject.TYPE_PYOBJECT,)),
    }
    
    def __init__(self, subsystems=['usb']):
        """
        Create a new DeviceFinder and attach to the udev system to 
        listen for events.
        """
        self.__gobject_init__()

        self.client = gudev.Client(subsystems)
        self.subsystems = subsystems
        self.devices = {}

        def explore_parent(device, devices_list):
            path = device.get_sysfs_path()        
            parent = device.get_parent()
            
            if parent:
                explore_parent(parent, devices_list)
                devices_list[path] = (Device(device), Device(parent))
            else:
                devices_list[path] = (Device(device), None)

        for subsystem in subsystems:
            for device in self.client.query_by_subsystem(subsystem):
                explore_parent(device, self.devices)
                                
        self.client.connect('uevent', self.event)

    def event(self, client, action, device):
        """Handle a udev event"""
        
        return {
            "add": self.device_added,
#            "change": self.device_changed,
#            "remove": self.device_removed,
        }.get(action, lambda x,y: None)(device, device.get_subsystem())

    def device_added(self, device, subsystem):
        """Called when a device has been added to the system"""
        
        print device, subsystem
        
        path = device.get_sysfs_path()
        self.devices[path] = Device(device)
        self.emit('connected', device)

gobject.type_register(DeviceFinder)

if __name__ == "__main__":
    import gobject
    
    def found(finder, device):
        print device.path + ": " + device.nice_label
    
    def lost(finder, device):
        print device.path + ": " + device.nice_label
    
    finder = DeviceFinder(['usb'])
    finder.connect('connected', found)
    finder.connect('disconnected', lost)
    
    import pprint
    pprint.pprint(finder.devices)
    
    loop = gobject.MainLoop()
    loop.run()
