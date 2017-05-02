# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.addons.connector.connector import ConnectorEnvironment


class APIConnectorEnvironment(ConnectorEnvironment):
    """ Custom connector environment for wrapping a Odoo api in it.

    NOTE: Storing the Odoo API instance should result in a better performance
    """

    _propagate_kwargs = ['api']

    def __init__(self, backend_record, model_name, api=None):
        super(APIConnectorEnvironment, self).__init__(
            backend_record, model_name)
        self.api = api
