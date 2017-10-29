Copyright 2017 **Toons**, `MIT licence`_


Command line interface
======================

You can use ``dpos-pool`` without writing a line of code trough command
line interface.

**How to send Oxycoins ?**

::

  Welcome to arky-cli [Python 3.6.0 / arky 1.0a0]
  Available commands: network, account, delegate
  cold@.../> network use
  Network(s) found:
      1 - lisk
      2 - oxy
      3 - shift
      4 - toxy
  Choose an item: [1-4]> 4
  hot@toxy/network> account link "your secret with spaces between quotes"
  hot@toxy/account[15600...1854X]> send 1.1235 12427608128403844156X
  {'success': True}

**How to run a pool ?**

::

  Welcome to arky-cli [Python 3.6.0 / arky 1.0a0]
  Available commands: network, account, delegate
  cold@.../> network use
  Network(s) found:
      1 - lisk
      2 - oxy
      3 - shift
      4 - toxy
  Choose an item: [1-4]> 4
  hot@toxy/network> delegate link "your secret with spaces between quotes"
  hot@toxy/account[15600...1854X]> share <amoun> --options=values

+ ``<amount>`` value can be:
   * relative value ie 10% of account balance
   * absolute value using decimal numbers 45.6
   * fiat ($60, £41, €62 or ¥125) value converted using ``coinmarketcap`` API
+ ``options`` can be :
   * ``-b`` or ``--blacklist`` a coma-separated-address-list or a full path to newline-separated-address file
   * ``-l`` or ``--lowest`` the treshold payout to trigger payment (unpaid payout are saved)
   * ``-h`` or ``--highest`` the ceiling payout


Authors
=======

Toons <moustikitos@gmail.com>

Support this project
====================

+ Toons Bitcoin address: ``1qjHtN5SuzvcA8RZSxNPuf79iyLaVjxfc``
+ Toons Oxycoin address: ``12427608128403844156X``

.. _MIT licence: http://htmlpreview.github.com/?https://github.com/Moustikitos/oxycoin/blob/master/pyoxy.html
