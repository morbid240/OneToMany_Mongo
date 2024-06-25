import mongoengine
from mongoengine import *
from Order import Order


class OrderItem(Document):
    """An individual product that is part of an order.  This could easily be done
    using a one to few, in which case it would be just an element in an array
    within the Order class, but I wanted to use this as a demonstration of how to
    do the same thing using a bidirectional relationship."""
    # The  parent order that this is a member of.
    order = ReferenceField(Order, required=True, reverse_delete_rule=mongoengine.DENY)
    # This will be replaced by a reference to an instance of the Product class.
    product = StringField(max_length=80, min_length=4, required=True)
    # There is no hard and fast maximum value for quantity.
    quantity = IntField(required=True, min_value=1)

    # Be sure to conform to the naming conventions for the collection versus the class.
    meta = {'collection': 'order_items',
            'indexes': [
                {'unique': True, 'fields': ['order', 'product'], 'name': 'order_items_pk'}
            ]}

    def __init__(self, order: Order, product: str, quantity: int, *args, **values):
        """
        Create a new instance of OrderItem.
        :param order:       The order that this item belongs to.
        :param product:     The product being ordered.
        :param quantity:    The number >= 1 of that product.
        :param args:        Other arguments as needed.
        :param values:      Other values as needed.
        """
        super().__init__(*args, **values)
        self.order = order
        self.product = product
        self.quantity = quantity


    def __str__(self):
        return f'OrderItem: Product: {self.product}, Qty: {str(self.quantity)}'

    def get_product(self):
        """
        Return the identity of the product that this order item refers to.
        :return:    The identity of the ordered product.
        """
        return self.product

    def equals(self, other) -> bool:
        """
        Check if this product is the same product as the other OrderItem instance.
        :param other: The OrderItem that we are comparing to.
        :return: True if they are for the same product, false otherwise.
        ToDo
            When Product becomes an object reference, this will need to be modified.
        """
        return self.get_product() == other.get_product()
