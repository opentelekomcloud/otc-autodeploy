import os
import base64
from src.otc_manager import OTC
import src.cfg as cfg
import subprocess
import pprint
from src.const import CONF_PATH
from src.utils import get_random_str


CONF = cfg.CONF


def deploy_server(name, image_name, flavor_name, key_name, userdata,
                  userdata_file, sg_name,
                  disk_size, network_id, az='eu-de-01', eip=False):
    name = name
    print ">>> deploy server %s" % name,

    image = OTC.images.get(image_name)
    flavor = OTC.flavors.get(flavor_name)

    volume = OTC.cloud.create_volume(size=disk_size, name=name, image=image['id'],
                                     volume_type='SATA', availability_zone=az,
                                     wait=True)

    p = subprocess.Popen(["nova", "boot", "--boot-volume", volume.id,
                          "--flavor", flavor['id'],
                          "--availability-zone", az,
                          "--security-group", sg_name, '--key-name', key_name,
                          "--nic", "net-id=%s" % (network_id), name],
                         env=os.environ.copy(),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         shell=True)
    (stdout, stderr) = p.communicate()

    server = OTC.cloud.get_server(name)
    if not server:
        print "create server fail"
        raise Exception

    server = OTC.cloud.wait_for_server(server, auto_ip=False, reuse=False)

    if eip:
        ports = OTC.cloud.list_ports(filters={'device_id': server.id})
        external_network = OTC.cloud.search_networks('admin_external_net')
        fip = OTC.op_conn.network.create_ip(floating_network_id=external_network[0].id,
                                            port_id=ports[0].id,
                                            bandwidth_size=10)
    print "OK >>>"
    return server, fip


def deploy_nat(vpc, network_id, nat_ip):
    # create nat server
    name = vpc.name + '-NAT-server'
    userdata = '''#!/usr/bin/env bash
    sudo apt-get update
    sudo iptables -t nat -A POSTROUTING -o eth0 -s %s -j SNAT --to %s
    sudo iptables-save > /etc/iptables.rules
    sudo touch /etc/network/if-pre-up.d/iptables
    sudo chmod +x /etc/network/if-pre-up.d/iptables
    sudo bash -c "cat>>/etc/network/if-pre-up.d/iptables"<<END_TEXT
    #!/bin/bash
    iptables -F
    iptables-restore /etc/iptables.rules
    END_TEXT
    ''' % (vpc.cidr, str(nat_ip))
    userdata_b64str = base64.b64encode(userdata)

    image_name = "Community_Ubuntu_16.04_TSI_20170630"
    flavor_name = CONF.nat_flavor if CONF.nat_flavor else "s1.medium"
    sg_name = "default"

    return deploy_server(name, image_name, flavor_name, CONF.key_name,
                         userdata_b64str, 'linux_nat.userdata',
                         sg_name, 40, network_id, eip=True)


def deploy_addc(vpc, network_id):
    # create adds
    name = vpc.name + '-ADDC'
    userdata = '''
    #ps1_sysnative
    $ErrorActionPreference = 'Stop'
    Install-WindowsFeature -Name %s -IncludeManagementTools
    $user = [ADSI]'WinNT://./Administrator'
    # Disable user
    #$user.userflags = 2
    #$user.SetInfo()
    $user.SetPassword(%s)
    Import-Module ADDSDeployment
    $safeModePwd = (ConvertTo-SecureString %s -AsPlainText -Force)
    Install-ADDSForest -DomainName %s -DomainNetbiosName %s -SafeModeAdministratorPassword %s -InstallDns -NoRebootOnCompletion -Force
    exit 1001
    ''' % (name, CONF.winapp.domain_admin_passwd, CONF.winapp.domain_admin_passwd,
           CONF.winapp.domain_name, CONF.winapp.domain_netbios_name, CONF.winapp.domain_admin_passwd)
    userdata_b64str = base64.b64encode(userdata)

    image_name="Enterprise_Windows_STD_2012R2_20170809-0"
    flavor_name="s1.large"
    sg_name="default"
    return deploy_server(name, image_name, flavor_name, CONF.key_name,
                         userdata_b64str, 'addc.userdata', sg_name, 60, network_id)


def deploy_rdgw(vpc, key_name, domain_name,
                image_name="Enterprise_Windows_STD_2012R2_20170809-0",
                flavor_name="s1.large", sg_name="default"):
    # create adds
    name = 'RDGW'
    userdata = '''
    '''
    userdata_b64str = base64.b64encode(userdata)
    if True: return

    return deploy_server(name, image_name, flavor_name, key_name,
                         userdata_b64str, sg_name, 60, eip=True)
