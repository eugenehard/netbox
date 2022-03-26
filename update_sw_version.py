import pynetbox
import ipaddress
import getpass
from netmiko import ConnectHandler

var_api_token = getpass.getpass(prompt = "Enter api token for netbox: ")
var_username = str(input("Enter username [evgeniy.tretyak]: ")) or "evgeniy.tretyak"
var_ssh_port = str(input("Enter ssh port[2200]: ")) or "2200"
netbox = pynetbox.api(
    "http://netbox.activeby.net",
    token = var_api_token
)

var_asset_tmpl = {
    "username": var_username,
    "use_keys": "True",
    "port": var_ssh_port
}

var_status = "active"
var_tenant = "noc-in-netbox"

#commands to run on different devices to get software version
var_iosxe_command = "show ver | in Cisco IOS XE Software"
var_ios_command = "show ver | in Cisco IOS Software"
var_nxos_command = "show ver | NXOS: version"
var_asa_command = "show ver | Appliance Software Version"
var_ce_command = "dis cur | in Version"
var_junos_command = 'show configuration | display set | match "set version"'

#get list of devices to update custom_field
def f_devs_list(arg):
    devs = netbox.dcim.devices.filter(model=arg,status=var_status,tenant=var_tenant)
    return devs

def test_f_devs_list():#test if f_devs_list return valid hostnames
    for device in f_devs_list("ios-xe"):
        assert 'activeby.net' in str(device)

#connect via ssh and run command, register software version for different devices
def f_get_sw_version_iosxe(dev,cmd):
    try:
        ssh_connect = ConnectHandler(**dev)
        output = ssh_connect.send_command(cmd)
        output = output.split(" ")
        output = output[-1]
        return output
    except Exception as error:
        print("\n====================",error)

def f_get_sw_version_ios(dev,cmd):
    try:
        ssh_connect = ConnectHandler(**dev)
        output = ssh_connect.send_command(cmd)
        output = output.split(" ")
        output = output[-4]
        return output
    except Exception as error:
        print("\n====================",error)
        
f_get_sw_version_nxos = f_get_sw_version_iosxe#used the same formula
f_get_sw_version_asa = f_get_sw_version_iosxe#used the same formula
f_get_sw_version_ce = f_get_sw_version_iosxe#used the same formula
f_get_sw_version_junos = f_get_sw_version_iosxe#used the same formula

#update custom_field in netbox
def f_job(devices,asset_type,f,cmd):
    for device in devices:
        var_asset = var_asset_tmpl
        var_ip = str(netbox.dcim.devices.get(name=device).primary_ip)
        var_ip = var_ip.split("/")#split prefix and mask
        var_ip = var_ip[0]#use only prefix
        var_old_info = netbox.dcim.devices.get(name=device).custom_fields["sw_version"]#sw_version before update
        var_asset["device_type"] = asset_type
        try:
            ipaddress.ip_address(var_ip)
            var_asset["ip"] = var_ip
            device.custom_fields["sw_version"] = f(var_asset,cmd)#update custom field sw_version
            device.save()
            print(device,"sw_version updated from",var_old_info,"to",device.custom_fields["sw_version"])
        except ValueError as error:
            print("Not valid primary_ip:",var_ip,"for",device)

if __name__ == "__main__":
    #run tasks for specified device type
    try:
        f_job(f_devs_list("ios-xe"),"cisco_ios",f_get_sw_version_iosxe,var_iosxe_command)#cisco ios-xe job
    except:
        print("Something went wrong with ios-xe device")
    try:
        f_job(f_devs_list("ios"),"cisco_ios",f_get_sw_version_ios,var_ios_command)#cisco ios job
    except:
        print("Something went wrong with ios device")
    try:
        f_job(f_devs_list("nxos"),"cisco_nxos",f_get_sw_version_nxos,var_nxos_command)#cisco nxos job
    except:
        print("Something went wrong with nxos device")
    try:
        f_job(f_devs_list("asa"),"cisco_asa",f_get_sw_version_asa,var_asa_command)#cisco nxos job
    except:
        print("Something went wrong with asa device")
    try:
        f_job(f_devs_list("ce"),"huawei",f_get_sw_version_ce,var_ce_command)#huawei ce job
    except:
        print("Something went wrong with huawei device")
    try:
        f_job(f_devs_list("junos"),"juniper_junos",f_get_sw_version_ce,var_junos_command)#juniper job
    except:
        print("Something went wrong with junos device")
