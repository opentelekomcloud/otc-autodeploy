import os
import base64
from src.otc_manager import OTC
import src.cfg as cfg
import subprocess
import pprint

CONF = cfg.CONF


def deploy_server(name, image_name, flavor_name, key_name, userdata, sg_name,
                  disk_size, network_id, az='eu-de-01', eip=False):
    print ">>> deploy server %s" % name,

#    image = OTC.cloud.get_image(image_name)
#    flavor = OTC.cloud.get_flavor(flavor_name)

#    server_args = {
#        'name': name,
#        'image': image,
#        'flavor': flavor,
#        'key_name': key_name,
#        'userdata': userdata,
#        'security_groups': [{'name': sg_name}],
#        'network': network,
#    }
#
#    server = OTC.cloud.create_server(wait=True, **server_args)

#    p = subprocess.Popen(["nova", "--debug", "boot", "--flavor", flavor['id'],
#                          "--image", image['id'], "--availability-zone", az,
#                          "--security-group", sg_name, '--key-name', key_name,
#                          "--user-data", "./conf/linux_nat.userdata"
#                          "--nic", "net-id=%s" % (network_id), name],
#                         env=os.environ.copy(),
#                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
#                         shell=True)
#    (stdout, stderr) = p.communicate()
#
#    server_id = None
#    output = stdout.splitlines()
#    for line in output:
#        v = [n.strip() for n in line.split('|') if n]
#        if v[0].lower() == 'id':
#            server_id = v[1]
#            break
#    if not server_id:
#        print "create server fail"
#        raise Exception
#
#    server = OTC.cloud.get_server(server_id)
#
#    if eip:
#        external_network = OTC.cloud.search_networks('admin_external_net')
#        OTC.cloud.create_floating_ip(network=external_network[0].id,
#                                     wait=True)
#        print OTC.cloud.add_auto_ip(server)

    # volume = OTC.cloud.create_volume(name=name,
    #                                  size=disk_size,
    #                                  wait=True,
    #                                  timeout=120)
    # OTC.cloud.attach_volume(server, volume, wait=True, timeout=120)
    print "OK >>>"
    return


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
                         userdata_b64str, sg_name, 40, network_id, eip=True)


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
                         userdata_b64str, sg_name, 60, network_id)


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
