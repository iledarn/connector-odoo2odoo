# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, fields
from openerp.addons.connector.unit.mapper import mapping

from ..unit.import_synchronizer import (OdooImporter, DirectBatchImporter,
                                        TranslationImporter)
from ..unit.mapper import (OdooImportMapper, OdooImportMapChild)
from ..unit.backend_adapter import OdooAdapter
from ..backend import oc_odoo


_logger = logging.getLogger(__name__)


class OdooConnectorProductTemplate(models.Model):
    _name = 'odooconnector.product.product'
    _inherit = 'odooconnector.binding'
    _inherits = {'product.product': 'openerp_id'}
    _description = 'Odoo Connector Product'

    openerp_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='restrict'
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.product.product',
        inverse_name='openerp_id',
        string='Odoo Connector Bindings'
    )


@oc_odoo
class ProductBatchImporter(DirectBatchImporter):
    _model_name = ['odooconnector.product.product']


@oc_odoo
class ProductTranslationImporter(TranslationImporter):
    _model_name = ['odooconnector.product.product']


@oc_odoo
class ProductImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.product']
    _map_child_class = OdooImportMapChild

    direct = [('name', 'name'), ('name_template', 'name_template'),
              ('type', 'type'),
              ('purchase_ok', 'purchase_ok'), ('sale_ok', 'sale_ok'),
              ('lst_price', 'lst_price'), ('standard_price', 'standard_price'),
              ('ean13', 'ean13'), ('default_code', 'default_code'),
              ('description', 'description')]

    children = [
        ('seller_ids', 'seller_ids', 'odooconnector.product.supplierinfo'),
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        child_records = source[from_attr]

        detail_records = []
        _logger.debug('Loop over product children ...')
        for child_record in child_records:
            adapter = self.unit_for(OdooAdapter, model_name)

            detail_record = adapter.read(child_record)[0]
            detail_records.append(detail_record)

        mapper = self._get_map_child_unit(model_name)

        items = mapper.get_items(
            detail_records, map_record, to_attr, options=self.options
        )

        _logger.debug('Product child "%s": %s', model_name, items)

        return items

    @mapping
    def uom_id(self, record):

        if not record.get('uom_id'):
            return

        uom = self.env['product.uom'].search(
            [('name', '=', record['uom_id'][1])],
            limit=1
        )

        if uom:
            return {'uom_id': uom.id}

    @mapping
    def uom_po_id(self, record):

        if not record.get('uom_id'):
            return

        uom = self.env['product.uom'].search(
            [('name', '=', record['uom_po_id'][1])],
            limit=1
        )

        if uom:
            return {'uom_po_id': uom.id}


@oc_odoo
class ProductSimpleImportMapper(OdooImportMapper):
    _model_name = ['odooconnector.product.product']

    direct = [('name', 'name'), ('name_template', 'name_template'),
              ('description', 'description')]


@oc_odoo
class ProductImporter(OdooImporter):
    _model_name = ['odooconnector.product.product']

    # We have to set a explicit mapper since there are two different
    # mappers that might match
    _base_mapper = ProductImportMapper

    def _after_import(self, binding):
        _logger.debug('Product Importer: _after_import called')
        translation_importer = self.unit_for(TranslationImporter)
        translation_importer.run(
            self.external_id,
            binding.id,
            mapper_class=ProductSimpleImportMapper
        )

    def _is_uptodate(self, binding):
        res = super(ProductImporter, self)._is_uptodate(binding)

        if res:
            _logger.debug('Check also the last product.template write date...')
            product_tmpl_id = self.external_record['product_tmpl_id'][0]
            product_tmpl = self.backend_adapter.read(
                product_tmpl_id, model_name='product.template')
            if product_tmpl:
                date_from_string = fields.Datetime.from_string
                sync_date = date_from_string(binding.sync_date)
                external_date = date_from_string(product_tmpl[0]['write_date'])

                return external_date < sync_date

        return res


@oc_odoo
class ProductImportChildMapper(OdooImportMapChild):
    _model_name = ['odooconnector.product.supplierinfo']
