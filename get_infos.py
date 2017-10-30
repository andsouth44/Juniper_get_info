'''
Set of Juniper utilities to find and check certain configuration variables.

'''
from jnpr.junos import Device
from itertools import count, ifilterfalse

def get_int_units(hostname, userid, pwd, intf):
    '''
    Function to return a sorted list of interface "units" configured on an interface on
    a Juniper device.

    get_int_units('routername', 'jsmith', 'abcd1234', 'ge-0/2/5') ->

    [4, 101, 102, 103, 104, 105, 106, 107, 108, 500, 1871,
     2001, 2002, 3182, 3432, 32767]

    '''
    dev = Device(host=hostname, user=userid, password=pwd, port='22')
    dev.open()

    interface = dev.rpc.get_interface_information(interface_name=intf)

    dev.close()

    all_units = []

    for item in interface.iter('logical-interface'):
        units = item.find('name').text
        all_units.append(int((units.split('.')[1]).strip()))

    return sorted(all_units)

def get_int_vlans(hostname, userid, pwd, intf):
    '''
    Function to return a sorted list of outer vlans configured on an interface on a Juniper device.

    get_int_vlans('routername', 'jsmith', 'abcd1234', 'ge-0/2/5') ->

    [0, 4, 101, 102, 103, 104, 105, 106, 107, 108, 500, 1871, 2001, 2002, 3182, 3432]
    '''
    dev = Device(host=hostname, user=userid, password=pwd, port='22')
    dev.open()

    facts = dev.facts

    if facts['ifd_style'] == 'CLASSIC':

        interface = dev.rpc.get_interface_information(interface_name=intf)

        dev.close()

        all_vlans = []

        for item in interface.iter('logical-interface'):
            vlandata = item.find('link-address').text
            vlandata = vlandata.split('.')[1]
            vlandata = vlandata.split(']')[0]
            all_vlans.append(int(vlandata.split(' ')[0].strip()))

        return sorted(all_vlans)

    elif facts['ifd_style'] == 'SWITCH':

        interface = dev.rpc.get_ethernet_switching_interface_information(interface_name=intf)

        dev.close()

        all_vlans = []

        for item in interface.iter('interface-vlan-member-list'):
            for item in interface.iter('interface-vlan-member'):
                all_vlans.append(int(item.find('interface-vlan-member-tagid').text))

        return sorted(all_vlans)

    else:
        raise TypeError('Unsupported device type')

def get_rts(hostname, userid, pwd):
    '''
    Function to return a sorted list of VPN RT values configured on
    a Juniper device. If a configured route-instance has no configured
    RT the function passes over that instance to avoid errors. The "target:64512:..."
    part of the RT value will be stripped off.

    get_rts('routername', 'jsmith', 'abcd1234') ->

    [27, 38, 54, 55, 58, 59, 60, 61, 63, 64]

    '''
    dev = Device(host=hostname, user=userid, password=pwd, port='22')
    dev.open()

    config = dev.rpc.get_config()

    dev.close()

    targets = []

    for item in config[-2]:
        try:
            rts = item.find('vrf-target/community').text
            targets.append(int(rts.split(':')[2]))
        except:
            pass

    return sorted(targets)

def get_rds(hostname, userid, pwd):
    '''
    Function to return a sorted list of VPN RD values configured on
    a Juniper device. If a configured route-instance has no configured
    RD the function passes over that instance to avoid errors. The "10.92.x.x:..."
    part of the RD value will be stripped off.

    get_rds('routername', 'jsmith', 'abcd1234') ->

    [27, 38, 54, 55, 58, 59, 60, 61, 63, 64]

    '''
    dev = Device(host=hostname, user=userid, password=pwd, port='22')
    dev.open()

    config = dev.rpc.get_config()

    dev.close()

    distinguishers = []

    for item in config[-2]:
        try:
            rds = item.find('route-distinguisher/rd-type').text
            distinguishers.append(int(rds.split(':')[1]))
        except:
            pass

    return sorted(distinguishers)

def is_unit_int(hostname, userid, pwd, intf, unit):
    '''
    Function to determine if a unit is already being used on an interface on
    a Juniper device.

    is_unit_int('routername', 'jsmith', 'abcd1234', 'ge-0/2/5', '250') ->

    False

    '''

    units = get_int_units(hostname, userid, pwd, intf)

    return int(unit) in units

