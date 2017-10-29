# -*- encoding: utf8 -*-
# © Toons
import arky.cli
from arky import cfg, api
from arky.util import stats
from arky.cli import delegate, common
import io, os, sys

if sys.platform.startswith("win"):
    for version in ["2.7", "3.5", "3.6"]:
        os.system('''py -%s -c "import py_compile;py_compile.compile('private/pshare.py', cfile='pshare%s.pyc')"''' % (version, version.replace(".", "")))

try:
    version_info = sys.version_info[:2]
    if version_info == (2, 7): import pshare27 as pshare
    elif version_info == (3, 5): import pshare35 as pshare
    elif version_info == (3, 6): import pshare36 as pshare
    SHARE = True
except ImportError:
    SHARE = False


def share(param):

    delegate.KEY2 = common.checkKeys(delegate.KEY1, delegate.KEY2, delegate.ADDRESS)
    if delegate.KEY2:
        if SHARE:
            if param["--blacklist"]:
                if os.path.exists(param["--blacklist"]):
                    with io.open(param["--blacklist"], "r") as in_:
                        blacklist = [e for e in in_.read().split() if e != ""]
                else:
                    blacklist = param["--blacklist"].split(",")
            else:
                blacklist = []

            amount = common.floatAmount(param["<amount>"], delegate.ADDRESS)
            if param["--complement"]:
                amount = float(api.Account.getBalance(delegate.ADDRESS, returnKey="balance")) / 100000000. - amount

            if param["--lowest"]:
                minimum = float(param["--lowest"]) + cfg.__FEES__["send"] / 100000000.
            else:
                minimum = cfg.__FEES__["send"] / 100000000.

            if param["--highest"]:
                maximum = float(param["--highest"]) + cfg.__FEES__["send"] / 100000000.
            else:
                maximum = amount

            if amount > 1:
                # get contributions of ech voters
                delay = int(param["--delay"])
                delegate_pubk = common.hexlify(delegate.PUBLICKEY)
                accounts = api.Delegate.getVoters(delegate_pubk, returnKey="accounts")
                addresses = [a["address"] for a in accounts]  # + hidden
                sys.stdout.write("Checking %s-day-true-vote-weight in transaction history...\n" % delay)
                contribution = dict([address, stats.getVoteForce(address, days=delay, delegate_pubk=delegate_pubk)] for address in [addr for addr in addresses if addr not in blacklist])
                
                # apply filters
                C = sum(contribution.values())
                max_C = C*maximum/amount
                cumul = 0
                # first filter
                for address, force in [(a, f) for a, f in contribution.items() if f >= max_C]:
                    contribution[address] = max_C
                    cumul += force - max_C
                # report cutted share
                untouched_pairs = sorted([(a, f) for a, f in contribution.items() if 0. < f < max_C], key=lambda e: e[-1], reverse=True)
                n, i = len(untouched_pairs), 0
                bounty = cumul / n
                for address, force in untouched_pairs:
                    if force + bounty > max_C:
                        i += 1
                        n -= 1
                        contribution[address] = max_C
                        cumul -= abs(max_C - force)
                        bounty = cumul / n
                    else:
                        break
                for address, force in untouched_pairs[i:]:
                    contribution[address] += bounty

                # apply contribution
                k = 1.0 / max(1, sum(contribution.values()))
                contribution = dict((a, s * k) for a, s in contribution.items())
                txgen = lambda addr, amnt, msg: common.generateColdTx(delegate.KEY1, delegate.PUBLICKEY, delegate.KEY2, type=0, amount=amnt, recipientId=addr, vendorField=msg)
                pshare.applyContribution(delegate.USERNAME, amount, minimum, param["<message>"], txgen, **contribution)

        else:
            sys.stdout.write("Share feature not available\n")


