import os
from threading import Thread

import src.cfg as cfg
from src.deploy_vpc import deploy_vpc
from src.deploy_base_server import deploy_server
from src.otc_manager import OTC
from src.const import SSH_PATH
from src.ssh import OTCSSH
from src.utils import get_random_str


CONF = cfg.CONF


chef_group_cli_opts = [
    cfg.StrOpt('admin-passwd', help="Chef admin user password."),
    cfg.StrOpt('organization', help="Organization name."),
    cfg.StrOpt('cookbook', help="Chef Cookbook."),
]


class ChefBase(object):

    def __init__(self):
        self.vpc = None
        self.pub_net = None
        self.pub_subnet = None
        self.private_net = None
        self.private_subnet = None
        self.keypair = None
        self.keypair_path = None
        self.pub_sg = None
        self.private_sg = None

        self.chef_server = None
        self.chef_workstation = None

        self.random = get_random_str()

    def __check_para(self):
        pass

    def __init_chef_server(self, ip, user, passwd, ifile):
        ssh_conn = OTCSSH(ip, user, passwd, identity_file=ifile)
        ssh_conn.execute(['ls'])


    def deploy_chef_server(self):
        print("Start deploy chef server ...")
        server, fip = deploy_server("chef-server-" + self.random,
                                    "Community_Ubuntu_16.04_TSI_20170630",
                                    "s1.xlarge", self.keypair.name, None, None,
                                    self.pub_sg.name,
                                    80, self.pub_net.id, eip=True)
        self.chef_server = server
        ssh_conn = OTCSSH(fip.floating_ip_address, 'ubuntu', None,
                          identity_file=self.keypair_path)
        ssh_conn.execute(['ls'])
        print("Deploy chef server end.")

    def deploy_chef_workstation(self):
        print("Start deploy chef workstation ...")
 #       server, fip = deploy_server("chef-workstation-" + self.random,
 #                                   "Community_Ubuntu_16.04_TSI_20170630",
 #                                   "c1.xlarge", self.keypair.name, None, None,
 #                                   self.pub_sg.name,
 #                                   80, self.pub_net.id, eip=True)
        print("Deploy chef workstation end.")

    def deploy_chef_net(self):
        self.__check_para()

        org = CONF.chef.organization

        print("Start deploy chef network ...")
        self.vpc = deploy_vpc()

        public_subnet_cidr, private_subnet_cidr \
            = self.vpc.cidr.subnet(new_prefix=24)[0:2]

        self.pub_net, self.pub_subnet \
            = self.vpc.add_subnet("public", public_subnet_cidr)
        self.private_net, self.private_subnet \
            = self.vpc.add_subnet("private", private_subnet_cidr)

        key_name = org + '-chef-' + self.random
        keypair = OTC.op_conn.compute.find_keypair(key_name)
        if not keypair:
            keypair = OTC.op_conn.compute.create_keypair(name=key_name)

        #keypair = OTC.cloud.get_keypair(key_name)
        #if keypair is None:
        #    keypair = OTC.cloud.create_keypair(key_name)
        self.keypair = keypair
        self.keypair_path = os.path.join(SSH_PATH, key_name)
        with open(self.keypair_path, 'w') as f:
            f.write("%s" % keypair.private_key)
        os.chmod(self.keypair_path, 0o400)

        pub_sg_name = 'sg-'+ org + '-public'
        private_sg_name = 'sg-'+ org + '-private'
        self.pub_sg = self.vpc.add_sg(pub_sg_name)
        self.private_sg = self.vpc.add_sg(private_sg_name)

        self.vpc.add_sg_rule(self.pub_sg.id, port_range_min=22,
                             port_range_max=22, protocol='tcp')
        self.vpc.add_sg_rule(self.pub_sg.id, port_range_min=80,
                             port_range_max=80, protocol='tcp')
        self.vpc.add_sg_rule(self.pub_sg.id, port_range_min=443,
                             port_range_max=443, protocol='tcp')
        self.vpc.add_sg_rule(self.pub_sg.id, remote_group_id=self.private_sg.id)
        self.vpc.add_sg_rule(self.private_sg.id, remote_group_id=self.pub_sg.id)
        print("Deploy chef network end.")

def deploy_chef_base():
    chef = ChefBase()
    chef.deploy_chef_net()

#    t1 = Thread(target=chef.deploy_chef_server)
#    t2 = Thread(target=chef.deploy_chef_workstation)
#    t1.start()
#    t2.start()
    chef.deploy_chef_server()
    chef.deploy_chef_workstation()
