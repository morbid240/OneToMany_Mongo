"""
Malcolm Roddy
CECS 323 S01
One to many mongodb

This self made file is for the PriceHistory that takes an embedded document
essentially its just a list of objects identified by product

modeled off of statuschange

needed to use bson to use Decimal128
converts from string to a Decimal128 initially
"""
from mongoengine import *
import datetime
from bson import Decimal128

class PriceHistory(EmbeddedDocument):
    """
    Each time there is a new price for a product, another instance of this class is
    added to the list of price history for that order.  They will always be
    appended to the end of the list, and never deleted, so that makes it pretty
    easy to manage the list of price changes.
    attributes: new_price NN, price_change_date NN
    """
    newPrice = Decimal128Field(db_field='new_price', min_value=0.1, precision=2, required=True) # should be same as buy price validation
    priceChangeDate = DateTimeField(db_field='price_change_date', required=True)

    def __init__(self, newPrice: str, priceChangeDate: datetime, *args, **kwargs):
        """Constructor, made sure argument type is newPrice since its a mongoengine object type"""
        super().__init__(*args, **kwargs)
        self.newPrice = Decimal128(newPrice)
        self.priceChangeDate = priceChangeDate

    def __str__(self):
        return f'Price History Entry: New price: {self.newPrice}, on date: {self.priceChangeDate}'
