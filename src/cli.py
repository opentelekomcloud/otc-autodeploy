import src.cfg as cfg
from src.deploy_vpc import cli_opts as vpc_cli_opts
from src.deploy_win_app_exchange import winapp_exchange_group_cli_opts
from src.deploy_chef_base import chef_group_cli_opts
from src.show import show_cli_opts

CONF = cfg.CONF

cli_opts = [
    cfg.StrOpt('project-name', required=True, help="Project name."),
    cfg.StrOpt('project-id', required=True, help="Project ID."),
    cfg.StrOpt('user', required=True, help="Cloud user."),
    cfg.StrOpt('password', required=True, help="User password"),
    cfg.StrOpt('user-domain', required=True, help="User domain name."),
    cfg.StrOpt('key-name', help='Key name.'),
    cfg.StrOpt('deploy',
               metavar='{winapp-exchange|winapp-sp|chef-base|chef-apache|daimler-demo}',
               choices=['winapp-exchange', 'winapp-sp',
                        'chef-base', 'chef-apache', 'daimler-demo'],
               help='Deploy.'),
    cfg.StrOpt('undeploy', metavar='{vpc}', help='Undeploy vpc.'),
    cfg.StrOpt("ha", metavar='{yes|no}', default='no', help="HA mode"),
    cfg.StrOpt("nat", metavar='{yes|no}', default='no', help="Deploy NAT server."),
    cfg.StrOpt("nat-type", metavar='[linux|win]', choices=['linux', 'win'],
               default='linux', help="NAT server type."),
    # cfg.StrOpt("nat-image", help="Image name"),
    cfg.StrOpt("nat-flavor", help="NAT Flavor name"),
    cfg.StrOpt("elb", metavar='[external|internal|null]',choices=['external', 'internal', 'null'],
               default='null', help="Specify how to configure the Elastic Load Balancer.")
]

CONF.register_cli_opts(cli_opts)
CONF.register_cli_opts(vpc_cli_opts)
CONF.register_cli_opts(show_cli_opts)

winapp_group = cfg.OptGroup(name="winapp", title="Windows application")
winapp_base_cli_opts = [
]

CONF.register_group(winapp_group)
CONF.register_cli_opts(winapp_base_cli_opts, group=winapp_group)
CONF.register_cli_opts(winapp_exchange_group_cli_opts, group=winapp_group)

chef_group = cfg.OptGroup(name="chef")
CONF.register_cli_opts(chef_group_cli_opts, group=chef_group)
