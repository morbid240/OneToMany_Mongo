"""
Created on 04/05/2024
These are utilities that are common between the sample code and the worked homework for the MongoDB One to Many
assignment.
"""
from Utilities import Utilities
from ConstraintUtilities import select_general, unique_general, prompt_for_date
from Order import Order
from StatusChange import StatusChange
from Menu import Menu
from Option import Option


def select_order() -> Order:
    return select_general(Order)


def prompt_for_enum(prompt: str, cls, attribute_name: str):
    """
    MongoEngine attributes can be regulated with an enum.  If they are, the definition of
    that attribute will carry the list of choices allowed by the enum (as well as the enum
    class itself) that we can use to prompt the user for one of the valid values.  This
    represents the 'don't let bad data happen in the first place' strategy rather than
    wait for an exception from the database.
    :param prompt:          A text string telling the user what they are being prompted for.
    :param cls:             The class (not just the name) of the MongoEngine class that the
                            enumerated attribute belongs to.
    :param attribute_name:  The NAME of the attribute that you want a value for.
    :return:                The enum class member that the user selected.
    """
    attr = getattr(cls, attribute_name)  # Get the enumerated attribute.
    if type(attr).__name__ == 'EnumField':  # Make sure that it is an enumeration.
        enum_values = []
        for choice in attr.choices:  # Build a menu option for each of the enum instances.
            enum_values.append(Option(choice.value, choice))
        # Build an "on the fly" menu and prompt the user for which option they want.
        return Menu('Enum Menu', prompt, enum_values).menu_prompt()
    else:
        raise ValueError(f'This attribute is not an enum: {attribute_name}')


def add_order():
    """
    Create a new Order instance.
    :return: None
    """
    success: bool = False
    new_order = None
    while not success:
        order_date = prompt_for_date('Date and time of the order: ')
        """This is sort of a hack.  The customer really should come from a Customer class, and the 
        clerk who made the sale, but I'm trying to keep this simple to concentrate on relationships."""
        new_order = Order(input('Customer name --> '),
                          order_date,
                          input('Clerk who made the sale --> '))
        violated_constraints = unique_general(new_order)
        if len(violated_constraints) > 0:
            for violated_constraint in violated_constraints:
                print('Your input values violated constraint: ', violated_constraint)
            print('try again')
        else:
            # The first "stats change" is placing the order itself.
            new_order.change_status(StatusChange(
                prompt_for_enum('Select the status:', StatusChange, 'status'),
                order_date))
            try:
                new_order.save()
                success = True
            except Exception as e:
                print('Errors storing the new order:')
                print(Utilities.print_exception(e))


def update_order():
    """
    Change the status of an existing order by adding another element to the status vector of the order.
    :return: None
    """
    success: bool = False
    # "Declare" the order variable, more for cosmetics than anything else.
    order: Order
    while not success:
        order = select_order()  # Find an order to modify.
        status_change_date = prompt_for_date('Date and time of the status change: ')
        new_status = prompt_for_enum('Select the status:', StatusChange, 'status')
        try:
            order.change_status(StatusChange(new_status, status_change_date))
            order.save()
            success = True
        except ValueError as VE:
            print('Attempted status change failed because:')
            print(VE)


def delete_order():
    """
    Delete an existing order from the database.
    :return: None
    """
    order = select_order()  # prompt the user for an order to delete
    items = order.orderItems  # retrieve the list of items in this order
    for item in items:
        """The reference from OrderItem back up to Order has a reverse_delete_rule of DENY, which 
        is similar to the RESTRICT option on a relational foreign key constraint.  Which means that
        if I try to delete the order and there are still any OrderItems depending on that order,
        MongoEngine (not MongoDB) will throw an exception."""
        item.delete()
    # Now that all the items on the order are removed, we can safely remove the order itself.
    order.delete()
