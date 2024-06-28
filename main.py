"""
Malcolm Roddy
CECS 323
One to Many update for mongodb
"""



from ConstraintUtilities import select_general, unique_general, prompt_for_date
from Utilities import Utilities
from Order import Order
from OrderItem import OrderItem
from Product import Product
from PriceHistory import PriceHistory
from StatusChange import StatusChange
from CommandLogger import CommandLogger, log
from pymongo import monitoring
from Menu import Menu
from Option import Option
from menu_definitions import menu_main, add_select, list_select, select_select, delete_select, update_select
import CommonUtilities as CU  # Utilities that work for the sample code & the worked HW assignment.
from _datetime import datetime

"""
This protects Order from deletions in OrderItem of any of the objects reference by Order
in its order_items list.  We could not include this in Order itself since that would 
make a cyclic delete_rule between Order and OrderItem.  I've commented this out because
it makes it impossible to remove OrderItem instances.  But you get the idea how it works."""


# OrderItem.register_delete_rule(Order, 'orderItems', mongoengine.DENY)

"""***************METHODS FOR PRODUCT CLASS*****************"""
def add_product():
    """
    Adds a new document to the product collection. Protects user from entering a duplicate product
    with respect to both uniqueness constraints"""
    success: bool = False
    new_product = None
    while not success:
        buy_price = input("Enter the buy price -->")
        product_date = prompt_for_date("Enter the starting date of the product listed")
        new_product = Product(
            input("Enter the product code-->"),
            input("Enter the product name-->"),
            input("Enter the product description-->"),
            int(input("Enter the quantity in stock-->")),
            buy_price,
            input("Enter the msrp-->")
        )
        # check for violated constraints
        violated_constraints = unique_general(new_product)
        if len(violated_constraints) > 0:
            for violated_constraint in violated_constraints:
                print('Your input values violated constraint: ', violated_constraint)
            print('try again')
        else:
            # The first "price history" is the first price being added
            new_product.change_price(
                PriceHistory(
                    buy_price,
                    product_date
                )
            )
            try:
                new_product.save()
                success = True
            except Exception as e:
                print('Errors storing the new order:')
                print(Utilities.print_exception(e))


def update_product():
    """
    Change the price of an existing product. When changed we add to the PriceHistory
        Make sure that the change date and time for the new price is < right now (no changing prices in the future).
        Make sure that the change date and time for the price change is > the latest price change.

    """
    success: bool = False
    # "Declare" the product variable, more for cosmetics than anything else.
    product: Product
    while not success:
        product = select_product()  # Find a product to add new price
        new_price = input('Enter new price-->')
        price_change_date = prompt_for_date('Date and time of the price change: ')
        try:
            product.change_price(PriceHistory(new_price, price_change_date))
            product.save()
            success = True
        except ValueError as VE:
            print('Attempted status change failed because:')
            print(VE)

def delete_product():
    """Deletes a document from product collection. Doesnt allow user to delete a product not in database.
    Doesnt allow user to delete a product that is mentioned in any orders."""
    product = select_product()  # prompt the user for an order to delete
    items = product.orderItems  # retrieve the list of items in this product
    for item in items:
        # delete items before product delete, so mongo doesnt complain
        print(f"Deleting item: {item} from product")
        item.delete()
    # Now that all the items on the order are removed, we can safely remove the order itself.
    product.delete()


def select_product() -> Product:
    return select_general(Product)

"""*****************METHODS FOR ORDERITEMS CLASS******************"""
def add_order_item():
    """
    Add an item to an existing order.
    :return: None
    """
    success: bool = False
    new_order_item: OrderItem
    order: Order
    product: Product
    while not success:
        print("Adding a new order item. Select the order")
        order = select_order()  # Prompt the user for an order to operate on.
        print("Order selected. Select the product")
        product = select_product() # Prompt user to select a product to order
        # Create a new OrderItem instance.
        new_order_item = OrderItem(
                            order,
                            product,
                            int(input('Quantity --> '))
        )
        # Make sure that this adheres to the existing uniqueness constraints.
        # I COULD use print_exception after MongoEngine detects any uniqueness constraint violations, but
        # MongoEngine will only report one uniqueness constraint violation at a time.  I want them all.
        violated_constraints = unique_general(new_order_item)
        if len(violated_constraints) > 0:
            for violated_constraint in violated_constraints:
                print('Your input values violated constraint: ', violated_constraint)
            print('Try again')
        else:
            try:
                # we cannot add the OrderItem to the Order until it's been stored in the database.
                new_order_item.save()
                order.add_item(new_order_item)  # Add this OrderItem to the Order's MongoDB list of items.
                order.save()  # Update the order in the database.
                success = True  # Finally ready to call  it good.
            except Exception as e:
                print('Exception trying to add the new item:')
                print(Utilities.print_exception(e))


def delete_order_item():
    """
    Remove just one item from an existing order.
    :return: None
    """
    order = select_order()  # prompt the user for an order to update
    items = order.orderItems  # retrieve the list of items in this order
    menu_items: [Option] = []  # list of order items to choose from
    # Create an ad hoc menu of all of the items presently on the order.  Use __str__ to make a text version of each item
    for item in items:
        menu_items.append(Option(item.__str__(), item))
    # prompt the user for which one of those order items to remove, and remove it.
    order.remove_item(Menu('Item Menu',
                           'Choose which order item to remove', menu_items).menu_prompt())
    # Update the order to no longer include that order item in its MongoDB list of order items.
    order.save()


def select_order_item() -> OrderItem:
    return select_general(OrderItem)


def display_order():
    """    d.	Display an order.
        i.	Prompt the user for which order they want to display.
        ii.	Print out the information on the order itself.
        iii.	And each of the items within the order."""
    print("Enter the order you wish to display")
    order = select_order()
    print(order.__str__)

"""*****************METHODS FOR ORDER CLASS******************"""
def select_order() -> Order:
    return select_general(Order)


def prompt_for_enum(prompt: str, cls, attribute_name: str):
    return CU.prompt_for_enum(prompt, cls, attribute_name)


def add_order():
    CU.add_order()


def update_order():
    CU.update_order()


def delete_order():
    CU.delete_order()


"""******************MENU METHODS*****************"""
def menu_loop(menu: Menu):
    """Little helper routine to just keep cycling in a menu until the user signals that they
    want to exit.
    :param  menu:   The menu that the user will see."""
    action: str = ''
    while action != menu.last_action():
        action = menu.menu_prompt()
        print('next action: ', action)
        exec(action)


def add():
    menu_loop(add_select)


def list_members():
    menu_loop(list_select)


def select():
    menu_loop(select_select)


def delete():
    menu_loop(delete_select)


def update():
    menu_loop(update_select)


if __name__ == '__main__':
    print('Starting in main.')
    monitoring.register(CommandLogger())
    db = Utilities.startup()
    main_action: str = ''
    while main_action != menu_main.last_action():
        main_action = menu_main.menu_prompt()
        print('next action: ', main_action)
        exec(main_action)
    log.info('All done for now.')