if __name__ == "__main__":

    delegate.__doc__ = """
Usage: delegate link [<secret> <2ndSecret>]
       delegate save <name>
       delegate unlink
       delegate status
       delegate voters
       delegate share <amount> [-c -b <blacklist> -d <delay> -l <lowest> -h <highest> <message>]

Options:
-b <blacklist> --blacklist <blacklist> ark addresses to exclude (comma-separated list or pathfile)
-h <highest> --highest <hihgest>       maximum payout in ARK
-l <lowest> --lowest <lowest>          minimum payout in ARK
-d <delay> --delay <delay>             number of fidelity-day [default: 30]
-c --complement                        share the amount complement

Subcommands:
    link   : link to delegate using secret passphrases. If secret passphrases
             contains spaces, it must be enclosed within double quotes
             ("secret with spaces"). If no secret given, it tries to link
             with saved account(s).
    save   : save linked delegate to a *.tokd file.
    unlink : unlink delegate.
    status : show information about linked delegate.
    voters : show voters contributions ([address - vote] pairs).
    share  : share ARK amount with voters (if any) according to their
             weight (1% mandatory fees). You can set a 64-char message.
"""
    delegate.share = share
    arky.cli.start()

# ## `share` command for pool runners

# `delegate` subsection allow user doing some basic checkings about their forging
# node. A special `share` command is designed to give back voters part of forged
# ark according to their vote weight.

# ### `<amount>`

# you can specify ARK amount:
# ```
# hot@dark/delegate[username]> share 600
# Checking 30-day-true-vote-weight in transaction history...
# ...
# ```

# percentage of delegate balance:
# ```
# hot@dark/delegate[username]> share 60%
# Checking 30-day-true-vote-weight in transaction history...
# ...
# ```

# fiat-currency amount:
# ```
# hot@ark/delegate[username]> share $600
# $600=A716.633542 (A/$=0.837248) - Validate ? [y-n]> y
# Checking 30-day-true-vote-weight in transaction history...
# ...
# ```

# ### --delay / -d :: True-vote-weight

# To deter vote hoppers using your pool, a true-vote-weight is computed over a number of day in transaction history.

# For each voter, `arky.cli` will integrate balance in ARK of the voting account over time in hours. It is actually the surface defined between balance curve and well known X-axis.

# So, a 50K hopper voting on your sharing pool 12 hour before sharing happen will represent: 50,000.0 * 12 = 600,000.0 ARK.hour.
# If you run a true-vote-weight:
#   * over 7 days, it is equivalent to 600,000.0 / (7*24) = 3571 ARK weight vote
#   * over 14 days, it is equivalent to 600,000.0 / (14*24) = 1785 ARK weight vote
#   * over 30 days, it is equivalent to 600,000.0 / (30*24) = 833 ARK weight vote

# ### --blacklist / -b

# For whatever reason you wish to ban ark account.

# You can specify coma-separated ARK addresses:
# ```
# hot@dark/delegate[username]> share 600 -b ARKdelegate.ADDRESS001,ARKdelegate.ADDRESS002,ARKdelegate.ADDRESS003
# ```

# You can specify a file containing new-line-separated addresses:

# ```
# ARKdelegate.ADDRESS001
# ARKdelegate.ADDRESS002
# ARKdelegate.ADDRESS003
# ```

# ```
# hot@dark/delegate[username]> share 600 -b /path/to/file
# ```

# ### --highest / -h

# You can specify a maximum payout. The cutted reward is equally-distributed to all other voters.

# ### --lowest / -l

# You can specify a minimum payout. All voters not reaching the lowest value are excluded from the round.

# ### --complement / -c

# Use this option if you want to send a payout round thinking about what you want to keep on your delegate account.

# If you want to keep 600 ARK on your account :
# ```
# hot@dark/delegate[username]> share 600 -c
# ```

# If you want to keep $600 on your account :
# ```
# hot@dark/delegate[username]> share $600 -c
# ```

# If you want to keep 6% on your account :
# ```
# hot@dark/delegate[username]> share 6% -c
# ```

import os, sys
if sys.platform.startswith("win"):
	for version in ["2.7", "3.5", "3.6"]:
		os.system('''py -%s -c "import py_compile;py_compile.compile('arky/cli/private/pshare.py', cfile='arky/cli/private/pshare%s.pyc')"''' % (version, version.replace(".", "")))


# rem -z arky/cli/private/pshare35.pyc=arky/cli/pshare35.pyc
