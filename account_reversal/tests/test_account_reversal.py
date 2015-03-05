# -*- encoding: utf-8 -*-
# #############################################################################
#
# Account partner required module for OpenERP
#    Copyright (C) 2014 Acsone (http://acsone.eu).
#    @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tests import common
from openerp import fields
from datetime import datetime


class test_account_reversal(common.TransactionCase):
    def setUp(self):
        super(test_account_reversal, self).setUp()
        self.move_obj = self.env['account.move']
        self.move_line_obj = self.env['account.move.line']

    def _create_move(self, with_partner, amount=100):
        date = datetime.now()
        company_id = self.env.ref('base.main_company').id
        period_id = self.env['account.period'].with_context(
            account_period_prefer_normal=True,
            company_id=self.env.ref('base.main_company').id).find(date)[0]

        journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'COD',
            'type': 'sale',
            'sequence_id': self.env.ref('account.sequence_sale_journal').id,
            'company_id': company_id})

        move_vals = {
            'journal_id': journal.id,
            'period_id': period_id.id,
            'date': date,
            'company_id': company_id,
        }

        # Why this doesn't work I don't know:
        # acct = self.ref('account.a_sale'
        account1, account2 = self.env['account.account'].search(
            [('company_id', '=', company_id), ('type', '=', 'other')])[:2]

        move_id = self.move_obj.create(move_vals)
        self.move_line_obj.create({
            'move_id': move_id.id,
            'name': '/',
            'debit': 0,
            'credit': amount,
            'company_id': company_id,
            'account_id': account1.id})
        move_line_id = self.move_line_obj.create(
            {
                'move_id': move_id.id,
                'name': '/',
                'debit': amount,
                'credit': 0,
                'account_id': account2.id,
                'company_id': company_id,
                'partner_id': self.ref('base.res_partner_1')
                if with_partner else False
            }
        )
        return move_line_id

    def test_reverse(self):
        move_line = self._create_move(with_partner=False)
        move = move_line.move_id
        company_id = self.env.ref('base.main_company').id
        account1 = self.env['account.account'].search(
            [('company_id', '=', company_id), ('type', '=', 'other')])[0]
        movestr = ''.join(['%.2f%.2f%s' % (x.debit, x.credit,
                                           x.account_id == account1 and 'aaaa' or 'bbbb')
                           for x in move.line_id])
        self.assertEqual(movestr, '100.000.00bbbb0.00100.00aaaa')
        yesterday_date = datetime(year=2015, month=3, day=3)
        yesterday = fields.Date.to_string(yesterday_date)
        reversed_move = move.create_reversals(yesterday)
        movestr_reversed = ''.join(
            ['%.2f%.2f%s' % (x.debit, x.credit,
                             x.account_id == account1 and 'aaaa' or 'bbbb')
             for x in reversed_move.line_id])
        self.assertEqual(movestr_reversed, '0.00100.00bbbb100.000.00aaaa')
