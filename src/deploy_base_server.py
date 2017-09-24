import base64
from src.otc_manager import OTC


def deploy_server(name, image, flavor, key_name, userdata, sg_name, disk_size, eip=False):
    image = OTC.conn.compute.find_image(image)
    flavor = OTC.conn.compute.find_flavor(flavor)

    server_args = {
        'name': name,
        'image': image,
        'flavor': flavor,
        'key_name': key_name,
        'user_data': userdata,
        'security_groups': [{'name': sg_name}]
    }

    server = OTC.conn.compute.create_server(**server_args)
    OTC.conn.compute.wait_for_server(server)

    if eip:
        ports = OTC.conn.network.ports(device_id=server.id)
        external_network = OTC.conn.network.find_network('admin_external_net')
        OTC.conn.network.create_ip(floating_network_id=external_network.id,
                                port_id=ports[0].id)

    volume = OTC.conn.block_store.create_volume(name=name,
                                                size=disk_size)
    OTC.conn.block_store.wait_for_status(volume,
                                         status='available',
                                         failures=['error'],
                                         interval=2,
                                         wait=120)
    OTC.conn.compute.create_volume_attachment(server,
                                              vloume_id=volume.id)
    OTC.conn.block_store.wait_for_status(volume,
                                         status='in-use',
                                         failures=['error'],
                                         interval=2,
                                         wait=120)

    return server


def deploy_nat(vpc, nat_ip, key_name, image="Community_Ubuntu_16.04_TSI_20170630",
               flavor="s1.medium", sg_name="default"):
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

    return deploy_server(name, image, flavor, key_name,
                         userdata_b64str, sg_name, 40, eip=True)


def deploy_adds(vpc, key_name, domain_name, domain_netbios_name,
                restore_passwd, domain_admin_user, domain_admin_passwd,
                image="Enterprise_Windows_STD_2012R2_20170809-0",
                flavor="s1.large", sg_name="default"):
    # create adds
    name = 'ADDS'
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
    ''' % (name, restore_passwd, restore_passwd, domain_name, domain_netbios_name, restore_passwd )
    userdata_b64str = base64.b64encode(userdata)
    if True: return

    return deploy_server(name, image, flavor, key_name,
                         userdata_b64str, sg_name, 60)


def deploy_rdgw(vpc, key_name, domain_name,
                image="Enterprise_Windows_STD_2012R2_20170809-0",
                flavor="s1.large", sg_name="default"):
    # create adds
    name = 'RDGW'
    userdata = '''
    '''
    userdata_b64str = base64.b64encode(userdata)
    if True: return

    return deploy_server(name, image, flavor, key_name,
                         userdata_b64str, sg_name, 60, eip=True)
