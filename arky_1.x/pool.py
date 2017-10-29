# -*- encoding: utf8 -*-
# © Toons

import os, imp, sys, collections
__PY3__ = True if sys.version_info[0] >= 3 else False
__FROZEN__ = hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__")


if not __FROZEN__:
	FOLDER = os.path.dirname(__file__)
	# if sys.platform.startswith("win"):
	# 	for version in ["2.7", "3.5", "3.6"]:
	# 		os.system('''py -%s -c "import py_compile;py_compile.compile('private/pshare.py', cfile='pshare%s.pyc')"''' % (version, version.replace(".", "")))
else:
	FOLDER = os.path.dirname(sys.executable)
# sys.path.insert(0, os.path.join(FOLDER, "../../ark-new"))

try:
	version_info = sys.version_info[:2]
	if version_info == (2, 7): import pshare27 as pshare
	elif version_info == (3, 5): import pshare35 as pshare
	elif version_info == (3, 6): import pshare36 as pshare
	SHARE = True
except ImportError:
	SHARE = False


import arky
from arky import cfg
from arky import cli
from arky import rest
from arky import util


def _payroll(param):

	if cli.DATA.delegate:
		payroll_json = "%s-%s.payroll" % (cli.DATA.delegate["username"], cfg.network)
		payroll = util.loadJson(payroll_json, FOLDER)

		ongoing = {}
		if payroll:
			ongoing_json = "%s-%s.ongoing" % (cli.DATA.delegate["username"], cfg.network)

			for recipientId, amount in list(payroll.items()):
				tx = arky.core.crypto.bakeTransaction(
					amount=amount,
					recipientId=recipientId,
					vendorField=param.get("<message>", None),
					publicKey=cli.DATA.firstkeys["publicKey"],
					privateKey=cli.DATA.firstkeys["privateKey"],
					secondPrivateKey=cli.DATA.secondkeys.get("privateKey", None)
				)
				ongoing[tx["id"]] = tx
				sys.stdout.write("Sending %.8f %s to %s...\n" % (tx["amount"]/100000000, cfg.token, tx["recipientId"]))
				if util.prettyPrint(arky.core.sendPayload(tx)):
					payroll.pop(recipientId, None)
					
			util.dumpJson(ongoing, ongoing_json, FOLDER)
			util.dumpJson(payroll, payroll_json, FOLDER)

			if cli.checkRegisteredTx(ongoing_json).wait():
				util.popJson(payroll_json, FOLDER)
				util.popJson(ongoing_json, FOLDER)


def _getVoteForce():
	pass


