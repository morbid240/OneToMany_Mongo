from Status import Status
from mongoengine import *
from datetime import datetime
from StatusChange import StatusChange
# from OrderItemProduct import OrderItem


class Order(Document):
    """An agreement between the enterprise and a single customer to exchange for
    a specified quantity of some number of products for an agreed upon price."""
    customerName = StringField(db_field='customer_name', max_length=80, min_length=5, required=True)
    orderDate = DateTimeField(db_field='order_date', required=True)
    statusHistory = EmbeddedDocumentListField(StatusChange, db_field='status_history')
    soldBy = StringField(db_field='sold_by', max_length=80, required=True)
    # Note that there is no delete rule here.  Without that, we could delete a document out of
    # OrderItem that an instance of Order references, and MongoEngine would not stop you.  But
    # there already is a delete rule from OrderItem to Order, and I cannot have circular delete
    # rules.  The delete rule to protect Order from losing Order Items will be in main.py.
    orderItems = ListField(ReferenceField('OrderItem'))

    meta = {'collection': 'orders',
            'indexes': [
                {'unique': True, 'fields': ['customerName', 'orderDate'], 'name': 'orders_pk'}
            ]}

    def change_status(self, new_status: StatusChange):
        """
        Every time the status changes for the order, we add another instance of StatusChange to
        the history list of status changes.
        :param new_status:  An instance of StatusChange representing the latest status change.
        :return:            None
        """
        if self.statusHistory:
            current_status = self.statusHistory[-1]
            if current_status.status == new_status.status:
                raise ValueError('It is already in this status.')
            if current_status.statusChangeDate >= new_status.statusChangeDate:
                raise ValueError('New status must be later than the latest status change.')
            if new_status.statusChangeDate > datetime.utcnow():
                raise ValueError('The status change cannot occur in the future.')
            self.statusHistory.append(new_status)
        else:
            self.statusHistory = [new_status]   # This is the first status "change".

    def get_current_status(self) -> Status:
        """
        Get the current status of the order.
        :return: The current status of the order.  Note, if there is no status for
        this order, then this method will return a None.
        """
        if self.statusHistory:
            return self.statusHistory[-1].status
        else:
            return None

    def __init__(self, customerName: str, orderDate: datetime, soldBy: str, *args, **values):
        """
        Create a new instance of an Order object
        :param customerName:    The name of the customer who placed the order.  This should be
                                a migrated foreign key from a customers collection, or the
                                orders should be rolled up into the customer's collection.
        :param orderDate:       The date and time on which the order was placed.  This must be
                                part of the primary key in order to allow the same customer
                                to place more than one order.
        :param soldBy:          The name of the employee who helped the customer to place the order.
        :param args:            Additional arguments as needed.
        :param values:
        """
        super().__init__(*args, **values)
        if self.orderItems is None:
            self.orderItems = []  # initialize to no items in the order, yet.
        self.customerName = customerName
        self.orderDate = orderDate
        self.soldBy = soldBy

    def __str__(self):
        """
        Returns a string representation of the Order instance.
        :return: A string representation of the Order instance.
        """
        results = f'Order: Placed by - {self.customerName} placed on {self.orderDate} status: {self.get_current_status()}'
        for orderItem in self.orderItems:
            results = results + '\n\t' + f'Item: {orderItem.product}'
        return results

    def add_item(self, item):
        """
        Adds an item to the Order.  Note that the item argument is an instance of the
        OrderItem class, and as such has both the product that is ordered and
        the quantity.  We cannot have more than one OrderItem for any Order for the
        same product.
        :param item:    An instance of OrderItem class to be added to this Order.  If
        an OrderItem    this Product is already in the order, this call is ignored.
        :return:    None
        """
        for already_ordered_item in self.orderItems:
            if item.equals(already_ordered_item):
                return  # Already in the order, don't add it.
        self.orderItems.append(item)
        # There is no need to update the OrderItem to point to this Order because the
        # constructor for OrderItem requires an Order and that constructor calls this
        # method.  Of course, the liability here is that someone could create an instance
        # of OrderItem withOUT using our constructor.  Argh.

    def remove_item(self, item):
        """
        Removes a Product from the order.  Note that the item argument is an instance of the
        OrderItem class, but we ignore the quantity.
        :param item:    An instance of the OrderItem class that includes the Product that
                        we are removing from the order.  If this Product is not already in
                        the order, the call is ignored.
        :return:        None
        """
        for already_ordered_item in self.orderItems:
            # Check to see whether this next order item is the one that they want to delete
            if item.equals(already_ordered_item):
                # They matched on the Product, so they match.  For the remove_item use
                # case, it doesn't really matter what quantity is called for.  I only used
                # an instance of OrderItem here to be consistent with add_item.
                self.orderItems.remove(already_ordered_item)
                # At this point, the OrderItem object should be deleted since there is
                # no longer a reference to it from Order.
#                already_ordered_item.delete()
                return
