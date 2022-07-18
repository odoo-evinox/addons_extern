==========
Nexterp Stock Date
==========
Features:
    On picking a new filed accounting_date ( Accounting Date) and Date_done_effecte ( in case of accounting date is set, efective date should be accounting date, and in date_done_effecte is time when we presset the receive button).
    
    If accounting_date field is set, all the stock_valuation_layer and accounting_entries ( if is a notice) will have this date.
    
    If accounting_date filed is not set, will be taken into account the time when you pres the receive button.
    
    At processing, date can not be in future.
    
    If you have a purchase in foreign currency, and you are making a reception at a date, the price_unit will be computed with the rate from the Accounting Date or date when the transfer is done

    In stock_valuation_layer you have a field create_date_in_reality because the original create_date is with this module the accounting_date
    
    On product you will not able to change the on hand qty.
    
Obs:
    If you recive a product at a date with price of x, than you return it with fifo returned price can be diffrent than x

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

