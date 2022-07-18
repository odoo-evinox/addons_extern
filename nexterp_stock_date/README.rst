==========
Nexterp Stock Date
==========
Features:
    On picking a new filed date ( Accounting Date).
    If this field is set, all the stock_valuation_layer and accounting_entries ( if is a notice) will have this date.
    If this filed is not set, will be taken into account the processing date.
    At processing, date can not be in future.
    
    If you have a purchase in foreign currency, and you are making a reception at a date, the price_unit will be computed with the rate from the Accounting Date or date when the transfer is done

    In stock_valuation_layer you have a field create_date_in_reality because the original create_date is with this module the accounting_date
    
    On product you will not able to change the on hand qty

**Table of contents**

.. contents::
   :local:

Bug Tracker
===========

Credits
=======

Authors
~~~~~~~

* Nexterp Romania SRL

Maintainers
~~~~~~~~~~~

