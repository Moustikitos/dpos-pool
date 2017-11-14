Copyright 2017 **Toons**, `MIT licence`_

Command line interface
======================

You can use ``dpos-pool`` without writing a line of code trough command
line interface.

**How to send Token ?**

::

  Welcome to dpos-pool [Python x.y.z]
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

  Welcome to dpos-pool [Python x.y.z]
  Available commands: network, account, delegate
  cold@.../> network use
  Network(s) found:
      1 - lisk
      2 - oxy
      3 - shift
      4 - toxy
  Choose an item: [1-4]> 4
  hot@toxy/network> delegate link "your secret with spaces between quotes"
  hot@toxy/delegate[username]> share <amount> --options=values

+ ``<amount>`` value can be:
   * relative value ie 10% of account balance
   * absolute value using decimal numbers 45.6
   * fiat ($60, £41, €62 or ¥125) value converted using ``coinmarketcap`` API
+ ``options`` can be :
   * ``-d`` or ``--delay`` a delay in days to check true voter weight
   * ``-b`` or ``--blacklist`` a coma-separated-address-list or a full path to newline-separated-address file
   * ``-l`` or ``--lowest`` the treshold payout to trigger payment (unpaid payout are saved)
   * ``-h`` or ``--highest`` the ceiling payout

**Easy way to manage multiple votes ?**

For blockchains allowing multiple vote per account, it can be hard to update
votes. DPOS pool propose you to manage vote from a delegate list. Just give
the final vote you want and it will send down-vote and up-vote transactions to
match exactly what you asked.

::

  hot@toxy/delegate[username]> account
  hot@toxy/account[15600...1854X]> vote -m <delegates>

+ ``<delegates>`` value can be:
   * a coma-separated username list
   * a ath to a file containing new-line-separated username list

Windows users
=============

Download `latest relase`_ from github, extract archive and run ``pool.exe``

Other OS users
==============

You can run the dpos-pool from source.

+ Install Python 3.5 or 3.6
+ install Arky AIP11 from github : 
   * Ubuntu : ``sudo -H pip3 install https://github.com/Moustikitos/arky/archive/aip11.zip``
   * Other OS : ``pip install https://github.com/Moustikitos/arky/archive/aip11.zip``
+ download `dpos-tool`_ from github
+ exctract archive and go to : ``dpos-tool/arky_1.x``
+ run pool :
   * Ubuntu : ``python3 pool.py``
   * Other OS : ``python -m pool`` or ``python pool.py``

Authors
=======

Toons <moustikitos@gmail.com>

Support this project
====================

+ Toons Bitcoin address: ``1qjHtN5SuzvcA8RZSxNPuf79iyLaVjxfc``
+ Toons Ark address: ``AUahWfkfr5J4tYakugRbfow7RWVTK35GPW``
+ Toons Oxycoin address: ``12427608128403844156X``

.. _MIT licence: http://htmlpreview.github.com/?https://github.com/Moustikitos/oxycoin/blob/master/pyoxy.html
.. _latest relase: https://github.com/Moustikitos/dpos-pool/releases
.. _dpos-tool: https://github.com/Moustikitos/dpos-pool/archive/master.zip
