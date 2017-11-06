import ipaddr
import time
import pprint

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


def deploy_vpc():
    print '>>> deploy vpc ' + CONF.vpc_name,
    vpc = Vpc(CONF.vpc_name, CONF.vpc_cidr)

    router = OTC.cloud.get_router(CONF.vpc_name)
    if router:
        raise DeployException("ERROR: VPC %s already exist!" % CONF.vpc_name)

    # create a router
    router = OTC.cloud.create_router(
        name=CONF.vpc_name
    )
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

    for port in ports:
        if port.device_owner == 'network:router_interface_distributed':
            print "remove router interface %s" % port.id
            OTC.cloud.remove_router_interface({'id': port.device_id},
                                              port_id=port.id)
        elif port.device_owner == 'network:dhcp':
            continue
        elif port.device_owner[0:8] == 'compute:':
            servers = OTC.cloud.search_servers(filters={'user_id': OTC.user_id})
            for server in servers:
                fips = OTC.cloud.search_floating_ips(filters={
                    'port_id': port.id
                })
                if fips:
                    fip = fips[0]
                    print "delete floating ip %s" % fip
                    OTC.cloud.detach_ip_from_server(server.id, fip.id)
                    OTC.cloud.delete_floating_ip(fip.id)

                server_networks = server['addresses'].keys()
                if not (set(network_names) & set(server_networks)):
                    print "can not delete server %s %s" % (server.name, server.id)
                    continue

                print "delete server %s %s" % (server.name, server.id)
                OTC.cloud.delete_server(server.id)

                while True:
                    if not OTC.cloud.get_server(server.id):
                        break
                    time.sleep(2)

                volumes = OTC.cloud.get_volumes(server)
                for volume in volumes:
                    print "delete volume %s" % volume.name
                    OTC.cloud.delete_volume(volume.id)
        else:
            print "delete port %s" % port.id
            OTC.cloud.delete_port(port.id)


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

#
#    router = OTC.conn.network.find_router(CONF.vpc_name)
#    if not router:
#        return
#
#    servers = set()
#    networks = OTC.conn.network.networks(name=router.id)
#    for network in networks:
#        print "network id:", network.id
#        ports = OTC.conn.network.ports(network_id=network.id)
#        for port in ports:
#            fips = OTC.conn.network.ips(port_id=port.id)
#            for fip in fips:
#                OTC.conn.network.delete_ip(fip)
#                print "delete fip:", fip
#
#        ports = OTC.conn.network.ports(network_id=network.id)
#        for port in ports:
#            if port.device_id == router.id:
#                #OTC.conn.network.remove_interface_from_router(router,
#                #                                              port_id=port.id)
#                print "remove router interface:", port
#            if port.device_owner[0:8] == "compute:" \
#                    and port.device_id != "":
#                servers.add(port.device_id)
#
#            #OTC.conn.network.delete_port(port)
#
#    for sid in servers:
#        server = OTC.conn.compute.find_server(sid, ignore_missing=True)
#        if server is None:
#            continue
#        #OTC.conn.compute.stop_server(server)
#        OTC.conn.compute.wait_for_server(server,"SHUTOFF")
#
#        vas = OTC.conn.compute.volume_attachments(server)
#        for va in vas:
#            OTC.conn.compute.delete_volume_attachment(va,
#                                                      server,
#                                                      ignore_missing=True)
#
#            OTC.conn.block_store.delete_volume(va.volume_id,
#                                               ignore_missing=True)
#            print "delete volume:", va
#
#        OTC.conn.compute.delete_server(sid, ignore_missing=True)
#        print "delete server:", server
#        while True:
#            s = OTC.conn.compute.find_server(sid, ignore_missing=True)
#            if not s:
#                break
#            time.sleep(3)
#
#    networks = OTC.conn.network.networks(name=router.id)
#    for network in networks:
#        ports = OTC.conn.network.ports(network_id=network.id)
#        for port in ports:
#            OTC.conn.network.delete_port(port)
#            print "delete port:", port
#
#        subnets = OTC.conn.network.subnets(network_id=network.id)
#        for s in subnets:
#            OTC.conn.network.delete_subnet(s)
#            print "delete subnet:", s
#
#        OTC.conn.network.delete_network(network)
#        print "delete network:", network
#
#    OTC.conn.network.delete_router(router)
#    print "delete router:", router
