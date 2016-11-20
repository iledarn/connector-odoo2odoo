# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
try:
    import odoorpc
except ImportError:
    pass
from openerp.addons.connector.connector import ConnectorEnvironment


_logger = logging.getLogger(__name__)


class APIConnectorEnvironment(ConnectorEnvironment):
    """ Custom connector environment for wrapping a Odoo api in it.

    NOTE: Storing the Odoo API instance should result in a better performance
    """

    _propagate_kwargs = ['api']

    def __init__(self, backend_record, session, model_name, api=None):
        super(APIConnectorEnvironment, self).__init__(
            backend_record, session, model_name)
        self.api = api


def get_odoo_api(hostname, port, database, protocol, username, password):
    """ Create a OERP instance for further reuse """
    api = odoorpc.ODOO(hostname, 'jsonrpc', port)
    api.login(database, username, password)
    _logger.info('Created a new Odoo API instance')
    return api


def get_environment(session, model_name, backend_id, api=None):
    """ Create a custom environment to work with """
    backend_record = session.env['odooconnector.backend'].browse(backend_id)

    if not api:
        api = get_odoo_api(backend_record.hostname, backend_record.port,
                           backend_record.database, 'xmlrpc',
                           backend_record.username, backend_record.password)

    env = APIConnectorEnvironment(backend_record, session, model_name, api=api)
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'
    if lang_code == session.context.get('lang'):
        return env
    else:
        with env.session.change_context(lang=lang_code):
            return env
