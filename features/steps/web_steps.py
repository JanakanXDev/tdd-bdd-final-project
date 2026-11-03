######################################################################
# Copyright 2016, 2021 John J. Rofrano. All Rights Reserved.
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

# pylint: disable=function-redefined, missing-function-docstring
# flake8: noqa
"""
Web Steps

Steps file for web interactions with Selenium

For information on Waiting until elements are present in the HTML see:
    https://selenium-python.readthedocs.io/waits.html
"""
import logging
from behave import when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ID_PREFIX = 'product_'


@when('I visit the "Home Page"')
def step_impl(context):
    """ Make a call to the base URL """
    context.driver.get(context.base_url)
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )

@then('I should see "{message}" in the title')
def step_impl(context, message):
    """ Check the document title for a message """
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda driver: message in driver.title
    )

@then('I should not see "{text_string}"')
def step_impl(context, text_string):
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda driver: text_string not in driver.find_element(By.TAG_NAME, "body").text
    )


@then('I should see "{text_string}"')
def step_impl(context, text_string):
    """Wait until visible page text contains the requested text."""
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda driver: text_string in driver.find_element(By.TAG_NAME, "body").text
    )


@then('I should see the message "{message}"')
def step_impl(context, message):
    """Wait until the UI displays the expected status message."""
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda driver: driver.find_element(By.ID, "flash_message").text.strip() == message
    )

@when('I set the "{element_name}" to "{text_string}"')
def step_impl(context, element_name, text_string):
    element_id = ID_PREFIX + element_name.lower().replace(' ', '_')
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )
    element.clear()
    element.send_keys(text_string)

@when('I select "{text}" in the "{element_name}" dropdown')
def step_impl(context, text, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(' ', '_')
    select = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.element_to_be_clickable((By.ID, element_id))
    )
    element = Select(select)
    element.select_by_visible_text(text)

@then('I should see "{text}" in the "{element_name}" dropdown')
def step_impl(context, text, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(' ', '_')
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda driver: Select(driver.find_element(By.ID, element_id))
        .first_selected_option.text
        == text
    )

@then('the "{element_name}" field should be empty')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(' ', '_')
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda driver: driver.find_element(By.ID, element_id).get_attribute("value") == ""
    )

##################################################################
# These two function simulate copy and paste
##################################################################
@when('I copy the "{element_name}" field')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(' ', '_')
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )
    context.clipboard = element.get_attribute('value')
    logging.info('Clipboard contains: %s', context.clipboard)

@when('I paste the "{element_name}" field')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(' ', '_')
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )
    element.clear()
    element.send_keys(context.clipboard)

##################################################################
# Button IDs use the action name followed by "-btn", such as "clear-btn".
##################################################################

@when('I press the "{button}" button')
def step_impl(context, button):
    """Click one of the catalog's named action buttons."""
    button_id = button.lower().replace(" ", "-") + "-btn"
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.element_to_be_clickable((By.ID, button_id))
    )
    element.click()

##################################################################
# Form field IDs use ID_PREFIX followed by the normalized field name.
##################################################################

@then('I should see "{text_string}" in the "{element_name}" field')
def step_impl(context, text_string, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(' ', '_')
    found = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.text_to_be_present_in_element_value((By.ID, element_id), text_string)
    )
    assert found

@when('I change "{element_name}" to "{text_string}"')
def step_impl(context, element_name, text_string):
    element_id = ID_PREFIX + element_name.lower().replace(' ', '_')
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )
    element.clear()
    element.send_keys(text_string)
