#!/usr/bin/env python

import sys

from src.cli import CONF
from src.otc_manager import OTC
from src.deploy_win_base_network import deploy as deploy_win_base_network
from src.deploy_win_base_network import undeploy as undeploy_win_base_network


if __name__ == "__main__":
    CONF(sys.argv[1:])
    OTC.create_connection()

    if CONF.deploy_win_base_network is True:
        deploy_win_base_network()

    if CONF.deploy_win_base_network is False:
        undeploy_win_base_network()
