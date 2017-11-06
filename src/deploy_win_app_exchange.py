import src.cfg as cfg
import base64
from src.deploy_vpc import deploy_vpc
from src.deploy_base_server import deploy_server, deploy_nat, deploy_addc


CONF = cfg.CONF


winapp_exchange_group_cli_opts = [
    cfg.StrOpt('domain-name', help="Domain DNS name."),
    cfg.StrOpt('domain-netbios-name', help="Domain NetBIOS ID."),
    cfg.StrOpt('restore-passwd', default="Password@123", help="Password for a separate Administrator \
                                       account when the domain controller is \
                                       in Restore Mode. Must be at least 8 \
                                       characters containing letters, \
                                       numbers and symbols."),
    cfg.StrOpt('domain-admin-user', default="administrator", help="User name for the account that\
                                          will be added as Domain Administrator.\
                                          This is separate from the default \
                                          'Administrator' account."),
    cfg.StrOpt('domain-admin-passwd', help="Password for the domain admin user."),
    cfg.StrOpt("addc-flavor", default="c2.large", help="ADDC flavor name"),
    cfg.StrOpt("addc-disksize", default="80", help="ADDC disk size(GB)"),
    cfg.StrOpt("server-flavor", default="c2.xlarge", help="Exchange Server flavor name"),
    cfg.StrOpt("server-disksize", default="500", help="Exchange Server disk size(GB)")
]


def __check_para():
    pass


def deploy_exchange_server(vpc, network_id):
    name = vpc.name + '-exchange-server'
    image_name = "Enterprise_Windows_STD_2012R2_ZEN"

    userdata = '''
    "#ps1_sysnative\n",
    "$ErrorActionPreference = 'Stop'\n",
    "Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools\n",
    "$user = [ADSI]'WinNT://./",
    {
        "Ref": %s
    },
    "'\n",
    "# Disable user\n",
    "#$user.userflags = 2\n",
    "#$user.SetInfo()\n",
    "$user.SetPassword('",
    {
        "Ref": %s
    },
    "')\n",
    "Import-Module ADDSDeployment\n",
    "$safeModePwd = (ConvertTo-SecureString '",
    {
        "Ref": %s
    },
    "' -AsPlainText -Force)\n",
    "Install-ADDSForest -DomainName '",
    {
        "Ref": %s
    },
    ".local' -DomainNetbiosName '",
    {
        "Ref": %s
    },
    "' -SafeModeAdministratorPassword $safeModePwd -InstallDns -Force -NoRebootOnCompletion\n",
    "$waitHandleUrl = \"",
    {
        "Ref": "1800"
    },
    "\"\n",
    "$cfnMessage = '{\"Status\" : \"SUCCESS\",\"Reason\" : \"Configuration Complete\",\"UniqueId\" : \"ID1234\",\"Data\" : \"ADDC has completed configuration.\"}'\n",
    "Invoke-RestMethod -Method PUT -Uri $waitHandleUrl -Body $cfnMessage\n",
    "Restart-Computer -Force\n"
    ''' % (CONF.winapp.domain_admin_user, CONF.winapp.domain_admin_passwd,
           CONF.winapp.domain_admin_passwd, CONF.winapp.domain_name,
           CONF.winapp.domain_netbios_name)
    userdata_b64str = base64.b64encode(userdata)

    deploy_server(name, image_name, CONF.winapp.server_flavor, CONF.key_name,
                  userdata_b64str, "default",
                  CONF.winapp.server_disksize, network_id,
                  az='eu-de-01', eip=False)


def deploy_winapp_exchange():
    __check_para()

    print "Start deploy windows exchange ..."
    vpc = deploy_vpc()

    public_subnet_cidr, private_subnet_cidr = vpc.cidr.subnet(new_prefix=24)[
                                                              0:2]

    pub_net, pub_subnet = vpc.add_subnet("public", public_subnet_cidr)
    private_net, private_subnet = vpc.add_subnet("private", private_subnet_cidr)

    if CONF.nat:
        nat_ip = str(list(public_subnet_cidr.iterhosts())[1])

        deploy_nat(vpc, pub_net.id, nat_ip)
        # vpc.add_custom_route(nat_ip)

    deploy_addc(vpc, private_net.id)
    deploy_exchange_server(vpc, private_net.id)
    print "Deploy windows exchange end."
