import ipaddr

import src.cfg as cfg
from src.rts import RTS
from src.deploy_vpc import deploy_win_base_vpc, undelpoy_vpc
from src.deploy_base_server import deploy_adds, deploy_rdgw

CONF = cfg.CONF


cli_opts = [
    cfg.StrOpt('domain-name', help="Domain DNS name."),
    cfg.StrOpt('domain-netbios-name', help="Domain NetBIOS ID."),
    cfg.StrOpt('restore-passwd', help="Password for a separate Administrator \
                                       account when the domain controller is \
                                       in Restore Mode. Must be at least 8 \
                                       characters containing letters, \
                                       numbers and symbols."),
    cfg.StrOpt('domain-admin-user', help="User name for the account that\
                                          will be added as Domain Administrator.\
                                          This is separate from the default \
                                          'Administrator' account."),
    cfg.StrOpt('domain-admin-passwd', help="Password for the domain admin user."),
    cfg.StrOpt("adds-flavor", help="Flavor name"),
    cfg.StrOpt("rdgw-flavor", help="Flavor name")
]


def __check_para():
    pass


def deploy():
    __check_para()
    vpc = deploy_win_base_vpc()
    deploy_adds(vpc, CONF.key_name, CONF.domain_name, CONF.domain_netbios_name,
                CONF.restore_passwd, CONF.domain_admin_user,
                CONF.domain_admin_passwd, flavor=CONF.adds_flavor)
    deploy_rdgw(vpc, CONF.key_name, CONF.domain_name, flavor=CONF.rdgw_flavor)


def undeploy():
    undelpoy_vpc()


def rts_deploy(template_name):
    v_cidr = ipaddr.IPNetwork(CONF.vpc_cidr)
    public_subnet_cidr, private_subnet_cidr \
        = v_cidr.subnet(new_prefix=24)[0:2]

    nat_private_ip = str(list(public_subnet_cidr.iterhosts())[1])

    para = {
        'vpc_name': CONF.vpc_name,
        'vpc_cidr': CONF.vpc_cidr,
        'public_subnet_cidr': str(public_subnet_cidr),
        'private_subnet_cidr': str(private_subnet_cidr),
        'nat_private_ip': nat_private_ip,
        'custom_route': "{routes: [{nexthop: " + nat_private_ip
                        + ", destination: '0.0.0.0/0'}]}",
        'key_name': CONF.key_name
    }

    stack = RTS("win_base_network")

    stack.create(template_name, para)
