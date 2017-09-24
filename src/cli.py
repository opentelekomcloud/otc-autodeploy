import src.cfg as cfg
from src.deploy_vpc import cli_opts as vpc_cli_opts
from src.deploy_win_base_network import cli_opts as win_base_cli_opts

CONF = cfg.CONF

cli_opts = [
    cfg.StrOpt('project-name', required=True, help="Project name."),
    cfg.StrOpt('project-id', required=True, help="Project ID."),
    cfg.StrOpt('user', required=True, help="Cloud user."),
    cfg.StrOpt('password', required=True, help="User password"),
    cfg.StrOpt('user-domain', required=True, help="User domain name."),
    cfg.StrOpt('key-name', help='Key name.')
]

CONF.register_cli_opts(cli_opts)
CONF.register_cli_opts(vpc_cli_opts)

win_group = cfg.OptGroup(name="winapp", title="Windows application")
win_cli_opts = [
    cfg.BoolOpt("ha", default=False, help="HA mode"),
    cfg.StrOpt("nat", choices=['linux', 'win', 'null'],
               default='null', help="Deploy SNAT server."),
    # cfg.StrOpt("nat-image", help="Image name"),
    cfg.StrOpt("nat-flavor", help="Flavor name"),
    cfg.StrOpt("elb", choices=['external', 'internal', 'null'],
               default='null', help="Specify how to configure the Elastic Load Balancer.")
]

CONF.register_cli_opt(cfg.BoolOpt("deploy_win_base_network",
                      help="Deploy windows application base network."))
CONF.register_group(win_group)
CONF.register_cli_opts(win_cli_opts, group=win_group)
CONF.register_cli_opts(win_base_cli_opts, group=win_group)
