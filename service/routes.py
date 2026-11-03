######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
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

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
from flask import abort, jsonify, request, url_for
from service.models import Category, DataValidationError, Product
from service.common import status  # HTTP Status Codes
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if request.mimetype != content_type:
        app.logger.error("Invalid or missing Content-Type: %s", request.content_type)
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Content-Type must be {content_type}")


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    try:
        product.deserialize(data)
    except DataValidationError as error:
        abort(status.HTTP_400_BAD_REQUEST, description=str(error))
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    location_url = url_for("get_product", product_id=product.id, _external=True)
    return jsonify(product.serialize()), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S
######################################################################

@app.route("/products", methods=["GET"])
def list_products():
    """Returns products, optionally filtered by name, category, or availability."""
    query = None

    name = request.args.get("name")
    if name is not None:
        if not name.strip():
            abort(status.HTTP_400_BAD_REQUEST, description="Product name cannot be empty")
        query = Product.find_by_name(name)

    description = request.args.get("description")
    if description is not None:
        if not description.strip():
            abort(status.HTTP_400_BAD_REQUEST, description="Product description cannot be empty")
        if query is None:
            query = Product.query
        query = query.filter(Product.description == description)

    category_name = request.args.get("category")
    if category_name is not None:
        try:
            category = Category[category_name.upper()]
        except (AttributeError, KeyError):
            abort(status.HTTP_400_BAD_REQUEST, description="Invalid product category")
        if query is None:
            query = Product.find_by_category(category)
        else:
            query = query.filter(Product.category == category)

    available_value = request.args.get("available")
    if available_value is not None:
        normalized_value = available_value.lower()
        if normalized_value not in ("true", "false"):
            abort(status.HTTP_400_BAD_REQUEST, description="Availability must be true or false")
        available = normalized_value == "true"
        if query is None:
            query = Product.find_by_availability(available)
        else:
            query = query.filter(Product.available == available)

    products = query.all() if query is not None else Product.all()
    return jsonify([product.serialize() for product in products]), status.HTTP_200_OK


######################################################################
# R E A D   A   P R O D U C T
######################################################################

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Reads a product by ID."""
    product = Product.find(product_id)
    if product is None:
        abort(status.HTTP_404_NOT_FOUND, description=f"Product with id '{product_id}' was not found")
    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# U P D A T E   A   P R O D U C T
######################################################################

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """Updates a product by ID."""
    check_content_type("application/json")
    product = Product.find(product_id)
    if product is None:
        abort(status.HTTP_404_NOT_FOUND, description=f"Product with id '{product_id}' was not found")

    try:
        product.deserialize(request.get_json())
    except DataValidationError as error:
        abort(status.HTTP_400_BAD_REQUEST, description=str(error))
    product.update()
    return jsonify(product.serialize()), status.HTTP_200_OK

######################################################################
# D E L E T E   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Deletes a product by ID."""
    product = Product.find(product_id)
    if product is None:
        abort(status.HTTP_404_NOT_FOUND, description=f"Product with id '{product_id}' was not found")
    product.delete()
    return "", status.HTTP_204_NO_CONTENT
