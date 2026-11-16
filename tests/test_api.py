import os, tempfile, unittest, importlib, sys
from pathlib import Path
class ProcurementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        os.environ['DATABASE_PATH']=str(Path(cls.tmp.name)/'test.db')
        sys.modules.pop('app',None)
        cls.client=importlib.import_module('app').app.test_client()
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_procurement_receipt_only_once(self):
        s=self.client.post('/api/suppliers',json={'name':'Supplies Ltd'}).json['id']
        p=self.client.post('/api/products',json={'sku':'ABC-1','name':'Paper','unit_cost_cents':150}).json['id']
        o=self.client.post('/api/purchase-orders',json={'supplier_id':s,'lines':[{'product_id':p,'quantity':7,'unit_cost_cents':150}]}).json['id']
        self.assertEqual(self.client.post(f'/api/purchase-orders/{o}/receive').status_code,200)
        self.assertEqual(self.client.post(f'/api/purchase-orders/{o}/receive').status_code,409)
        product=self.client.get('/api/products').json[0]
        self.assertEqual(product['stock'],7)
    def test_reject_negative_cost(self):
        self.assertEqual(self.client.post('/api/products',json={'sku':'bad','name':'Bad','unit_cost_cents':-3}).status_code,400)
