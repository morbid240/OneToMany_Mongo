from enum import Enum
"""The enumeration of the available status values.  These are taken from the Practice SQL homework.  The
status names are listed in alphabetical order, not necessarily the order in which a given order would 
go through these statuses.  There is no strict workflow in effect here.  An order could visit a given 
status more than once.  Some rules suggest themselves, but I'm not going to implement them.  For instance,
an order can only go to 'resolved' if it is currently in 'disputed'.  It should go into 'in process' initially.
Once an order has 'shipped', I would think that no further status changes are possible.  In this application,
the only requirement that I'm implementing is that the next status cannot equal the current one."""


class Status(Enum):
    CANCELLED = 'cancelled'
    DISPUTED = 'disputed'
    IN_PROCESS = 'in process'
    ON_HOLD = 'on hold'
    RESOLVED = 'resolved'
    SHIPPED = 'shipped'

