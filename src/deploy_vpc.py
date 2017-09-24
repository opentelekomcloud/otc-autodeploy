import ipaddr
import time

import src.cfg as cfg
from src.log import LOG
from src.otc_manager import OTC
from src.deploy_base_server import deploy_nat

CONF = cfg.CONF

cli_opts = [
    cfg.StrOpt('vpc-name', help='VPC name.'),
    cfg.IPOpt('vpc-cidr', help='Available Network Segment: 10.0.0.0/8-24, \
              172.16.0.0/12-24, and 192.168.0.0/16-24.'),
]


class Vpc(object):

    def __init__(self, name, cidr):
        self.name = name
        self.cidr = ipaddr.IPNetwork(cidr)
        self.router = None
        self.networks = []
        self.subnets = []


def add_custom_route(vpc, nat_ip):
    if nat_ip is None:
        LOG.error("Not config nexthop!")
        return
    OTC.conn.network.update_router(
        vpc.router, routes=[{'nexthop': nat_ip, 'destination': '0.0.0.0/0'}])


def deploy_win_base_vpc():
    vpc = deploy_vpc()

    public_subnet_cidr, private_subnet_cidr = vpc.cidr.subnet(new_prefix=24)[
                                                              0:2]

    deploy_subnet(vpc, "public", public_subnet_cidr)
    deploy_subnet(vpc, "private", private_subnet_cidr)

    if CONF.nat:
        nat_ip = str(list(public_subnet_cidr.iterhosts())[1])
        deploy_nat(vpc, nat_ip,
                   CONF.key_name, flavor=CONF.nat_flavor)
        add_custom_route(vpc, nat_ip)

    return vpc


def deploy_vpc():
    vpc = Vpc(CONF.vpc_name, CONF.vpc_cidr)

    # create a router
    vpc.router = OTC.conn.network.create_router(
        name=CONF.vpc_name
    )
    return vpc


def deploy_subnet(vpc, name, cidr):
    # create_network
    network = OTC.conn.network.create_network(
        name=vpc.router.id
    )
    vpc.networks.append(network)

    # create a public subnet
    subnet = OTC.conn.network.create_subnet(
        name=name,
        is_dhcp_enabled=True,
        cidr=str(cidr),
        network_id=network.id,
        dns_nameservers=['100.125.4.25', '8.8.8.8']
    )
    vpc.subnets.append(subnet)

    # connect the subnet to the router, make the subnet connect to the internet.
    OTC.conn.network.add_interface_to_router(vpc.router, subnet.id)


def undelpoy_vpc():
    if not OTC.router:
        print "vpc is not exist."
        return

    networks = OTC.cloud.list_networks(
        filters={'name': OTC.router.id}
    )


    servers = OTC.cloud.search_servers(filters={'user_id': OTC.user_id})
    for server in servers:
        volumes = OTC.cloud.get_volumes(server)

        print "delete server %s %s" % (server.name, server.id)
        OTC.cloud.delete_server(server.id)

        while True:
            if not OTC.cloud.get_server(server.id):
                break
            time.sleep(2)

        for volume in volumes:
            print "delete volume %s" % volume.name
            OTC.cloud.delete_volume(volume.id)


    fips = OTC.cloud.search_floating_ips(filters={
        'tenant_id': OTC.project_id,
        'router_id': OTC.router.id
    })
    for fip in fips:
        print "delete floating ip %s" % fip
        OTC.cloud.delete_floating_ip(fip.id)


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
            OTC.cloud.remove_router_interface({'id': port.device_id},
                                              port_id=port.id)
        elif port.device_owner == 'network:dhcp':
            continue
        else:
            OTC.cloud.delete_port(port.id)


    for network in networks:
        subnets = OTC.cloud.search_subnets(filters={"network_id": network.id})
        for subnet in subnets:
            OTC.cloud.delete_subnet(subnet.id)

        print "delete network %s" % network.name
        OTC.cloud.delete_network(network.id)


    print "delete router %s" % OTC.router.name
    OTC.cloud.delete_router(OTC.router.id)

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
