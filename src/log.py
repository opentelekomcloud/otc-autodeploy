import os
import logging
import logging.config

log_conf_path = os.path.join(os.path.dirname(__file__), 
                             os.pardir, './conf/log.conf')
logging.config.fileConfig(os.path.abspath(log_conf_path),
                          disable_existing_loggers=False)
LOG = logging.getLogger('ms_auto')
