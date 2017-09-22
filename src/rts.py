import os
import json

from otc_conn import OTC


class RTS(object):

    template_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                 os.pardir, './hot_template')

    def __init__(self, name):
        self.name = name

    def create(self, template, para):
        with open(os.path.join(self.template_path, template)) as f:
            tp = f.read()
            json.dumps(para)
            self.stack = OTC.conn.orchestration.create_stack(
                name=self.name,
                parameters=para,
                template=tp,
            )
            OTC.conn.orchestration.wait_for_status(
                self.stack,
                status='CREATE_COMPLETE',
                failures=['CREATE_FAILED'])

    def delete(self):
        OTC.conn.orchestration.delete_stack(self.stack)

    def create_by_rest(self, template, para):
        pass
