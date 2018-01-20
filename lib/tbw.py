# -*- encoding: utf8 -*-
# © Toons

import os
import io
import imp
import sys
import json
import random
import datetime
import collections

__PY3__ = True if sys.version_info[0] >= 3 else False
__FROZEN__ = hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__")

if __PY3__:
	import urllib.request as urllib2
else:
	import urllib2

if not __FROZEN__: ROOT = os.path.abspath(os.path.dirname(__file__))
else: ROOT = os.path.abspath(os.path.dirname(sys.executable))
NAME = NAME = os.path.splitext(os.path.basename(__file__))[0]

CONFIG = {}
STATUS = {}
FORGED = {}


def urlOpenRead(*args, **kw):
	result = urllib2.urlopen(*args, **kw).read()
	return result.decode() if isinstance(result, bytes) else ressult


def getBestSeed():
	best_seed = False
	height = 0
	for seed in CONFIG["peers"]:
		try:
			test = json.loads(urlOpenRead(seed+"/api/blocks/getHeight")).get("height", -1)
			if test > height:
				best_seed = seed
				height = test
		except:
			print(">>> [%s] %s seed is not responding !" % (reprNow(), seed))
	return best_seed


def getNextPayrollDay():
	now = datetime.datetime.now()
	weekday = now.weekday()
	day_to_next_key_day = (7-(weekday-CONFIG.get("payday", 6)))%7

	return datetime.datetime(
		year=now.year,
		day=now.day,
		month=now.month,
		hour=CONFIG.get("payhour", 20),
		minute=0,
		second=0
	) + datetime.timedelta(day_to_next_key_day)


def reprNow():
	return datetime.datetime.now().strftime("%x %X")


def loadConfig():
	config_file = os.path.join(ROOT, NAME+".json")
	if os.path.exists(config_file):
		with io.open(config_file) as in_:
			CONFIG.update(**json.load(in_))
	else:
		print(">>> [%s] No config file found !" % reprNow())
		quit()


def loadStatus():
	status_file = os.path.join(ROOT, NAME+".status")
	if os.path.exists(status_file):
		with io.open(status_file) as in_:
			STATUS.update(**json.load(in_))


def dumpStatus():	
	with io.open(os.path.join(ROOT, NAME+".status"), "w" if __PY3__ else "wb") as out:
		json.dump(STATUS, out, indent=4)


def loadForged():
	forged_file = os.path.join(ROOT, NAME+".forged")
	if os.path.exists(forged_file):
		with io.open(forged_file) as in_:
			FORGED.update(**json.load(in_))


def dumpForged():
	with io.open(os.path.join(ROOT, NAME+".forged"), "w" if __PY3__ else "wb") as out:
		json.dump(FORGED, out, indent=4)


def check():
	loadStatus()
	checksum = sum(STATUS.get("weight", {"":0.}).values())
	print(">>> [%s] checksum : %f" % (reprNow(), checksum))
	

def weight():
	loadStatus()
	weight = STATUS.get("weight", {"":0.})
	k = sum(weight.values())
	return dict([a,r/k] for a,r in weight.items())


def computeRound():
	global STATUS, FORGED

	seed = getBestSeed()
	resp = json.loads(urlOpenRead(seed+"/api/delegates/forging/getForgedByAccount?generatorPublicKey="+CONFIG["delegate_pubkey"]))
	
	reward = 0
	loadForged()
	if not len(FORGED):
		print(">>> [%s] initialisation !" % reprNow())
		FORGED = resp
		dumpForged()
		return False

	
	if resp["success"]:
		reward = (int(resp["rewards"]) - int(FORGED.get("rewards", 0)))/100000000.
		FORGED = resp

		if reward > 0:
			resp = json.loads(urlOpenRead(seed+"/api/delegates/voters?publicKey="+CONFIG["delegate_pubkey"]))
			if resp.get("success", False):
				loadStatus()

				now = datetime.datetime.now().toordinal()
				if now > STATUS.get("paydate", now):
					payroll_file = os.path.join(ROOT, "%s.tbw" % datetime.datetime.fromordinal(STATUS["paydate"]).strftime("%Y-%m-%d"))
					weight = STATUS.get("weight", {"":0.})
					k = sum(weight.values())
					with io.open(payroll_file, "w" if __PY3__ else "wb") as out:
						json.dump(dict([a,r/k] for a,r in weight.items()), out, indent=4)
					STATUS["weight"] = dict([a,0.] for a in weight.keys()) #.clear()

				voters = resp.get("accounts", [])
				all_addresses = [v["address"] for v in voters]
				total_balance = sum([float(v["balance"]) for v in voters])
				
				weight = STATUS.get("weight", {})

				cowards = set(weight.keys()) - set(all_addresses)
				if len(cowards):
					print(">>> [%s] down-voted by : %s" % (reprNow(), ", ".join(cowards)))
					
				newcomers = set(all_addresses) - set(weight.keys())
				if len(newcomers):
					print(">>> [%s] up-voted by : %s" % (reprNow(), ", ".join(newcomers)))

				print(">>> [%s] %d token distributed to %d voters !" % (reprNow(), int(reward), len(all_addresses)))
				STATUS = {
					"paydate": getNextPayrollDay().toordinal(),
					"weight": dict([a, weight.get(a, 0)+reward*r] for a,r in [[v["address"],float(v["balance"])/total_balance] for v in voters])
				}

				dumpStatus()
				dumpForged()


if __name__ == "__main__":
	from optparse import OptionParser

	loadConfig()

	#do something
	parser = OptionParser()
	(options, args) = parser.parse_args()
	if not len(args):
		computeRound()
	elif len(args) > 1:
		print("Only one argument in a row...")
	else:
		value = getattr(sys.modules[__name__], args[0])()
		if value: print(value)
