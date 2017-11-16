
import os
from threading import Thread
from prettytable import PrettyTable
from time import sleep

import src.cfg as cfg
from src.deploy_vpc import deploy_vpc
from src.deploy_base_server import deploy_server
from src.otc_manager import OTC
from src.const import SSH_PATH, SRC_TEMPLATE_PATH, SERVER_STATE_INIT, \
    SERVER_STATE_DEPLOY, SERVER_STATE_INSTALLED
from src.ssh import ssh_connect
from src.utils import get_random_str, gen_password


CONF = cfg.CONF


chef_group_cli_opts = [
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
        self.key_name = None
        self.keypair_path = None
        self.pub_sg = None
        self.private_sg = None

        self.chef_server = None
        self.chef_server_state = SERVER_STATE_INIT
        self.chef_workstation = None
        self.chef_workstation_state = SERVER_STATE_INIT

        self.random = get_random_str()
        self.admin_passwd = gen_password()

    def __check_para(self):
        pass

    def deploy_chef_server(self):
        print("Start deploy chef server ...")
        server_name = "chef-server-" + self.random
        self.chef_server = deploy_server(server_name,
                                    "Community_Ubuntu_16.04_TSI_20170630",
                                    "s1.xlarge", self.keypair.name, None, None,
                                    self.pub_sg.name,
                                    80, self.pub_net.id, eip=True)

        self.chef_server_state = SERVER_STATE_DEPLOY

        ssh_conn, sftp_conn = ssh_connect(
            self.chef_server['fip'].floating_ip_address, 'ubuntu', None,
            identity_file=self.keypair_path)

        cmds = '''#!/bin/bash
sudo apt-get update
sudo wget https://packages.chef.io/files/stable/chef-server/12.17.5/ubuntu/16.04/chef-server-core_12.17.5-1_amd64.deb
sudo dpkg -i chef-server-core_12.17.5-1_amd64.deb
sudo rm chef-server-core_12.17.5-1_amd64.deb
sudo chef-server-ctl install chef-manage
sudo chef-server-ctl reconfigure
sudo chef-manage-ctl reconfigure --accept-license
sudo mkdir /home/ubuntu/chef
sudo mkdir /home/ubuntu/chef/ca_certs
sudo chef-server-ctl user-create admin admin admin admin@{organization}.com '{admin_passwd}' -f /home/ubuntu/chef/ca_certs/admin.pem
sudo chef-server-ctl org-create otc otc_cloud --association_user admin --filename /home/ubuntu/chef/ca_certs/otc.pem
'''.format(organization=CONF.chef.organization,
           admin_passwd=self.admin_passwd)

        sh_file = '/tmp/' + server_name + '.sh'
        with open(sh_file, 'w') as f:
            f.write(cmds)

        dst_sh_file = '/home/ubuntu/' + server_name + '.sh'
        sftp_conn.put(sh_file, dst_sh_file)
        os.remove(sh_file)

        ssh_conn.exec_command('sudo chmod +x ' + dst_sh_file)
        stdin, stdout, stderr = ssh_conn.exec_command(
            'sudo bash ' + dst_sh_file + ' > ' + server_name + '.log')
        while (not stdout.channel.exit_status_ready()
               and not stdout.channel.recv_ready()):
            sleep(1)

        ssh_conn.close()
        sftp_conn.close()

        self.chef_server_state = SERVER_STATE_INSTALLED

        print("Deploy chef server end.")

    def deploy_chef_workstation(self):
        print("Start deploy chef workstation ...")
        server_name = "chef-workstation-" + self.random
        self.chef_workstation = deploy_server(server_name,
                                    "Community_Ubuntu_16.04_TSI_20170630",
                                    "c2.xlarge", self.keypair.name, None, None,
                                    self.pub_sg.name,
                                    80, self.pub_net.id, eip=True)

        self.chef_workstation_state = SERVER_STATE_DEPLOY

        ssh_conn, sftp_conn = ssh_connect(
            self.chef_workstation['fip'].floating_ip_address, 'ubuntu',
            None, identity_file=self.keypair_path)

        sftp_conn.put(self.keypair_path, '/home/ubuntu/' + self.key_name)
        sftp_conn.put(os.path.join(SRC_TEMPLATE_PATH, 'knife.rb'),
                      '/home/ubuntu/knife.rb')
        sftp_conn.put(os.path.join(SRC_TEMPLATE_PATH, 'Berksfile'),
                      '/home/ubuntu/Berksfile')


        # wait for chef-server
        for i in range(1200):
            if self.chef_server_state < SERVER_STATE_INSTALLED:
                sleep(2)
                continue
            else:
                break

        cmds = '''#!/bin/bash
sudo apt-get update
sudo apt-get install -y gcc make g++ git
sudo wget https://packages.chef.io/files/stable/chefdk/2.3.4/ubuntu/16.04/chefdk_2.3.4-1_amd64.deb
sudo dpkg -i chefdk_2.3.4-1_amd64.deb
sudo echo 'eval "$(chef shell-init bash)"' >> ~/.bash_profile
eval "$(chef shell-init bash)"
sudo git clone git://github.com/chef/chef-repo.git
echo ".chef" | sudo tee -a ~/chef-repo/.gitignore
sudo mkdir ~/chef-repo/.chef
sudo mv /home/ubuntu/{key_pair} ~/chef-repo/.chef/
sudo chmod 400 ~/chef-repo/.chef/{key_pair}
sudo scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i ~/chef-repo/.chef/{key_pair} ubuntu@{server_ip}:/home/ubuntu/chef/ca_certs/admin.pem ~/chef-repo/.chef/admin.pem
sudo sed -i 's/chef_server_name/{server_name}/g' ~/knife.rb
sudo mv /home/ubuntu/knife.rb ~/chef-repo/.chef/knife.rb
sudo mv /home/ubuntu/Berksfile ~/chef-repo/Berksfile
sudo mkdir ~/chef-repo/.chef/ca_certs
echo '{server_ip} {server_name}' | sudo tee -a /etc/hosts
cd ~/chef-repo/.chef/ca_certs
sudo knife ssl fetch
'''.format(key_pair=self.key_name,
           server_ip=self.chef_server['fip'].floating_ip_address,
           server_name=self.chef_server['server'].name)

        sh_file = '/tmp/' + server_name + '.sh'
        with open(sh_file, 'w') as f:
            f.write(cmds)

        dst_sh_file = '/home/ubuntu/' + server_name + '.sh'
        sftp_conn.put(sh_file, dst_sh_file)
        os.remove(sh_file)

        ssh_conn.exec_command('sudo chmod +x ' + dst_sh_file)
        stdin, stdout, stderr = ssh_conn.exec_command(
            'sudo bash ' + dst_sh_file + ' > ' + server_name + '.log')
        while (not stdout.channel.exit_status_ready()
               and not stdout.channel.recv_ready()):
            sleep(1)

        ssh_conn.close()
        sftp_conn.close()

        self.chef_workstation_state = SERVER_STATE_INSTALLED

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

        # create key-pair
        self.key_name = org + '-chef-' + self.random
        keypair = OTC.op_conn.compute.find_keypair(self.key_name)
        if not keypair:
            keypair = OTC.op_conn.compute.create_keypair(name=self.key_name)

        self.keypair = keypair
        self.keypair_path = os.path.join(SSH_PATH, self.key_name)
        with open(self.keypair_path, 'w') as f:
            f.write("%s" % keypair.private_key)
        os.chmod(self.keypair_path, 0o400)

        # create security-groups
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

def deploy():
    chef = ChefBase()
    chef.deploy_chef_net()

    t1 = Thread(target=chef.deploy_chef_server)
    t2 = Thread(target=chef.deploy_chef_workstation)
    t1.start()
    t2.start()

    t1.join()
    t2.join()

    chef_server = chef.chef_server
    chef_workstation = chef.chef_workstation

    print '\r\n' * 2
    t = PrettyTable(['Property', 'Value'])
    t.align = 'l'
    t.add_row(['vpc-name', chef.vpc.name])
    t.add_row(['vpc-cidr', str(chef.vpc.cidr)])
    t.add_row(['chef-server-name', chef_server['server'].name])
    t.add_row(['chef-server-eip', chef_server['fip'].floating_ip_address])
    t.add_row(['chef-admin-user', 'admin'])
    t.add_row(['chef-admin-passwd', chef.admin_passwd])
    t.add_row(['chef-workstation-name', chef_workstation['server'].name])
    t.add_row(['chef-workstation-eip', chef_workstation['fip'].floating_ip_address])
    t.add_row(['key-pair', chef.key_name])
    t.add_row(['key-pair-path', chef.keypair_path])
    print(t)

#    chef.deploy_chef_server()
#    chef.deploy_chef_workstation()
