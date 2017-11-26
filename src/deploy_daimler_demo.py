import os

import src.cfg as cfg
from src.otc_manager import OTC
from src.const import HOT_TEMPLATE_PATH


CONF = cfg.CONF


chef_group_cli_opts = [
]


class DaimlerDemo(object):

    def __init__(self):
        self.name = 'Daimler_Demo'

        self.vpc = None
        self.subnet1 = None
        self.subnet1_1 = None
        self.subnet2 = None
        self.subnet3 = None

    def deploy_network(self):
        vpc_name = self.name + '_vpc'
        vpc_template = os.path.join(HOT_TEMPLATE_PATH, 'vpc.yaml')
        vpc_para = {'vpc_name': vpc_name, 'cidr' : "172.31.0.0/16", 'snat' : "true" }
        OTC.cloud.create_stack(vpc_name,
                               template_file=vpc_template,
                               paramaters=vpc_para,
                               wait=True)

        self.router = OTC.cloud.get_router(vpc_name)

        subnet_template = os.path.join(HOT_TEMPLATE_PATH, 'subnet.yaml')
        subnet1_para = {'vpc_id': vpc_name, 'name': 'subnet1', 'cidr' : "172.31.16.0/24"}
        OTC.cloud.create_stack(vpc_name + '_subnet1',
                               template_file=subnet_template,
                               paramaters=subnet1_para)

        subnet1_1_para = {'vpc_id': vpc_name, 'name': 'subnet1-1', 'cidr' : "172.31.48.0/24"}
        OTC.cloud.create_stack(vpc_name + '_subnet1-1',
                               template_file=subnet_template,
                               paramaters=subnet1_1_para)

        subnet2_para = {'vpc_id': vpc_name, 'name': 'subnet2', 'cidr' : "172.31.80.0/24"}
        OTC.cloud.create_stack(vpc_name + '_subnet2',
                               template_file=subnet_template,
                               paramaters=subnet2_para)

        subnet3_para = {'vpc_id': vpc_name, 'name': 'subnet3', 'cidr' : "172.31.112.0/24"}
        OTC.cloud.create_stack(vpc_name + '_subnet3',
                               template_file=subnet_template,
                               paramaters=subnet3_para)

    def deploy_server(self):
        pass

    def deploy_sg(self):
        sg_template = os.path.join(HOT_TEMPLATE_PATH, 'daimler-demo', 'sg.yaml')
        sg1_name = 'Daimler_AZ1_SG1'
        sg1_para = {'name': sg1_name}
        OTC.cloud.create_stack(sg1_name,
                               template_file=sg_template,
                               paramaters=sg1_para)

        sg_template = os.path.join(HOT_TEMPLATE_PATH, 'daimler-demo', 'sg.yaml')
        sg2_name = 'Daimler_AZ1_SG2'
        sg2_para = {'name': sg2_name}
        OTC.cloud.create_stack(sg2_name,
                               template_file=sg_template,
                               paramaters=sg2_para)

    def deploy_fw(self):
        pass

    def deploy_vpc_peering(self):
        pass

    def deploy_elb(self):
        pass

def deploy():
    dd = DaimlerDemo()
    dd.deploy_network()
    dd.deploy_sg()
    dd.deploy_server()
    dd.deploy_elb()
