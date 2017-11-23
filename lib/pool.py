# -*- encoding: utf8 -*-
# © Toons

import os, io, imp, sys, collections
__PY3__ = True if sys.version_info[0] >= 3 else False
__FROZEN__ = hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__")


if not __FROZEN__:
	FOLDER = os.path.dirname(__file__)
else:
	FOLDER = os.path.dirname(sys.executable)

try:
	pshare = __import__("pshare%s%s" % sys.version_info[:2], globals(), locals(), [], 0)
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
		ongoing_json = "%s-%s.ongoing" % (cli.DATA.delegate["username"], cfg.network)
		ongoing = util.loadJson(ongoing_json, FOLDER)

		if payroll:
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
				payroll.pop(recipientId, None)
				sys.stdout.write("Sending %.8f %s to %s...\n" % (tx["amount"]/100000000, cfg.token, tx["recipientId"]))
				util.prettyPrint(arky.core.sendPayload(tx))
				util.dumpJson(payroll, payroll_json, FOLDER)
				util.dumpJson(ongoing, ongoing_json, FOLDER)

			util.popJson(payroll_json, FOLDER)

		if cli.checkRegisteredTx(ongoing_json, FOLDER).wait():
			util.popJson(ongoing_json, FOLDER)


def checkPayloadApplied(payload):
	LOCK = None
	sys.stdout.write("Waiting for payload being applied...\n")
	@util.setInterval(cfg.blocktime)
	def _checkPayload(payload):
		if rest.GET.api.transactions.get(id=payload["id"]).get("success", False):
			LOCK.set()
		else:
			arky.core.sendPayload(payload)
	LOCK = _checkPayload(payload)
	return LOCK