def share(param):
	
	if cli.DATA.delegate and SHARE:
		# get blacklisted addresses
		if param["--blacklist"]:
			if os.path.exists(param["--blacklist"]):
				with io.open(param["--blacklist"], "r") as in_:
					blacklist = [e for e in in_.read().split() if e != ""]
			else:
				blacklist = param["--blacklist"].split(",")
		else:
			blacklist = []

		# separate fees from rewards
		forged_json = "%s-%s.forged" % (cli.DATA.delegate["username"], cfg.network)
		forged_details = rest.GET.api.delegates.forging.getForgedByAccount(generatorPublicKey=cli.DATA.delegate["publicKey"])
		rewards = int(forged_details["rewards"])
		last = util.loadJson(forged_json, FOLDER)
		if "rewards" in last:
			rewards -= int(last["rewards"])
		else:
			blockreward = int(rest.GET.api.blocks.getReward(returnKey="reward"))
			rewards = int(cli.DATA.account["balance"]) * rewards/float(forged_details["forged"])
			rewards = (rewards//blockreward)*blockreward
		forged_details.pop("success", False)

		# computes amount to share using reward
		if param["<amount>"].endswith("%"):
			amount = int(float(param["<amount>"][:-1])/100 * rewards)
		elif param["<amount>"][0] in ["$", "€", "£", "¥"]:
			price = util.getTokenPrice(cfg.token, {"$":"usd", "EUR":"eur", "€":"eur", "£":"gbp", "¥":"cny"}[amount[0]])
			result = float(param["<amount>"][1:])/price
			if util.askYesOrNo("%s=%f %s (%s/%s=%f) - Validate ?" % (amount, result, cfg.token, cfg.token, amount[0], price)):
				amount = int(min(rewards, result*100000000))
			else:
				sys.stdout.write("    Share command canceled\n")
				return
		else:
			amount = int(min(rewards, float(param["<amount>"])*100000000))

		# define treshold and ceiling
		if param["--lowest"]:
			minimum = int(float(param["--lowest"])*100000000 + cfg.fees["send"])
		else:
			minimum = int(cfg.fees["send"])
		if param["--highest"]:
			maximum = int(float(param["--highest"])*100000000 + cfg.fees["send"])
		else:
			maximum = amount

		if amount > 100000000:
			sys.stdout.write("Writing share for %.8f %s\n" % (amount/100000000, cfg.token))
			# get voter contributions
			voters = rest.GET.api.delegates.voters(publicKey=cli.DATA.delegate["publicKey"]).get("accounts", []) 
			contributions = dict([v["address"], int(v["balance"])] for v in voters if v["address"] not in blacklist)
			k = 1.0 / max(1, sum(contributions.values()))
			contributions = dict((a, b*k) for a,b in contributions.items())

			waiting_json = "%s-%s.waiting" % (cli.DATA.delegate["username"], cfg.network)
			payroll_json = "%s-%s.payroll" % (cli.DATA.delegate["username"], cfg.network)
			saved_payroll = util.loadJson(waiting_json, FOLDER)
			tosave_payroll = {}
			complement = {}
			payroll = collections.OrderedDict()

			for address, ratio in contributions.items():
				share = amount*ratio + saved_payroll.pop(address, 0)
				if share >= maximum:
					payroll[address] = int(maximum)
				elif share < minimum:
					tosave_payroll[address] = int(share)
				else:
					complement[address] = share
			
			pairs = list(pshare.applyContribution(**complement).items())
			for address, share in pairs:
				if share < minimum:
					tosave_payroll[address] = share
				else:
					payroll[address] = share
			
			sys.stdout.write("Payroll in SATOSHI [%s file]:\n" % payroll_json)
			util.prettyPrint(payroll)
			sys.stdout.write("Saved payroll in SATOSHI [%s file]):\n" % waiting_json)
			util.prettyPrint(tosave_payroll)

			if util.askYesOrNo("Validate share payroll ?"):
				tosave_payroll.update(saved_payroll)
				util.dumpJson(tosave_payroll, waiting_json, FOLDER)
				util.dumpJson(payroll, payroll_json, FOLDER)
				util.dumpJson(forged_details, forged_json, FOLDER)

				_payroll(param)
			else:
				sys.stdout.write("    Share canceled\n")
		else:
			sys.stdout.write("    No reward to send since last share\n")
	else:
		sys.stdout.write("    Share feature not available\n")


if __name__ == "__main__":
	cli.delegate.__doc__ = """
Usage: delegate link [<secret> <2ndSecret>]
       delegate unlink
       delegate status
       delegate voters
       delegate share <amount> [-b <blacklist> -d <delay> -l <lowest> -h <highest> <message>]

Options:
-b <blacklist> --blacklist <blacklist> addresses to exclude (comma-separated list or pathfile)
-h <highest> --highest <hihgest>       maximum payout in token
-l <lowest> --lowest <lowest>          minimum payout in token
-d <delay> --delay <delay>             number of fidelity-day

Subcommands:
    link   : link to delegate using secret passphrases. If secret passphrases
             contains spaces, it must be enclosed within double quotes
             ("secret with spaces"). If no secret given, it tries to link
             with saved account(s).
    unlink : unlink delegate.
    status : show information about linked delegate.
    voters : show voters contributions ([address - vote] pairs).
    share  : write share payroll for voters (if any) according to their
             weight (there are mandatory fees)
"""
	cli.delegate.share = share
	cli.start()
