######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import Category, db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1, **overrides) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory(**overrides)
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)
        response.close()

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        self.assertTrue(location.endswith(f"{BASE_URL}/{new_product['id']}"))
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), new_product)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------
    def test_read_product(self):
        """It should Read a Product by ID"""
        product = self._create_products()[0]
        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(Decimal(data["price"]), product.price)
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["category"], product.category.name)

    def test_read_product_not_found(self):
        """It should return 404 when a Product does not exist"""
        response = self.client.get(f"{BASE_URL}/999999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("message", response.get_json())

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_product(self):
        """It should Update a Product and return the updated data"""
        product = self._create_products()[0]
        updated = {
            "name": "Updated product",
            "description": "An updated product description",
            "price": "123.45",
            "available": False,
            "category": Category.TOOLS.name,
        }
        response = self.client.put(f"{BASE_URL}/{product.id}", json=updated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["id"], product.id)
        self.assertEqual(response.get_json()["name"], updated["name"])
        self.assertEqual(response.get_json()["description"], updated["description"])
        self.assertEqual(Decimal(response.get_json()["price"]), Decimal(updated["price"]))
        self.assertFalse(response.get_json()["available"])
        self.assertEqual(response.get_json()["category"], updated["category"])

        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["name"], updated["name"])

    def test_update_product_errors(self):
        """It should reject invalid updates and missing products"""
        product = self._create_products()[0]
        response = self.client.put(f"{BASE_URL}/{product.id}", json={"name": "Missing fields"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.put(f"{BASE_URL}/999999", json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.put(
            f"{BASE_URL}/{product.id}", data="{}", content_type="text/plain"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_product(self):
        """It should Delete a Product"""
        product = self._create_products()[0]
        response = self.client.delete(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")
        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product_not_found(self):
        """It should return 404 when deleting a missing Product"""
        response = self.client.delete(f"{BASE_URL}/999999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------
    # TEST LIST AND FILTER
    # ----------------------------------------------------------
    def test_list_all_products(self):
        """It should List all Products"""
        expected = self._create_products(count=3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {product["id"] for product in response.get_json()},
            {product.id for product in expected},
        )

    def test_list_products_by_name(self):
        """It should filter Products by name"""
        product = self._create_products(name="Named product")[0]
        self._create_products(name="Other product")
        response = self.client.get(BASE_URL, query_string={"name": product.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual([item["id"] for item in data], [product.id])
        self.assertEqual(data[0]["name"], product.name)

    def test_list_products_by_category(self):
        """It should filter Products by category"""
        product = self._create_products(category=Category.FOOD)[0]
        self._create_products(category=Category.TOOLS)
        response = self.client.get(BASE_URL, query_string={"category": product.category.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual([item["id"] for item in data], [product.id])
        self.assertEqual(data[0]["category"], Category.FOOD.name)

    def test_list_products_by_availability(self):
        """It should filter Products by true and false availability"""
        available_product = self._create_products(available=True)[0]
        unavailable_product = self._create_products(available=False)[0]
        for value, expected in (
            ("true", available_product),
            ("false", unavailable_product),
        ):
            response = self.client.get(BASE_URL, query_string={"available": value})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                [item["id"] for item in response.get_json()], [expected.id]
            )

    def test_list_products_by_combined_filters(self):
        """It should apply name, description, category, and availability filters together"""
        product = self._create_products(
            name="Matching product",
            description="Matching description",
            category=Category.FOOD,
            available=True,
        )[0]
        self._create_products(
            name="Matching product",
            description="Other description",
            category=Category.FOOD,
            available=False,
        )
        response = self.client.get(
            BASE_URL,
            query_string={
                "name": product.name,
                "description": product.description,
                "category": Category.FOOD.name,
                "available": "true",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.get_json()], [product.id])

    def test_list_products_rejects_invalid_filters(self):
        """It should reject invalid category, availability, and empty-name filters"""
        for filters in (
            {"category": "not-a-category"},
            {"available": "sometimes"},
            {"name": "  "},
            {"description": "  "},
        ):
            response = self.client.get(BASE_URL, query_string=filters)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
