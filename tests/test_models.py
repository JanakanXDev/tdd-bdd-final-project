# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        found_product = Product.find(product.id)
        self.assertIsNotNone(found_product)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)
        self.assertIsNone(Product.find(product.id + 100))

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        original_id = product.id
        product.name = "Updated product"
        product.description = "An updated product description"
        product.price = Decimal("123.45")
        product.available = not product.available
        product.category = Category.TOOLS
        product.update()
        self.assertEqual(product.id, original_id)
        db.session.expire_all()
        updated_product = Product.find(original_id)
        self.assertEqual(updated_product.name, "Updated product")
        self.assertEqual(updated_product.description, "An updated product description")
        self.assertEqual(updated_product.price, Decimal("123.45"))
        self.assertEqual(updated_product.available, product.available)
        self.assertEqual(updated_product.category, Category.TOOLS)

        invalid_product = ProductFactory()
        invalid_product.id = None
        with self.assertRaises(DataValidationError):
            invalid_product.update()

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)
        self.assertIsNone(Product.find(product.id))

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        expected = ProductFactory.create_batch(5)
        for product in expected:
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)
        self.assertEqual({product.id for product in products}, {product.id for product in expected})

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        self.assertGreater(count, 0)
        for product in found:
            self.assertEqual(product.name, name)
        self.assertEqual(Product.find_by_name("missing product").count(), 0)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        self.assertGreater(count, 0)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        self.assertGreater(count, 0)
        for product in found:
            self.assertEqual(product.available, available)

    def test_serialize_a_product(self):
        """It should serialize a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        d = product.serialize()
        self.assertEqual(d["id"], product.id)
        self.assertEqual(d["name"], product.name)
        self.assertEqual(d["description"], product.description)
        self.assertEqual(d["price"], str(product.price))
        self.assertEqual(d["available"], product.available)
        self.assertEqual(d["category"], product.category.name)

    def test_deserialize_rejects_invalid_products(self):
        """It should reject incomplete and invalid product data."""
        product = ProductFactory()
        with self.assertRaises(DataValidationError):
            product.deserialize({"name": "Missing fields"})
        with self.assertRaises(DataValidationError):
            product.deserialize(
                {
                    "name": "Invalid product",
                    "description": "Invalid category",
                    "price": "12.50",
                    "available": True,
                    "category": "NOT_A_CATEGORY",
                }
            )
        with self.assertRaises(DataValidationError):
            product.deserialize(
                {
                    "name": "Invalid product",
                    "description": "Invalid availability",
                    "price": "12.50",
                    "available": "yes",
                    "category": Category.FOOD.name,
                }
            )
        with self.assertRaises(DataValidationError):
            product.deserialize(
                {
                    "name": "Invalid product",
                    "description": "Invalid price",
                    "price": "not-a-price",
                    "available": True,
                    "category": Category.FOOD.name,
                }
            )
