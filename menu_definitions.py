"""
Malcolm Roddy
CECS 323
One to Many update for mongodb


added menu options for displaying order, add and delete functions for
product
"""
from Menu import Menu
import logging
from Option import Option

menu_logging = Menu('debug', 'Please select the logging level from the following:', [
    Option("Debugging", "logging.DEBUG"),
    Option("Informational", "logging.INFO"),
    Option("Error", "logging.ERROR")
])

menu_main = Menu('main', 'Please select one of the following options:', [
    Option("Add new instance", "add()"),
    Option("Delete existing instance", "delete()"),
    Option("List existing instances", "list_members()"),
    Option("Select existing instance", "select()"),
    Option("Update existing instance", "update()"),
    Option("Display an Order instance", "display_order()"),
    Option("Exit", "pass")
])

# options for adding a new instance
add_select = Menu('add select', 'Which type of object do you want to add?:', [
    Option("Orders", "add_order()"),
    Option("Products", "add_product()"),
    Option("Order Items", "add_order_item()"),
    Option("Exit", "pass")
])

# options for deleting an existing instance
delete_select = Menu('delete select', 'Which type of object do you want to delete?:', [
    Option("Orders", "delete_order()"),
    Option("Order Items", "delete_order_item()"),
    Option("Products", "delete_product()"),
    Option("Exit", "pass")
])

# options for listing the existing instances
list_select = Menu('list select', 'Which type of object do you want to list?:', [
    Option("Orders", "list_order()"),
    Option("Order Items", "list_order_item()"),
    Option("Products", "list_product()"),
    Option("Exit", "pass")
])

# options for testing the select functions
select_select = Menu('select select', 'Which type of object do you want to select:', [
    Option("Order", "print(select_order())"),
    Option("Order Item", "print(select_order_item())"),
    Option("Product", "print(select_product())"),
    Option("Exit", "pass")
])

# options for testing the update functions
update_select = Menu("update select", 'Which type of object do you want to update:', [
    Option("Order", "update_order()"),
    Option("Order Items", "update_order_item()"),
    Option("Products", "update_product()"),
    Option("Exit", "pass")
])
