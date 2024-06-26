"""
Malcolm Roddy
CECS 323
One to Many MongoDb

This handles the product class. Parent to OrderItem
"""

from mongoengine import *
from datetime import datetime
from PriceHistory import PriceHistory
from bson import Decimal128


class Product(Document):
    """An individual item that has a varying price sold by an enterprise"""
    # unique keys
    productCode = StringField(db_field='product_code', max_length=15, required=True)
    productName = StringField(db_field='product_name', max_length=70, required=True)
    # other attributes
    productDescription = StringField(db_field='product_description', max_length=800, required=True)
    quantityInStock = IntField(db_field='quantity_in_stock', min_value=0, required=True)
    buyPrice = Decimal128Field(db_field='buy_price', min_value=0.01, precision=2, required=True)
    msrp = Decimal128Field(db_field='msrp', min_value=0.01, precision=2, required=True)
    priceHistory = ListField(EmbeddedDocumentField(PriceHistory, db_field='price_history'))

    # The delete rule to protect Product from losing Order Items will be in main.py.
    orderItems = ListField(ReferenceField('OrderItem'))
    # Uniqueness constraint/ index creation
    meta = {'collection': 'products',
            'indexes': [
                {'unique': True, 'fields': ['productName', 'productCode'], 'name': 'products_pk'}
            ]}

    def __init__(self, productCode: str, productName: str, productDescription: str, quantityInStock: int, buyPrice: str, msrp: str, *args, **values):
        """Create a new instance of Product object
        NOTE: Have to make sure to convert string value to Decimal 128. Cannot do with float
        """
        super().__init__(*args, **values)
        self.productName = productName
        self.productCode = productCode
        self.productDescription = productDescription
        self.quantityInStock = quantityInStock
        self.buyPrice = Decimal128(buyPrice)
        self.msrp = Decimal128(msrp)
        if self.orderItems is None:
            self.orderItems = []  # initialize to no items in the product, yet.

    def change_price(self, new_price: PriceHistory):
        """
        Every time the price changes for the product, we add another instance of PriceHistory to
        the history list of price changes.
        """
        if self.priceHistory:
            current_price = self.priceHistory[-1] # get latest price
            if current_price.newPrice == new_price.newPrice:
                raise ValueError('This is already the newest price.')
            if current_price.priceChangeDate >= new_price.priceChangeDate:
                raise ValueError('New price must be later than the latest price change.')
            if new_price.priceChangeDate > datetime.utcnow():
                raise ValueError('The status change cannot occur in the future.')
            self.priceHistory.append(new_price) # append to price history list
        else:
            self.priceHistory = [new_price]   # This is the first price "change".

    def get_current_price(self) -> PriceHistory:
        """
        Get the current price of the product
        """
        if self.priceHistory:
            return self.priceHistory[-1].newPrice
        else:
            return None


    def __str__(self):
        """
        Returns a string representation of the Product instance.
        Note: returns the price stored as instance of PriceHistory
        """
        results = f'Product code: {self.productCode} Product Name: {self.productName} current price: {self.get_current_price()}'
        # print out orderitems that the product appears in
        for orderItem in self.orderItems:
            results = results + '\n\t' + f'Item: {orderItem.product}'
        return results


    """Handling order_items list, deletion and insertion. COPIED from Order"""
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