_vote = cli.account.vote
def vote(param):

	if cli.DATA.account and param["--manage"]:
		if os.path.exists(param["<delegates>"]) and param["<delegates>"] != "":
			with io.open(param["<delegates>"], "r") as in_:
				candidates = [e for e in in_.read().split() if e != ""]
		else:
			candidates = [c for c in param["<delegates>"].split(",") if c != ""]

		voted = rest.GET.api.accounts.delegates(address=cli.DATA.account["address"]).get("delegates", [])
		voted = [d["username"] for d in voted]

		unvote = [d for d in voted if d not in candidates]
		vote = [d for d in candidates if d not in voted]

		all_delegates = util.getCandidates()
		if len(unvote) and cli.checkSecondKeys():
			for i in range(0, len(unvote), cfg.maxvotepertx):
				lst = [d["publicKey"] for d in all_delegates if d["username"] in unvote[i:i+cfg.maxvotepertx]]
				if len(lst):
					payload = arky.core.crypto.bakeTransaction(
						type=3,
						recipientId=cli.DATA.account["address"],
						publicKey=cli.DATA.firstkeys["publicKey"],
						privateKey=cli.DATA.firstkeys["privateKey"],
						secondPrivateKey=cli.DATA.secondkeys.get("privateKey", None),
						asset={"votes": ["-%s"%pk for pk in lst]}
					)
					sys.stdout.write("Broadcasting down-vote for %s\n" % (",".join(unvote[i:i+cfg.maxvotepertx])))
					util.prettyPrint(arky.core.sendPayload(payload))
					checkPayloadApplied(payload).wait()

		if len(vote) and cli.checkSecondKeys():
			for i in range(0, len(vote), cfg.maxvotepertx):
				lst = [d["publicKey"] for d in all_delegates if d["username"] in vote[i:i+cfg.maxvotepertx]]
				if len(lst):
					payload = arky.core.crypto.bakeTransaction(
						type=3,
						recipientId=cli.DATA.account["address"],
						publicKey=cli.DATA.firstkeys["publicKey"],
						privateKey=cli.DATA.firstkeys["privateKey"],
						secondPrivateKey=cli.DATA.secondkeys.get("privateKey", None),
						asset={"votes": ["+%s"%pk for pk in lst]}
					)
					sys.stdout.write("Broadcasting up-vote for %s\n" % (",".join(vote[i:i+cfg.maxvotepertx])))
					util.prettyPrint(arky.core.sendPayload(payload))
					checkPayloadApplied(payload).wait()

	else:
		_vote(param)


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
			rewards = int(cli.DATA.account["balance"]) * rewards/max(1, float(forged_details["forged"]))
			rewards = (rewards//blockreward)*blockreward
		forged_details.pop("success", False)

		# computes amount to share using reward
		if param["<amount>"].endswith("%"):
			amount = int(float(param["<amount>"][:-1])/100 * rewards)
		elif param["<amount>"][0] in ["$", "€", "£", "¥"]:
			price = util.getTokenPrice(cfg.token, {"$":"usd", "EUR":"eur", "€":"eur", "£":"gbp", "¥":"cny"}[amount[0]])
			result = float(param["<amount>"][1:])/price
			if cli.askYesOrNo("%s=%f %s (%s/%s=%f) - Validate ?" % (amount, result, cfg.token, cfg.token, amount[0], price)):
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
			if param["--delay"]:
				delay = int(param["--delay"])
				sys.stdout.write("Checking %s day%s true vote weight...\n" % (delay, "s" if delay > 1 else ""))
				contributions = {}
				for voter in [v for v in voters if v["address"] not in blacklist]:
					voteforce = util.getVoteForce(voter["address"], days=delay)
					contributions[voter["address"]] = voteforce
					sys.stdout.write("    %s : %.2f\n" % (voter["address"], voteforce))
			else:
				contributions = dict([v["address"], int(v["balance"])] for v in voters if v["address"] not in blacklist)
			k = 1.0 / max(1, sum(contributions.values()))
			contributions = dict((a, b*k) for a,b in contributions.items())

			waiting_json = "%s-%s.waiting" % (cli.DATA.delegate["username"], cfg.network)
			payroll_json = "%s-%s.payroll" % (cli.DATA.delegate["username"], cfg.network)
			saved_payroll = util.loadJson(waiting_json, FOLDER)
			tosave_payroll = {}
			complement = {}
			payroll = {}

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
			
			payroll = collections.OrderedDict(sorted(payroll.items(), key=lambda e:e[-1]))
			tosave_payroll = collections.OrderedDict(sorted(tosave_payroll.items(), key=lambda e:e[-1]))
			sys.stdout.write("Payroll in SATOSHI [%s file]:\n" % payroll_json)
			util.prettyPrint(payroll)
			sys.stdout.write("Saved payroll in SATOSHI [%s file]):\n" % waiting_json)
			util.prettyPrint(tosave_payroll)

			if cli.askYesOrNo("Validate share payroll ?") \
			   and cli.checkSecondKeys():
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


def resume(param):
	_payroll(param)


if __name__ == "__main__":

	cli.__doc__ = """Welcome to dpos-pool [Python %(python)s]
Available commands: %(sets)s""" % {"python": sys.version.split()[0], "sets": ", ".join(cli.__all__)}

	cli.delegate.__doc__ = """
Usage:
    delegate link <secret> [<2ndSecret>]
    delegate unlink
    delegate status
    delegate voters
    delegate forged
    delegate share <amount> [-b <blacklist> -d <delay> -l <lowest> -h <highest> <message>]
    delegate resume [<message>]

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
    forged : show forge report.
    share  : write share payroll for voters (if any) according to their
             weight (there are mandatory fees).
    resume : resume delegate payroll.
"""

	cli.account.__doc__ = """
Usage:
    account link <secret> [<2ndSecret>|-e]
    account unlink
    account status
    account register <username>
    account register 2ndSecret <secret>
    account register escrow <thirdparty>
    account validate <registry>
    account vote [-udm] [<delegates>]
    account send <amount> <address> [<message>]

Options:
-e --escrow  link as escrowed account
-u --up      up vote delegate name folowing
-d --down    down vote delegate name folowing
-m --manage  send vote transactions to match asked delegates

Subcommands:
    link     : link to account using secret passphrases. If secret passphrases
               contains spaces, it must be enclosed within double quotes
               (ie "secret with spaces").
    unlink   : unlink account.
    status   : show information about linked account.
    register : register linked account as delegate;
               or
               register second signature to linked account;
			   or
               register an escrower using an account address or a publicKey.
    validate : validate transaction from registry.
    vote     : up or down vote delegate(s). <delegates> can be a coma-separated list
               or a valid new-line-separated file list conaining delegate usernames.
    send     : send ARK amount to address. You can set a 64-char message.
"""

	cli.account.vote = vote
	cli.delegate.share = share
	cli.delegate.resume = resume

	if len(sys.argv) > 1 and os.path.exists(sys.argv[-1]):
		cli.launch(sys.argv[-1])
	else:
		cli.start()
