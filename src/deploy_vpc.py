import ipaddr
import time
import pprint
import subprocess
import os

import src.cfg as cfg
from src.log import LOG
from src.otc_manager import OTC
from src.deploy_base_server import deploy_nat
from src.excepts import DeployException


CONF = cfg.CONF

cli_opts = [
    cfg.StrOpt('vpc-name', help='VPC name.'),
    cfg.StrOpt('vpc-cidr', help='Available Network Segment: 10.0.0.0/8-24, \
              172.16.0.0/12-24, and 192.168.0.0/16-24.'),
    cfg.StrOpt('vpc-enable-snat', metavar='{yes|no}', default='yes',
               help='Enable SNAT on VPC.'),
]


class Vpc(object):

    def __init__(self, name, cidr):
        self.name = name
        self.cidr = ipaddr.IPNetwork(cidr)
        self.router = None
        self.networks = []
        self.subnets = []


    def add_custom_route(self, nat_ip):
        if nat_ip is None:
            LOG.error("Not config nexthop!")
            return
        OTC.op_conn.network.update_router(
            self.router, routes=[{'nexthop': nat_ip,
                                  'destination': '0.0.0.0/0'}])

    def add_subnet(self, name, cidr):
        print '>>> deploy subnet ' + name + '(' + str(cidr) + ')',
        # create_network
        network = OTC.cloud.create_network(
            name=self.router.id
        )
        self.networks.append(network)

        # create a public subnet
        subnet = OTC.cloud.create_subnet(
            network.id,
            cidr=str(cidr),
            subnet_name=name,
            enable_dhcp=True,
            dns_nameservers=['100.125.4.25', '8.8.8.8']
        )
        self.subnets.append(subnet)

        # connect the subnet to the router, make the subnet connect to the internet.
        OTC.cloud.add_router_interface(self.router, subnet.id)
        print 'OK >>>'
        return network, subnet

    def add_sg(self, name, desc=''):
        sg = OTC.cloud.get_security_group(name)
        if sg is None:
            sg = OTC.cloud.create_security_group(name, desc)
        return sg

    def add_sg_rule(self, sg_id, port_range_min=None, port_range_max=None,
                    protocol=None, remote_ip_prefix=None, remote_group_id=None,
                    direction='ingress', ethertype='IPv4'):
        try:
            rule = OTC.cloud.create_security_group_rule(
                sg_id,
                port_range_min=port_range_min,
                port_range_max=port_range_max,
                protocol=protocol,
                remote_ip_prefix=remote_ip_prefix,
                remote_group_id=remote_group_id,
                direction=direction,
                ethertype=ethertype)
        except Exception as e:
            if -1 == e.message.find('rule already exists'):
                print e.message

        return

def deploy_vpc():
    print '>>> deploy vpc ' + CONF.vpc_name,

    vpc = Vpc(CONF.vpc_name, CONF.vpc_cidr)

    router = OTC.cloud.get_router(CONF.vpc_name)
    if router:
        raise DeployException("ERROR: VPC %s already exist!" % CONF.vpc_name)

    # create a router
    router = OTC.cloud.create_router(
        name=CONF.vpc_name,
    )

    if CONF.vpc_enable_snat == 'yes':
        print 'ENABLE_SNAT'
        cmd = ["neutron", "router-gateway-set", "--enable-snat", CONF.vpc_name,
            router.external_gateway_info['network_id']]
        p = subprocess.Popen(' '.join(cmd),
                            env=os.environ.copy(),
                            shell=True)
        p.wait()

    vpc.router = router

    print 'OK >>>'
    return vpc



def undeploy_vpc():
    print '>>> undeploy vpc ' + CONF.vpc_name
    if not OTC.router:
        print "vpc is not exist."
        return

    networks = OTC.cloud.list_networks(
        filters={'name': OTC.router.id}
    )
    network_names = [n['name'] for n in networks]

    ports = []
    for network in networks:
        nw_ports = OTC.cloud.list_ports(
            filters={'tenant_id': OTC.project_id,
                     'network_id': network.id}
        )
        if nw_ports:
            ports = ports + nw_ports

    router_interfaces = []
    servers = []
    for port in ports:
        if port.device_owner == 'network:router_interface_distributed':
            router_interfaces.append(port.id)
        elif port.device_owner == 'network:dhcp':
            continue
        elif port.device_owner[0:8] == 'compute:':
            server = OTC.cloud.get_server(port.device_id)
            server_networks = server['addresses'].keys()
            if not (set(network_names) & set(server_networks)):
                continue
            servers.append(server)

            fips = OTC.cloud.search_floating_ips(filters={
                'port_id': port.id
            })
            for fip in fips:
                print "delete floating ip %s" % fip.floating_ip_address
                OTC.cloud.detach_ip_from_server(server.id, fip.id)
                OTC.cloud.delete_floating_ip(fip.id)
        else:
            print "delete port %s" % port.id
            OTC.cloud.delete_port(port.id)

    keys = []
    for s in servers:
        print("delete server %s %s" % (s.name, s.id))

        if s.key_name:
            keys.append(s.key_name)

        OTC.cloud.delete_server(s.id)
        volumes = OTC.cloud.get_volumes(s)

        while True:
            if not OTC.cloud.get_server(s.id):
                break
            time.sleep(2)

        for volume in volumes:
            print "delete volume %s" % volume.name
            OTC.cloud.delete_volume(volume.id)

    all_used_keys = [s.key_name for s in OTC.cloud.list_servers()]
    for key in (set(keys).difference(set(all_used_keys))):
        print("delete keypair %s" % key)
        OTC.cloud.delete_keypair(key)

    for router_interface in router_interfaces:
        print "remove router interface %s" % router_interface
        OTC.cloud.remove_router_interface(OTC.router,
                                          port_id=router_interface)

    for network in networks:
        subnets = OTC.cloud.search_subnets(filters={"network_id": network.id})
        for subnet in subnets:
            print "delete subnet %s" % subnet.name
            OTC.cloud.delete_subnet(subnet.id)

        print "delete network %s" % network.name
        OTC.cloud.delete_network(network.id)


    print "delete router %s" % OTC.router.name
    OTC.cloud.delete_router(OTC.router.id)
    print 'OK >>>'
