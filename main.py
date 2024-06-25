from ConstraintUtilities import select_general, unique_general, prompt_for_date
from Utilities import Utilities
from Order import Order
from OrderItem import OrderItem
from StatusChange import StatusChange
from CommandLogger import CommandLogger, log
from pymongo import monitoring
from Menu import Menu
from Option import Option
from menu_definitions import menu_main, add_select, list_select, select_select, delete_select, update_select
import CommonUtilities as CU  # Utilities that work for the sample code & the worked HW assignment.

"""
This protects Order from deletions in OrderItem of any of the objects reference by Order
in its order_items list.  We could not include this in Order itself since that would 
make a cyclic delete_rule between Order and OrderItem.  I've commented this out because
it makes it impossible to remove OrderItem instances.  But you get the idea how it works."""


# OrderItem.register_delete_rule(Order, 'orderItems', mongoengine.DENY)

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


def select_order() -> Order:
    return select_general(Order)


def select_order_item() -> OrderItem:
    return select_general(OrderItem)


def prompt_for_enum(prompt: str, cls, attribute_name: str):
    return CU.prompt_for_enum(prompt, cls, attribute_name)


def add_order():
    CU.add_order()


def add_order_item():
    """
    Add an item to an existing order.
    :return: None
    """
    success: bool = False
    new_order_item: OrderItem
    order: Order
    while not success:
        order = select_order()  # Prompt the user for an order to operate on.
        # Create a new OrderItem instance.
        new_order_item = OrderItem(order,
                                   input('Product Name --> '),
                                   int(input('Quantity --> ')))
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


def update_order():
    CU.update_order()


def delete_order():
    CU.delete_order()


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