def is_vlan_int(hostname, userid, pwd, intf, vlan):
    '''
    Function to determine if an outer VLAN is already being used on an interface on
    a Juniper device.

    is_vlan_int('routername', 'jsmith', 'abcd1234', 'ge-0/2/5', '250') ->

    False

    '''

    vlans = get_int_vlans(hostname, userid, pwd, intf)

    return int(vlan) in vlans

def is_rt(hostname, userid, pwd, rt):
    '''
    Function to determine if an VPN RT is already configured on a Juniper device.

    is_rt('routername', 'jsmith', '250') ->

    False

    '''

    rts = get_rts(hostname, userid, pwd)

    return int(rt) in rts

def is_rd(hostname, userid, pwd, rd):
    '''
    Function to determine if an VPN RD is already configured on a Juniper device.

    is_rd('routername', 'jsmith', '250') ->

    False

    '''

    rds = get_rds(hostname, userid, pwd)

    return int(rd) in rds

def next_unit_int(hostname, userid, pwd, intf, start):
    '''
    Function to determine the next free unit (after start) on an interface on
    a Juniper device.

    next_unit_int('routername', 'jsmith', 'abcd1234', 'ge-0/2/5', 2001) ->

    2003

    '''

    units = get_int_units(hostname, userid, pwd, intf)

    return next(ifilterfalse(units.__contains__, count(start)))

def find_unit_for_vlan(hostname, userid, pwd, intf, vlan):
    '''
    Function to determine the unit associated with a specified vlan on an
    interface on a Juniper MX device.

    find_unit_for_vlan('routername', 'jsmith', 'abcd1234', 'ge-0/2/5', 2001) ->

    2003

    '''
    dev = Device(host=hostname, user=userid, password=pwd, port='22')
    dev.open()

    interface = dev.rpc.get_interface_information(interface_name=intf)

    dev.close()

    for item in interface.iter('logical-interface'):
        if item.find('link-address').text.split('.')[1].split(']')[0].split(' ')[0].strip() == vlan:
            return item.find('name').text.split('.')[1].strip()

def next_unit_int_lo(hostname, userid, pwd, intf, start):
    '''
    Function used to determine the next free unit (after supplied start value)
    on an interface on a Juniper device plus the loopback 0.0 IP address of the device. Function
    retrieves both values in single connection.

    next_unit_int_lo('routername', 'jsmith', 'abcd1234', 'ge-0/2/5', 2001) ->

    (2003, '10.1.1.1')

    '''
    dev = Device(host=hostname, user=userid, password=pwd, port='22')
    dev.open()

    interface = dev.rpc.get_interface_information(interface_name=intf)

    loopback = dev.rpc.get_interface_information(interface_name='lo0.0', terse=True, normalize=True)

    dev.close()

    all_units = []

    for item in interface.iter('logical-interface'):
        units = item.find('name').text
        all_units.append(int((units.split('.')[1]).strip()))

    next_unit = next(ifilterfalse(all_units.__contains__, count(start)))

    loopbackip = loopback.xpath(".//address-family[address-family-name='inet']/ \
    interface-address/ifa-local")[0].text

    return (next_unit, loopbackip)

def find_unit_for_vlan_lo(hostname, userid, pwd, intf, vlan):
    '''
    Function used to determine the unit being used for a vlan
    on an interface on a Juniper device plus the loopback 0.0 IP address of the device. Function retrieves both values in single connection.

    find_unit_for_vlan_lo('routername', 'jsmith', 'abcd1234', 'ge-0/2/5', 2001) ->

    (2003, '10.1.1.1')

    '''
    dev = Device(host=hostname, user=userid, password=pwd, port='22')
    dev.open()

    interface = dev.rpc.get_interface_information(interface_name=intf)

    loopback = dev.rpc.get_interface_information(interface_name='lo0.0', terse=True, normalize=True)

    loopbackip = loopback.xpath(".//address-family[address-family-name='inet']/ \
    interface-address/ifa-local")[0].text

    dev.close()

    for item in interface.iter('logical-interface'):
        if item.find('link-address').text.split('.')[1].split(']')[0].split(' ')[0].strip() == vlan:
            unit = item.find('name').text.split('.')[1].strip()

    return(unit, loopbackip)

