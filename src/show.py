from prettytable import PrettyTable
import humanfriendly

from src.otc_manager import OTC
import src.cfg as cfg

show_cli_opts = [
    cfg.StrOpt("show", metavar='{flavor|image|az|sg}',
               choices=['flavor', 'image', 'az', 'sg'],
               help="show [ flavor | image | az | sg ]"),
]


CONF = cfg.CONF


class Show(object):
    @classmethod
    def show(cls):
        if CONF.show:
            func = getattr(cls, CONF.show)
            if func:
                func()

    @staticmethod
    def flavor():
        fs = OTC.cloud.list_flavors()
        t = PrettyTable(['name', 'vcpu', 'ram', 'disk', 'disabled', 'public'])

        for f in fs:
            t.add_row([f['name'], f['vcpus'],
                       humanfriendly.format_size(f['ram'] * 1024 * 1024, binary=True),
                       humanfriendly.format_size(f['disk'] * 1024 * 1024 * 1024, binary=True),
                       f['is_disabled'],
                       f['is_public']])
        print t

    @staticmethod
    def image():
        imgs = OTC.cloud.list_images()
        t = PrettyTable(['name', 'os_type', 'platform', 'os_version',
                         'image_size', 'min_ram', 'min_disk',
                         'status'], sortby='platform')

        try:
            for img in imgs:
                properties = img['properties']
                img_size = properties.get('__image_size', '')
                min_ram = img.get('min_ram', '')
                min_disk = img.get('min_disk', '')
                t.add_row([img['name'], properties.get('__os_type', ''),
                           properties.get('__platform', ''),
                           properties.get('__os_version', ''),
                           humanfriendly.format_size(float(img_size), binary=True) if img_size else img_size,
                           humanfriendly.format_size(float(min_ram) * 1024 * 1024, binary=True) if min_ram else min_ram,
                           humanfriendly.format_size(float(min_disk) * 1024 * 1024 * 1024, binary=True) if min_disk else min_disk,
                           img.get('status', '')])
        except KeyError:
            print img
        print t

    @staticmethod
    def az():
        azs = OTC.cloud.list_availability_zone_names()
        t = PrettyTable(['availability_zone'])

        for az in azs:
            t.add_row([az])
        print t

    @staticmethod
    def sg():
        sgs = OTC.cloud.list_security_groups()


        for sg in sgs:
            print '+' + '-' * 81 + '+'
            print '  name:        ' + sg['name']
            print '  description: ' + sg['description']

            t = PrettyTable(['direction', 'type', 'protocol', 'port-range', 'remote-end'])
            for rule in sg['security_group_rules']:
                t.add_row([str(rule['direction']), str(rule['ethertype']),
                        str(rule['protocol']),
                        str(rule['port_range_min']) + '-' + str(rule['port_range_max']),
                        str(rule['remote_group_id'])])
            print t
