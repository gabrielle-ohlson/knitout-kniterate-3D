import numpy as np
import math
import warnings

from distutils import util

from copy import deepcopy

from PIL import Image, ImageColor

#NOTE: for gauge > 1: decided baseBed should consistently be front so as to make things less complicated (because doesn't really matter) --- so translation would be fn -> f(gauge*n) bn -> b((gauge*n)+1)

#---------------------------------------------
#--- CUSTOMIZABLE VARIABLES FOR EXTENSIONS ---
#---------------------------------------------
#for waste section
wasteSpeedNumber = 400
wasteStitchNumber = 4

#for main section
speedNumber = 300
stitchNumber = 4
rollerAdvance = 300

#for xfers
xferSpeedNumber = 300
xferStitchNumber = math.ceil(stitchNumber//2)
xferRollerAdvance = 0

#for splits
splitSpeedNumber = 100
splitStitchNumber = 4
splitRollerAdvance = 0

#for wasteWeights
wasteWeightsRowCount = 20

#----------------------
#--- MISC FUNCTIONS ---
#----------------------
def query_yes_no(question, default=None):
	if default is None:
		prompt = " [y/n] "
	elif default == 'yes':
		prompt = " [Y/n] "
	elif default == 'no':
		prompt = " [y/N] "
	else:
		raise ValueError(f"Unknown setting '{default}' for default.")

	while True:
		try:
			resp = input(question + prompt).strip().lower()
			if default is not None and resp == '':
				return default == 'yes'
			else:
				return util.strtobool(resp)
		except ValueError:
			print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def colorDistance(rgb1, rgb2, returnRGBs=False):
	np_rgb1 = np.array(list(rgb1))
	np_rgb2 = np.array(list(rgb2))

	rm = 0.5*(np_rgb1[0]+np_rgb2[0])
	d = abs(sum((2+rm, 4, 3-rm) * (np_rgb1-np_rgb2)**2))**0.5
	if returnRGBs: return d, rgb1, rgb2
	else: return d


def setSettings(k=None, speed=None, stitch=None, roller=None, xferSpeed=None, xferStitch=None, xferRoller=None, splitSpeed=None, splitStitch=None, splitRoller=None, wasteSpeed=None, wasteStitch=None):
	'''
	*TODO
	'''
	if speed is not None:
		globals()['speedNumber'] = speed
		if k is not None: k.speedNumber(speed)
	if stitch is not None:
		globals()['stitchNumber'] = stitch
		if k is not None: k.stitchNumber(stitch)

	if roller is not None:
		globals()['rollerAdvance'] = roller
		if k is not None: k.rollerAdvance(roller)

	if xferSpeed is not None: globals()['xferSpeedNumber'] = xferSpeed
	if xferStitch is not None:
		globals()['xferStitchNumber'] = xferStitch
		if k is not None: k.xferStitchNumber(xferStitch) #only xfer setting with dedicated extension
	if xferRoller is not None: globals()['xferRollerAdvance'] = xferRoller

	if splitSpeed is not None: globals()['splitSpeedNumber'] = splitSpeed
	if splitStitch is not None: globals()['splitStitchNumber'] = splitStitch
	if splitRoller is not None: globals()['splitRollerAdvance'] = splitRoller

	if wasteSpeed is not None: globals()['wasteSpeedNumber'] = wasteSpeed
	if wasteStitch is not None: globals()['wasteStitchNumber'] = wasteStitch


def defaultSettings(k=None):
	#for main section 
	globals()['speedNumber'] = 300
	globals()['stitchNumber'] = 4
	globals()['rollerAdvance'] = 300

	#for xfers
	globals()['xferSpeedNumber'] = 300
	globals()['xferStitchNumber'] = math.ceil(stitchNumber//2)
	globals()['xferRollerAdvance'] = 0

	#for splits
	globals()['splitSpeedNumber'] = 100
	globals()['splitStitchNumber'] = 4
	globals()['splitRollerAdvance'] = 0

	#for waste section
	globals()['wasteSpeedNumber'] = 400

	if k is not None:
		k.speedNumber(speedNumber)
		k.stitchNumber(stitchNumber)
		k.rollerAdvance(rollerAdvance)
		k.xferStitchNumber(xferStitchNumber)


def xferSettings(k, alterations={}):
	'''
	*TODO
	'''
	xSpeed = xferSpeedNumber
	xStitch = xferStitchNumber
	xRoll = xferRollerAdvance

	if 'speedNumber' in alterations: xSpeed = alterations['speedNumber']
	if 'stitchNumber' in alterations: xStitch = alterations['stitchNumber']
	if 'rollerAdvance' in alterations: xRoll = alterations['rollerAdvance']

	k.speedNumber(xSpeed)
	k.stitchNumber(xStitch)
	k.rollerAdvance(xRoll)


def splitSettings(k, alterations={}):
	'''
	*TODO
	'''
	splitSpeed = splitSpeedNumber
	splitStitch = splitStitchNumber
	splitRoll = splitRollerAdvance

	if 'speedNumber' in alterations: splitSpeed = alterations['speedNumber']
	if 'stitchNumber' in alterations: splitStitch = alterations['stitchNumber']
	if 'rollerAdvance' in alterations: splitRoll = alterations['rollerAdvance']

	k.speedNumber(splitSpeed)
	k.stitchNumber(splitStitch)
	k.rollerAdvance(splitRoll)


def resetSettings(k):
	'''
	*TODO
	'''
	k.speedNumber(speedNumber)
	k.stitchNumber(stitchNumber)
	k.rollerAdvance(rollerAdvance)


def convertGauge(gauge=2, leftN=None, rightN=None):
	'''
	*TODO
	'''
	newLeftN = leftN
	newRightN = rightN
	if gauge > 1:
		if leftN is not None: newLeftN = int(leftN*gauge)
		if rightN is not None: newRightN = int(rightN*gauge)

	if leftN is None: return newRightN
	elif rightN is None: return newLeftN
	else: return newLeftN, newRightN


def tempMissOut(k, width, direction, c=None, buffer=None):
	'''
	*TODO
	'''
	#if c is None, meant to just move carriage out of way, without carrier
	autobuffer = np.floor((252-width)/2)
	if buffer is not None and buffer > autobuffer:
		buffer = None
		warnings.warn(f'Passes buffer value is too large, using default buffer value {autobuffer} instead.')

	if direction == '-':
		if buffer is None: missN = 0 - np.floor((252-width)/2)
		else: missN = 0 - buffer

		if c is None: k.drop(f'f{missN}') #just move carriage out of way #TODO: add carriage move (no drop) to knitout-backend-kniterate
		else: k.miss('-', f'f{missN}', c) #move carrier out of way
	else:
		if buffer is None: missN = (width-1) + np.floor((252-width)/2)
		else: missN = (width-1) + buffer

		if c is None: k.drop(f'f{missN}') #just move carriage out of way
		else: k.miss('+', f'f{missN}', c) #move carrier out of way


def sortBedNeedles(bnList=[], direction='+'):
	'''
	*TODO
	'''
	sortedBnList = list(set(bnList.copy()))
	if direction == '-': sortedBnList.sort(key=lambda bn: int(bn[1:]), reverse=True)
	else: sortedBnList.sort(key=lambda bn: int(bn[1:]))
	return sortedBnList


def placeCarrier(k, leftN=None, rightN=None, carrierOpts=[], gauge=2, opDetails={}):
	'''
	*TODO
	'''
	placedCarrier = None #for now
	tuckDir = None
	tuckDrop = []

	lastOps = []

	carrierOpts = list(filter(None, carrierOpts))

	for c in carrierOpts:
		lastLineC = k.returnLastOp(carrier=c, asDict=True, **opDetails)
		if lastLineC is not None: lastOps.append(lastLineC)
		else: lastOps.append({'op': None, 'carrier': c})

	distances = {}
	needleNums = {}

	for ln in lastOps:
		c = ln['carrier']

		if type(c) == list:
			for carr in c:
				if carr in carrierOpts:
					c = carr
					break

		if ln['op'] == 'in' or ln['op'] == 'out' or ln['op'] is None: needleNum = 0 #just assume 0 is the min needle (#TODO: have option for detecting min needle) #if None, means carrier hasn't been used yet
		else: needleNum = ln['bn1']['needle']
		
		needleNums[c] = needleNum

		if leftN is not None: distances[abs(needleNum-leftN)] = {'carrier': c, 'sideN': leftN}
		if rightN is not None: distances[abs(needleNum-rightN)] = {'carrier': c, 'sideN': rightN}

	if len(distances):
		minDist = min(distances.keys())
		placedCarrier = distances[minDist]['carrier']
		needleNum = needleNums[placedCarrier]

		if (needleNum-(distances[minDist]['sideN'])) > 0: tuckDir = '-'
		else: tuckDir = '+'

		if minDist > 5: #need to tuck to get it in correct spot
			tuckB = 0 #for tucking every other
			tuckF = 0

			k.comment(f'tuck to move carrier {placedCarrier} from {needleNum} to {distances[minDist]["sideN"]}')

			k.rollerAdvance(0)

			if tuckDir == '+':
				for t in range(needleNums[placedCarrier]+1, distances[minDist]['sideN']):
					if t % gauge == 0:
						if tuckB % 2 == 0:
							k.tuck('+', f'b{t}', placedCarrier)
							tuckDrop.append(f'b{t}')
						tuckB += 1
					elif t % gauge != 0:
						if tuckF % 2 == 0:
							k.tuck('+', f'f{t}', placedCarrier)
							tuckDrop.append(f'f{t}')
						tuckF += 1
			else:
				for t in range(needleNums[placedCarrier]-1, distances[minDist]['sideN'], -1):
					if t % gauge == 0:
						if tuckB % 2 == 0:
							k.tuck('-', f'b{t}', placedCarrier)
							tuckDrop.append(f'b{t}')
						tuckB += 1
					elif t % gauge != 0:
						if tuckF % 2 == 0:
							k.tuck('-', f'f{t}', placedCarrier)
							tuckDrop.append(f'f{t}')
						tuckF += 1

			k.rollerAdvance(rollerAdvance)

	return tuckDrop, placedCarrier, tuckDir


flatten = lambda *n: list(e for a in n for e in (flatten(*a) if isinstance(a, (tuple, list,)) else (a,)))


def includeNSecureSides(n, secureNeedles={}, knitBed=None):
	'''
	*n is the number associated with the needle we're checking
	*secureNeedles is dict with needle numbers as key and bed as value (valid values are 'f', 'b', or 'both')
	*knitBed is the bed that is currently knitting, if applicable (because this is only checking if we can't xfer it, so if it was unable to be xferred from a certain bed, it should still be knitted on that bed); value of None indicates we are just check for xfer
	'''
	if n in secureNeedles:
		if knitBed is None: return False
		else: #for knitting
			if knitBed == secureNeedles[n]: return True
			else: return False
	else: return True


def convertToBN(needles, sort=True, gauge=2):
	'''
	for now, only works with: list (with potential sublists/sub-ranges), int, or str
	'''
	try:
		int(needles)
		return f'b{needles}' if (needles % gauge != 0) else f'f{needles}'
	except Exception:
		if type(needles) == str: return needles
		else: # list of lists of range
			needles = [convertToBN(n) for sublist in needles for n in ([sublist] if isinstance(sublist, (str, int, float)) else sublist)] #new # if type(needles[0]) == list or type(needles[0]) == range:
			# if isinstance(needles[0], (list, range, tuple)): needles = [convertToBN(n) for sublist in needles for n in list(sublist)] #new # if type(needles[0]) == list or type(needles[0]) == range:
			# else: needles = [convertToBN(n) for n in needles]
	# needles = flatten(needles) #new
	if sort: sortBedNeedles(needles)
	return needles #otherwise, just return original list

# e.g.: `convertToBN([1, 2, 'f2', range(0, 10)])`
#----------------------------------------------------
#--- STANDARD KNITTING FUNCTIONS /STITCH PATTERNS ---
#----------------------------------------------------

#--- KNITTING PASSES ---
def knitPass(k, startN, endN, c, bed='f', gauge=1, emptyNeedles=[]):
	'''
	*TODO
	'''
	if endN > startN: #pass is pos
		for n in range(startN, endN+1):
			if f'{bed}{n}' not in emptyNeedles:
				if (bed == 'f' and n % gauge == 0) or (bed == 'b' and (gauge == 1 or n % gauge != 0)): k.knit('+', f'{bed}{n}', c) 
				elif n == endN: k.miss('+', f'{bed}{n}', c)
			elif n == endN: k.miss('+', f'{bed}{n}', c)
	else: #pass is neg
		for n in range(startN, endN-1, -1):
			if f'{bed}{n}' not in emptyNeedles:
				if (bed == 'f' and n % gauge == 0) or (bed == 'b' and (gauge == 1 or n % gauge != 0)): k.knit('-', f'{bed}{n}', c)
				elif n == endN: k.miss('-', f'{bed}{n}', c)
			elif n == endN: k.miss('-', f'{bed}{n}', c)


def jersey(k, startN, endN, length, c, currentBed='f', gauge=1, emptyNeedles=[]):
	'''
	*TODO
	'''
	k.comment('begin jersey')
	for p in range(0, length):
		if p % 2 == 0:
			passStartN = startN
			passEndN = endN
		else:
			passStartN = endN
			passEndN = startN
		knitPass(k, startN=passStartN, endN=passEndN, c=c, bed=currentBed, gauge=gauge, emptyNeedles=emptyNeedles)
	k.comment('end jersey')


#--- FUNCTION FOR KNITTING ON ALT NEEDLES, PARITY SWITCHING FOR FRONT & BACK ---
def interlock(k, startN, endN, length, c, gauge=1, startCondition=1, emptyNeedles=[], currentBed=None, homeBed=None, secureStartN=False, secureEndN=False):
	'''
	Knits on every needle interlock starting on side indicated by which needle value is greater.
	In this function length is the number of total passes knit so if you want an interlock segment that is 20 courses long on each side set length to 40. Useful if you want to have odd amounts of interlock.

	*k is knitout Writer
	*startN is the starting needle to knit on
	*endN is the last needle to knit on (***note: no longer needs to be +1)
	*length is total passes knit
	*c is carrier
	*gauge is the... well, gauge
	*startCondition is *TODO
	*emptyNeedles is *TODO
	*currentBed is the bed(s) that current has knitting (valid values are: 'f' [front] and 'b' [back]); if value is None, will assume that the loops are already in position for interlock (e.g. not knitting circular half-gauge interlock)
	*homeBed is the bed to transfer the loops back to at the end (if applicable); NOTE: this should only be added if knitting if half gauge tube will stitch patterns inserted on one bed (since the function will act accordingly)
	*secureStartN and *secureEndN are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
	'''
	emptyNeedles = convertToBN(emptyNeedles) #new #* #check
		
	length *= 2
	length = int(length) #incase doing e.g. .5 length (only a pass)

	if endN > startN: #first pass is pos
		beg = 0
		leftN = startN
		rightN = endN
	else: #first pass is neg
		beg = 1
		length += 1
		leftN = endN
		rightN = startN
		if startCondition == 1: startCondition = 2 #switch since starting at 1
		else: startCondition = 1
	
	if homeBed is not None:
		if homeBed == 'f':
			homeCondition = lambda n: (n % gauge == 0)
			travelBed = 'b'
		else:
			homeCondition = lambda n: ((n-1) % gauge == 0)
			travelBed = 'f'
	

	def frontBed1(n, direction):
		if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'b': return False

		if f'f{n}' not in emptyNeedles and n % gauge == 0 and (((n//gauge) % 2) == 0):
			k.knit(direction, f'f{n}', c)
			return True
		else: return False
	
	
	def backBed1(n, direction):
		if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'f': return False

		if f'b{n}' not in emptyNeedles and (gauge == 1 or n % gauge != 0) and ((((n-1)//gauge) % 2) == 0):
			k.knit(direction, f'b{n}', c)
			return True
		else: return False
	
	def frontBed2(n, direction):
		if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'b': return False

		if f'f{n}' not in emptyNeedles and n % gauge == 0 and (((n//gauge) % 2) != 0):
			k.knit(direction, f'f{n}', c)
			return True
		else: return False
	

	def backBed2(n, direction):
		if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'f': return False

		if f'b{n}' not in emptyNeedles and (gauge == 1 or n % gauge != 0) and ((((n-1)//gauge) % 2) != 0):
			k.knit(direction, f'b{n}', c)
			return True
		else: return False


	if currentBed is not None: #currentBed indicates that we need to start by xferring to proper spots
		xferSettings(k)

		if currentBed == 'f':
			otherBed = 'b'
			currCondition = lambda n: (n % gauge == 0)
		else:
			otherBed = 'f'
			currCondition = lambda n: ((n-1) % gauge == 0)

		for n in range(leftN, rightN+1):
			if (n == startN and secureStartN) or (n == endN and secureEndN): continue

			if currCondition(n) and f'{currentBed}{n}' not in emptyNeedles and (((n//gauge) % (2*gauge)) % gauge) != 0: k.xfer(f'{currentBed}{n}', f'{otherBed}{n}') #check (especially check if works for gauge 1)
		resetSettings(k)

	#for if home bed
	def homeBed1(n, direction):
		if homeCondition(n) and f'{homeBed}{n}' not in emptyNeedles and ((n//gauge) % (2*gauge) == 0):
			k.knit(direction, f'{homeBed}{n}', c)
			return True
		else: return False
	

	def travelBed1(n, direction):
		if (n == startN and secureStartN) or (n == endN and secureEndN):
			if homeCondition(n):
				k.knit(direction, f'{homeBed}{n}', c)
				return True
			else: return False

		if homeCondition(n) and f'{travelBed}{n}' not in emptyNeedles and ((n//gauge) % (2*gauge) == (gauge+1)): #check for gauge 1
			k.knit(direction, f'{travelBed}{n}', c)
			return True
		else: return False
	

	def homeBed2(n, direction):
		if homeCondition(n) and f'{homeBed}{n}' not in emptyNeedles and ((n//gauge) % (2*gauge) == gauge):
			k.knit(direction, f'{homeBed}{n}', c)
			return True
		else: return False
	

	def travelBed2(n, direction):
		if (n == startN and secureStartN) or (n == endN and secureEndN):
			if homeCondition(n):
				k.knit(direction, f'{homeBed}{n}', c)
				return True
			else: return False

		if homeCondition(n) and f'{travelBed}{n}' not in emptyNeedles and ((n//gauge) % (2*gauge) == (gauge-1)): #check for gauge 1
			k.knit(direction, f'{travelBed}{n}', c)
			return True
		else: return False


	#--- the knitting ---
	for h in range(beg, length):
		if h % 2 == 0:
			for n in range(leftN, rightN+1):
				if startCondition == 1: #first pass of interlock will knit on 0, 1, 4, 5, etc.
					if homeBed is None:
						if frontBed1(n, '+'): continue
						elif backBed1(n, '+'): continue
						elif n == rightN: k.miss('+', f'f{n}', c)
					else:
						if homeBed1(n, '+'): continue
						elif travelBed1(n, '+'): continue
						elif n == rightN: k.miss('+', f'f{n}', c)
				else: #first pass of interlock will knit on 2, 3, 6, 7, etc.
					if homeBed is None:
						if frontBed2(n, '+'): continue
						elif backBed2(n, '+'): continue
						elif n == rightN: k.miss('+', f'f{n}', c)
					else:
						if homeBed2(n, '+'): continue
						elif travelBed2(n, '+'): continue
						elif n == rightN: k.miss('+', f'f{n}', c)
		else:
			for n in range(rightN, leftN-1, -1):
				if startCondition == 2:
					if homeBed is None:
						if frontBed1(n, '-'): continue
						elif backBed1(n, '-'): continue
						elif n == leftN: k.miss('-', f'f{n}', c)
					else:
						if homeBed1(n, '-'): continue
						elif travelBed1(n, '-'): continue
						elif n == leftN: k.miss('-', f'f{n}', c)
				else:
					if homeBed is None:
						if frontBed2(n, '-'): continue
						elif backBed2(n, '-'): continue
						elif n == leftN: k.miss('-', f'f{n}', c)
					else:
						if homeBed2(n, '-'): continue
						elif travelBed2(n, '-'): continue
						elif n == leftN: k.miss('-', f'f{n}', c)
	
	if homeBed is not None:
		xferSettings(k)
		for n in range(leftN, rightN+1):
			if (n == startN and secureStartN) or (n == endN and secureEndN): continue

			if currCondition(n) and f'{homeBed}{n}' not in emptyNeedles and (((n//gauge) % (2*gauge)) % gauge) != 0: k.xfer(f'{travelBed}{n}', f'{homeBed}{n}') #check (especially check if works for gauge 1)
		resetSettings(k)


#--- FUNCTION FOR DOING THE MAIN KNITTING OF CIRCULAR, OPEN TUBES ---
def circular(k, startN, endN, length, c, gauge=1):
	'''
	Knits on every needle circular tube starting on side indicated by which needle value is greater.
	In this function length is the number of total passes knit so if you want a tube that
	is 20 courses long on each side set length to 40.

	*k is knitout Writer
	*startN is the starting needle to knit on
	*endN is the last needle to knit on
	*length is total passes knit
	*c is carrier
	*gauge is... gauge
	'''

	if endN > startN: #first pass is pos
		beg = 0
		leftN = startN
		rightN = endN
	else: #first pass is neg
		beg = 1
		length += 1
		leftN = endN
		rightN = startN

	for h in range(beg, length):
		if h % 2 == 0:
			for n in range(leftN, rightN+1):
				if n % gauge == 0: k.knit('+', f'f{n}', c)
				elif n == rightN: k.miss('+', f'f{n}', c)
		else:
			for n in range(rightN, leftN-1, -1):
				if gauge == 1 or n % gauge != 0: k.knit('-', f'b{n}', c)
				elif n == leftN: k.miss('-', f'b{n}', c)


def garter(k, startN, endN, length, c, patternRows=1, startBed='f', currentBed=None, originBed=None, homeBed=None, secureStartN=True, secureEndN=True, gauge=1):  #TODO: add seed!
	'''
	*k is knitout Writer
	*startN is the starting needle to knit on
	*endN is the last needle to knit on
	*length is total passes knit
	*c is carrier
	*patternRows is the number of knit/purl rows to knit before switch to the other (e.g. 2 -- knit 2 rows, purl 2 rows [repeat])
	*startBed is the bed to start on
	*currentBed is the bed(s) that current has knitting (valid values are: 'f' [front], 'b' [back], and 'both'); assumes you start on the front bed, unless otherwise indicated
	*originBed is the bed that the section belongs to
	*homeBed is the bed to transfer the loops back to at the end (if applicable)
	*secureStartN and *secureEndN are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
	*gauge is... gauge
	'''

	if currentBed is None: currentBed = startBed
	if originBed is None: originBed = currentBed

	k.comment('begin garter')

	if endN > startN: #first pass is pos
		dir1 = '+'
		dir2 = '-'
		otherEndN = endN-1 #for gauge 2
		otherStartN = startN+1
		tuckEndShift = 1
		tuckStartShift = -1
		range1 = range(startN, endN+1)
		range2 = range(endN, startN-1, -1)
	else: #first pass is neg
		dir1 = '-'
		dir2 = '+'
		otherEndN = endN+1 #for gauge 2
		otherStartN = startN-1
		tuckEndShift = -1
		tuckStartShift = 1
		range1 = range(startN, endN-1, -1)
		range2 = range(endN, startN+1)
	
	secureNeedles = {}
	if originBed == 'f': otherBed = 'b'
	else: otherBed = 'f'

	if (startN % 2 == 0 and originBed == 'f') or ((startN+1) % 2 == 0 and originBed == 'b'):
		secureNeedles[startN] = originBed
		secureNeedles[otherStartN] = otherBed
	else:
		secureNeedles[startN] = otherBed
		secureNeedles[otherStartN] = originBed
	
	if (endN % 2 == 0 and originBed == 'f') or ((endN+1) % 2 == 0 and originBed == 'b'):
		secureNeedles[endN] = originBed
		secureNeedles[otherEndN] = otherBed
	else:
		secureNeedles[endN] = otherBed
		secureNeedles[otherEndN] = originBed
	
	if homeBed == 'b' or (homeBed is None and originBed == 'b'):
		condition = lambda n: (n % gauge != 0 or gauge == 1)
	else:
		condition = lambda n: n % gauge == 0
	
	if startBed == 'b':
		bed1 = 'b'
		bed2 = 'f'

		if currentBed != 'b':
			if currentBed == 'both' and gauge > 1:
				shift = 1
				k.rack(1)
				# k.rack(-1)
			else: shift = 0

			xferSettings(k)

			for n in range1:
				if condition(n) and includeNSecureSides(n, secureNeedles=secureNeedles): k.xfer(f'f{n+shift}', f'b{n}')
				elif currentBed == 'both' and condition(n): k.xfer(f'f{n+shift}', f'b{n}') #xfer it anyway if current bed is both

			if currentBed == 'both' and gauge > 1: k.rack(0)

			resetSettings(k)
			currentBed = 'b'
	else: #knit garter on front or both
		bed1 = 'f'
		bed2 = 'b'

		if currentBed != 'f': #both
			if currentBed == 'both' and gauge > 1:
				shift = -1
				k.rack(1)
			else: shift = 0

			xferSettings(k)
			for n in range1:
				if condition(n) and includeNSecureSides(n, secureNeedles=secureNeedles): k.xfer(f'b{n+shift}', f'f{n}')
				elif currentBed == 'both' and condition(n): k.xfer(f'b{n+shift}', f'f{n}') #xfer it anyway if current bed is both

			if currentBed == 'both' and gauge > 1: k.rack(0)

			resetSettings(k)
		currentBed = 'f'

	direction = dir1
	needleRange = range1

	passCt = 0
	for l in range(0, length):
		for r in range(0, patternRows):
			for n in needleRange: #TODO: maybe just do dir1 instead of direction ?
				if condition(n):
					if includeNSecureSides(n, secureNeedles=secureNeedles, knitBed=bed1): k.knit(direction, f'{bed1}{n}', c)
					else: k.knit(direction, f'{bed2}{n}', c)
				elif n == endN: k.miss(direction, f'{bed1}{n}', c)

			if direction == dir1: direction = dir2
			else: direction = dir1 #remove #?
			if needleRange == range1: needleRange = range2 #TODO: maybe just make it needleRange = range2 since it will always be that?
			else: needleRange = range1 #remove #?

			passCt += 1
			if passCt == length: break

		if passCt == length and ((homeBed is None) or (currentBed == homeBed)): break

		xferSettings(k)
			
		for n in range1:
			if condition(n) and includeNSecureSides(n, secureNeedles=secureNeedles): k.xfer(f'{bed1}{n}', f'{bed2}{n}')

		currentBed = bed2
		resetSettings(k)

		if passCt == length: break

		for r in range(0, patternRows):
			for n in needleRange:
				if condition(n):
					if includeNSecureSides(n, secureNeedles=secureNeedles, knitBed=bed2): k.knit(direction, f'{bed2}{n}', c)
					else: k.knit(direction, f'{bed1}{n}', c)
				elif n == startN: k.miss(direction, f'{bed2}{n}', c)

			if direction == dir1: direction = dir2 #remove #?
			else: direction = dir1
			if needleRange == range1: needleRange = range2 #remove #? #^
			else: needleRange = range1 #TODO: maybe just make it needleRange = range1 since it will always be that?

			passCt += 1
			if passCt == length: break
		
		if passCt == length and ((homeBed is None) or (currentBed == homeBed)): break

		xferSettings(k)

		for n in range2:
			if condition(n) and includeNSecureSides(n, secureNeedles=secureNeedles): k.xfer(f'{bed2}{n}', f'{bed1}{n}')

		currentBed = bed1

		resetSettings(k)

		if passCt == length: break

	k.comment('end garter')

	nextDirection = direction
	if nextDirection == '+': nextSide = 'l'
	else: nextSide = 'r'

	return nextSide #so know where carrier is at (note: will be *next* side)


def lace(k, startN, endN, length, c, patBeg=0, patternRows=2, spaceBtwHoles=1, offset=1, offsetStart=0, offsetReset=None, currentBed='f', gauge='1', secureStartN=True, secureEndN=True): #TODO: ensure it works well for gauge 2
	'''
	*k is the knitout Writer
	*startN is the first needle to knit on in first pass
	*endN is the last needle to knit on in first pass
	*length is the total number of rows
	*c is the carrier
	*patBeg is the pass number to start at (useful for if using this function in cactus and need to prevent reseting xfer pattern)
	*patternRows is the number of rows between xfers to form new holes
	*spaceBtwHoles is the number of needles that are skipped btw xfers to form the lace holes
	*offset is the shift in lace hole placement for alternating rows (e.g. offset=0 would stack lace holes directly ontop of one another [NOTE: requires patternRows to have minimum value of 2], offset=1 would be checkerboard pattern, etc.)
	*offsetStart is *TODO
	*offsetReset is the number of rows after which the offset is set back to the beginning (if None, will just reset once offset automatically resets)
	*currentBed is the needle bed where the main knitting will occur (other bed wil be used for xfers)
	*gauge is gauge
	*secureStartN and *secureEndN are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
	'''

	if patBeg == 1 and length == 1: length += 1

	if patternRows < 2:
		patternRows = 2
		print('\nwarning: changing patternRows to 2 so lace holes can properly form.')

	if currentBed == 'f':
		rack1 = -gauge
		rack2 = gauge
		bed2 = 'b'
	else:
		rack1 = gauge
		rack2 = -gauge
		bed2 = 'f'

	if endN > startN: #first pass is pos
		dir1 = '+'
		dir2 = '-'
		leftN = startN
		rightN = endN
		ranges = {dir1: range(startN, endN+1), dir2: range(endN, startN-1, -1)}
	else: #first pass is neg
		dir1 = '-'
		dir2 = '+'
		leftN = endN
		rightN = startN
		ranges = {dir1: range(startN, endN-1, -1), dir2: range(endN, startN+1)}
	
	laceStitch = stitchNumber+3
	if laceStitch > 9: laceStitch = 9
	k.comment('begin lace')
	
	xferPasses = 0
	mod = offsetStart

	for p in range(patBeg, length):
		if (p-patBeg) % 2 == 0:
			direction = dir1
			lastN = endN
		else:
			direction = dir2
			lastN = startN

		if p % patternRows == 0:
			k.stitchNumber(stitchNumber)
			if gauge == 1:
				if xferPasses % 2 == 0: rack = rack1
				else: rack = rack2
				shift = rack
			else:
				rack = rack1
				shift = -gauge

			xferPasses += 1

			for n in ranges[dir1]:
				if (n+shift >= leftN and n+shift <= rightN) and ((n - startN) % (gauge*(spaceBtwHoles+1)) == (gauge*mod)) and (not secureStartN or n != startN) and (not secureEndN or n != endN): #don't xfer edge-most stitches so don't have to worry about them dropping
					if gauge == 1 or ((currentBed == 'f' and n % gauge == 0) or (currentBed == 'b' and (n-1) % gauge == 0)): k.xfer(f'{currentBed}{n}', f'{bed2}{n}')
			
			k.rack(rack)
			for n in ranges[dir1]:
				if (n+shift >= leftN and n+shift <= rightN) and ((n-startN) % (gauge*(spaceBtwHoles+1)) == (gauge*mod)) and (not secureStartN or n != startN) and (not secureEndN or n != endN):
					if gauge == 1 or ((currentBed == 'f' and n % gauge == 0) or (currentBed == 'b' and (n-1) % gauge == 0)): k.xfer(f'{bed2}{n}', f'{currentBed}{n+shift}')
			
			k.rack(0)
			
			mod += offset
			if mod > spaceBtwHoles or (offsetReset is not None and xferPasses % offsetReset == 0): mod = 0
			
		k.stitchNumber(laceStitch)
		for n in ranges[direction]:
			if gauge == 1 or ((currentBed == 'f' and n % gauge == 0) or (currentBed == 'b' and (n+1) % gauge == 0)): k.knit(direction, f'{currentBed}{n}', c)
			elif n == lastN: k.miss(direction, f'f{n}', c)
		
		k.stitchNumber(stitchNumber)
	k.comment('end lace')


def rib(k, startN, endN, length, c, currentBed='f', originBed=None, homeBed=None, secureStartN=True, secureEndN=True, sequence='fb', gauge=1):
	'''
	*k is the knitout Writer
	*endN is the last needle
	*startN is the first needle
	*currentBed is the bed(s) that current has knitting (valid values are: 'f' [front], 'b' [back], and 'both'); if value is None, will assume that the loops are already in position for rib
	*originBed is the bed that the section belongs to
	*homeBed is the bed to transfer the loops back to at the end (if applicable); NOTE: this should only be added if knitting if half gauge tube will stitch patterns inserted on one bed (since the function will act accordingly)
	*secureStartN and *secureEndN are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
	*sequence is the repeating rib pattern (e.g. 'fb' of 'bf' for 1x1 [first bed indicates which bed left-most needle will be on], 'ffbb' for 2x2, 'fbffbb' for 1x1x2x2, etc.)
	*gauge is gauge
	'''
	k.comment(f'begin rib ({sequence})')
	if originBed is None: originBed = currentBed

	if gauge > 1:
		gaugedSequence = ''
		for char in sequence:
			gaugedSequence += char * gauge
		sequence = gaugedSequence
	

	def bedConditions(n):
		if originBed == 'f':
			if n % gauge == 0: return True
			else: return False
		else:
			if (n+1) % gauge == 0: return True
			else: return False


	if endN > startN: #first pass is pos
		dir1 = '+'
		dir2 = '-'
		otherEndN = endN-1 #for gauge 2
		otherStartN = startN+1
		ranges = {dir1: range(startN, endN+1), dir2: range(endN, startN-1, -1)}
	else: #first pass is neg
		dir1 = '-'
		dir2 = '+'
		otherEndN = endN+1 #for gauge 2
		otherStartN = startN-1
		ranges = {dir1: range(startN, endN-1, -1), dir2: range(endN, startN+1)}

	secureNeedles = {}
	if originBed == 'f': otherBed = 'b'
	else: otherBed = 'f'

	if (startN % 2 == 0 and originBed == 'f') or ((startN+1) % 2 == 0 and originBed == 'b'):
		secureNeedles[startN] = originBed
		secureNeedles[otherStartN] = otherBed
	else:
		secureNeedles[startN] = otherBed
		secureNeedles[otherStartN] = originBed
	
	if (endN % 2 == 0 and originBed == 'f') or ((endN+1) % 2 == 0 and originBed == 'b'):
		secureNeedles[endN] = originBed
		secureNeedles[otherEndN] = otherBed
	else:
		secureNeedles[endN] = otherBed
		secureNeedles[otherEndN] = originBed

	if currentBed is not None: #currentBed indicates that we need to start by xferring to proper spots
		xferSettings(k)

		if currentBed == 'both': #can't be applicable if homeBed is not None
			for n in ranges[dir1]: #TODO: adjust for gauge
				if bedConditions(n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{currentBed}{n}', f'{otherBed}{n}')
		else:
			for n in ranges[dir1]: #TODO: adjust for gauge
				if includeNSecureSides(n, secureNeedles=secureNeedles):
					if bedConditions(n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{currentBed}{n}', f'{otherBed}{n}')
			
		resetSettings(k)

	#TODO: maybe change stitch size for rib? k.stitchNumber(math.ceil(stitchNumber/2)) (if so -- remember to reset settings)
	for p in range(0, length):
		if p % 2 == 0:
			direction = dir1
			lastN = endN
		else:
			direction = dir2
			lastN = startN

		for n in ranges[direction]:
			if sequence[n % len(sequence)] == 'f':
				if bedConditions(n):
					if includeNSecureSides(n, secureNeedles=secureNeedles, knitBed='f'): k.knit(direction, f'f{n}', c) #xferred it or originBed == 'f', ok to knit
					else: k.knit(direction, f'b{n}', c) #if didn't xfer this, knit on the bed it started on
				elif n == lastN: k.miss(direction, f'f{n}', c)
			else: #sequence == 'b'
				if bedConditions(n):
					if includeNSecureSides(n, secureNeedles=secureNeedles, knitBed='b'): k.knit(direction, f'b{n}', c) #xferred it or originBed == 'b', ok to knit
					else: k.knit(direction, f'f{n}', c) #if didn't xfer this, knit on the bed it started on
				elif n == lastN: k.miss(direction, f'b{n}', c)
	
	if homeBed is not None:
		if homeBed == 'f': otherBed = 'b'
		else: otherBed = 'f'
		xferSettings(k)
		for n in ranges[dir1]: #TODO: adjust for gauge
			if includeNSecureSides(n, secureNeedles=secureNeedles):
					if bedConditions(n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{otherBed}{n}', f'{homeBed}{n}')
		resetSettings(k)
	k.comment('end rib')


def stitchPatternTube(k, leftN, rightN, c, wasteC='1', drawC='2', featureCs=[], side='l', patterns=[], defaultLength=None, wasteDivider=False, wasteLength=42):
	'''
	Knits a half-gauge tube in the stitch pattern[s] indicated in the `patterns` arg.
	
	Parameters:
	----------
	 * k (import): the knitout Writer.
	 * leftN (int): the left-most needle to knit on.
	 * rightN (int): the right-most needle to knit on.
	 * c (str): the carrier to knit with.
	 * wasteC (str, optional): the carrier to use for the waste section. If None, won't add any waste sections. Defaults to '1'.
	 * drawC (str, optional): the carrier to use for the draw thread. Defaults to '2'.
	 * featureCs (list, optional): any carriers that might be used for special features (for now, the only use case would be if plaiting were to occur). Defaults to [].
	 * side (str, optional): the side the start on (valid values are 'l' [left] and 'r' [right]). Defaults to 'l'.
	 * patterns (list): indicates which stitch patterns to make tubes for; a list containing sub-list(s) containing 1-2 items.
		 * e.g.: `[['rib', {'sequence': 'fb'}], ['jersey'], ['garter', {'patternRows': 2}]]`
		 * sublist[0] is a string specifying which stitch pattern to use (should match the function name for that specific pattern [which should, in turn, simply be the pattern name])
			 * note that 'jersey' is fine for circular (either will work).
		 * sublist[1] (optional) is a dict with args specific to the given pattern's function.
			 * The key should be the parameter name (as a string) and the value should be the specification you're passing for it. These are the parameters that you might include for certain patterns:
				 * garter: 'patternRows'
				 * lace: 'patternRows'
				 * rib: 'sequence'
				 * **for ANY pattern, can also include the following information:
				 	 * 'extensions' which is a dict that can contain the following knitout extensions as keys and their assigned as the dict value. E.g.:
						* extensions: { 'stitchNumber': 5, 'rollerAdvance': 300, 'speedNumber': 400 }
					 * 'length' which is the number of passes on either bed (will override the defaultLength)
					 * 'plaiting' which indicates plaiting will be used for the stitch pattern (in which case, the additional plaiting carrier should be included in featureCs, and front/back bed will knit in intervals of 3 passes each, with plaiting occurring for first two passes and normal for last [so that plaiting carrier can consistently live on the same side, since knitting circularly])
	 * defaultLength (int, optional): the number of passes on either bed that will automatically be used if no 'length' is specified in a pattern's dict. Defaults to None.
	 * wasteDivider (bool, optional): indicates whether or not the stitch pattern tubes should be separated by waste sections with a draw thread in the middle. Defaults to False.  
	 * wasteLength (int, optional): the total length of any waste sections.
	'''

	defaultExtensions = {'speed': speedNumber, 'stitch': stitchNumber, 'roller': rollerAdvance, 'xferSpeed': xferSpeedNumber, 'xferStitch': xferStitchNumber, 'xferRoller': xferRollerAdvance, 'splitSpeed': splitSpeedNumber, 'splitStitch': splitStitchNumber, 'splitRoller': splitRollerAdvance, 'wasteSpeed': wasteSpeedNumber, 'wasteStitch': wasteStitchNumber} #in case changed

	if wasteC is None: wasteDivider = False #just in case the user made a mistake

	gauge = 2

	otherCs = featureCs.copy()
	if c != drawC and c != wasteC: otherCs.append(c)
	
	plaitCs = featureCs.copy()
	if len(featureCs):
		if drawC in otherCs: otherCs.remove(drawC)
		if wasteC in otherCs: otherCs.remove(wasteC)
		if len(plaitCs) > 1: endOnRight = [plaitCs[1]]
		else: endOnRight = [] #just plaiting on the front
	else: endOnRight = []
	
	for idx, pat in enumerate(patterns):
		passCt = 80 #if nothing specified

		if defaultLength is not None: passCt = defaultLength*2

		frontPlaitC = c
		backPlaitC = c

		missDrawC = True
		missWasteC = True

		if type(pat) == str:
			pattern = pat
			patFuncArgs = {}
			info = {}
		else:
			pattern = pat[0]
			info = pat[1].copy()
			patFuncArgs = pat[1]
			if 'length' in patFuncArgs:
				passCt = patFuncArgs['length']*2
				del patFuncArgs['length'] #so don't use it in get_parameters
			if 'plaiting' in patFuncArgs:
				if drawC in plaitCs: missDrawC = False
				if wasteC in plaitCs: missWasteC = False

				if len(plaitCs) > 1:
					frontPlaitC = [c, plaitCs[0]]
					backPlaitC = [c, plaitCs[1]]
				else: frontPlaitC = [c, plaitCs[0]] #only plaiting on front bed
				del patFuncArgs['plaiting'] #so don't use it in get_parameters
			if 'extensions' in patFuncArgs: del patFuncArgs['extensions'] #so don't use it in get_parameters
			# if 'stitchNumber' in patFuncArgs:
			# 	del patFuncArgs['stitchNumber'] #so don't use it in get_parameters
			# if 'rollerAdvance' in patFuncArgs:
			# 	del patFuncArgs['rollerAdvance'] #so don't use it in get_parameters
			# if 'speedNumber' in patFuncArgs:
			# 	del patFuncArgs['speedNumber'] #so don't use it in get_parameters
		
		if wasteDivider and idx != 0:
			wasteSection(k, leftN=leftN, rightN=rightN, wasteC=wasteC, drawC=drawC, otherCs=otherCs, gauge=2, endOnRight=endOnRight, initial=False, drawMiddle=wasteDivider, interlockLength=wasteLength) #TODO: give option of passing interlockLength

			if c != drawC and missDrawC:
				if drawC in endOnRight: k.miss('+', f'f{rightN+3}', drawC)
				else: k.miss('-', f'f{leftN-3}', drawC)
			if c != wasteC and missWasteC: 
				if wasteC in endOnRight: k.miss('+', f'f{rightN+3}', wasteC)
				else: k.miss('-', f'f{leftN-3}', wasteC)
		elif idx == 0 and wasteC is not None:
			wasteSection(k, leftN=leftN, rightN=rightN, closedCaston=False, wasteC=wasteC, drawC=drawC, otherCs=otherCs, gauge=2, endOnRight=endOnRight, initial=True, drawMiddle=wasteDivider) #open caston to start (for now)

			if c != drawC and missDrawC:
				if drawC in endOnRight: k.miss('+', f'f{rightN+3}', drawC)
				else: k.miss('-', f'f{leftN-3}', drawC)
			if c != wasteC and missWasteC: 
				if wasteC in endOnRight: k.miss('+', f'f{rightN+3}', wasteC)
				else: k.miss('-', f'f{leftN-3}', wasteC)
			
			if not wasteDivider: #add open tube caston if no wasteDivider
				if c in endOnRight: castonStartN, castonEndN = rightN, leftN
				else: castonStartN, castonEndN = leftN, rightN
				openTubeCaston(k, startN=castonStartN, endN=castonEndN, c=c, gauge=2)
		# else: #just a draw thread #TODO: add back as option?
			# drawThread(k, leftN, rightN, drawC, side=drawSide, circular=True, missDraw=((rightN+3) if drawSide == 'r' else (leftN-3)), gauge=2)

		tubeSpeed, tubeStitch, tubeRoller = None, None, None
		if 'extensions' in info:
			if 'speedNumber' in info['extensions']: tubeSpeed = info['extensions']['speedNumber']
			if 'stitchNumber' in info['extensions']: tubeStitch = info['extensions']['stitchNumber']
			if 'rollerAdvance' in info['extensions']: tubeRoller = info['extensions']['rollerAdvance']
			
			setSettings(k=k, speed=tubeSpeed, stitch=tubeStitch, roller=tubeRoller)

		if len(info): details = ' ' + str(info)
		else: details = ''
		k.comment(f'stitch pattern tube: {pattern}{details} for {passCt//2} rows')

		if pattern == 'jersey' or pattern == 'circular':
			if side == 'l':
				startN = leftN
				endN = rightN
				beg = 0
			else:
				startN = rightN
				endN = leftN
				beg = 3
				passCt += 3
			
			if type(frontPlaitC) == list: #means there's some plaiting happening
				plaitPasses = beg
				for r in range(beg, passCt):
					if plaitPasses < 3:
						if plaitPasses == 0:
							knitPass(k, startN=leftN, endN=rightN, c=frontPlaitC, bed='f', gauge=2)
							if (rightN+1) % gauge == 0: k.tuck('-', f'b{rightN}', c) #prevent holes
							else: k.tuck('-', f'b{rightN-1}', c)
							k.miss('+', f'f{rightN}', c)
						elif plaitPasses == 1:
							knitPass(k, startN=rightN, endN=leftN, c=frontPlaitC, bed='f', gauge=2)
							if (leftN+1) % gauge == 0: k.tuck('+', f'b{leftN}', c)
							else: k.tuck('+', f'b{leftN+1}', c)
							k.miss('-', f'f{leftN}', c)
						else: knitPass(k, startN=leftN, endN=rightN, c=c, bed='f', gauge=2)
						plaitPasses += 1
					else:
						if plaitPasses == 3:
							knitPass(k, startN=rightN, endN=leftN, c=backPlaitC, bed='b', gauge=2)
							if leftN % gauge == 0: k.tuck('+', f'f{leftN}', c)
							else: k.tuck('+', f'f{leftN+1}', c)
							k.miss('-', f'b{leftN}', c)
						elif plaitPasses == 4:
							knitPass(k, startN=leftN, endN=rightN, c=backPlaitC, bed='b', gauge=2)
							if rightN % gauge == 0: k.tuck('-', f'f{rightN}', c) #prevent holes
							else: k.tuck('-', f'f{rightN-1}', c)
							k.miss('+', f'b{rightN}', c)
						else: knitPass(k, startN=rightN, endN=leftN, c=c, bed='b', gauge=2)
						plaitPasses += 1

					if plaitPasses > 5: plaitPasses = 0
			else:
				circular(k, startN=startN, endN=endN, length=passCt, c=c, gauge=2)
		else:
			stitchPatFunc = globals()[pattern]


			def get_parameters(func):
				toSet = ['startBed', 'currentBed', 'originBed', 'homeBed', 'patternRows', 'patBeg', 'startCondition']
				keep = ['gauge', 'secureStartN', 'secureEndN', 'offsetStart', 'sequence', 'startN', 'endN']

				keys = func.__code__.co_varnames[:func.__code__.co_argcount][::-1]
				sorter = {j: i for i, j in enumerate(keys[::-1])}

				if func.__defaults__ is not None:
					values = func.__defaults__[::-1]
					kwargs = {i: j for i, j in zip(keys, values)}
				else: kwargs = None
				
				sorted_args = {i: 'undefined' for i in sorted(keys, key=sorter.get) if i in toSet or i in patFuncArgs or i in keep}

				if kwargs is not None:
					for i in sorted_args:
						if i in kwargs: sorted_args[i] = kwargs[i]

				if 'gauge' in sorted_args: sorted_args['gauge'] = 2 #change the default to half gauge since need that for a tube with stitch pattern
				if 'secureStartN' in sorted_args: sorted_args['secureStartN'] = True
				if 'secureEndN' in sorted_args: sorted_args['secureEndN'] = True
				
				if len(patFuncArgs):
					for i in sorted_args:
						if i in patFuncArgs: sorted_args[i] = patFuncArgs[i]
				
				return sorted_args
			#--- end get_parameters func ---#^


			args = get_parameters(stitchPatFunc)

			argsF = args.copy()
			argsB = args.copy()

			argsF['startN'], argsF['endN'] = leftN, rightN
			argsB['startN'], argsB['endN'] = rightN, leftN

			if 'patternRows' in args: patternRows = args['patternRows']
			else: patternRows = None

			if 'startCondition' in args:
				startCondition = args['startCondition']
				startConF = startCondition
				startConB = startCondition
			else: startCondition = None

			if pattern == 'rib' and args['secureStartN'] is True:
				switchBeds = str.maketrans('fb', 'bf')
				seq = args['sequence']

				if seq[leftN % len(seq)] == 'f': argsF['sequence'] = seq.translate(switchBeds) #switch beds since secureStartN means it will stay on the bed
				if seq[rightN % len(seq)] == 'b': argsB['sequence'] = seq.translate(switchBeds)

			def setValues(argBed, args_vals={}):
				for key in args_vals:
					if key in argBed: argBed[key] = args_vals[key]

			if side == 'l':
				beg = 0
			else:
				beg = 1
				passCt += 1
			
			patRowsF = 0
			patRowsB = 0

			patBegF = 0
			patBegB = 0
			offsetStart = 0
			startBedF = 'b'
			startBedB = 'f'
			
			for r in range(beg, passCt):
				if r % 2 == 0: #pos front bed
					currentBed = 'f'
					currArgs = argsF

					if patternRows is not None:
						offsetStart = patBegF #whatever the previous patBeg was
						patBegF = patRowsF % patternRows

						if patRowsF % patternRows == 0:
							if startBedF == 'b': startBedF = 'f'
							else: startBedF = 'b'
						patRowsF += 1
					if startCondition is not None:
						if startConF == 1: startConF = 2
						else: startConF = 1
						args['startCondition'] = startConF

					setValues(argsF, {'startBed': startBedF, 'currentBed': currentBed, 'originBed': currentBed, 'homeBed': currentBed, 'patBeg': patBegF, 'offsetStart': offsetStart})
				else: #neg back bed
					currentBed = 'b'
					currArgs = argsB

					if patternRows is not None:
						offsetStart = patBegB #whatever the previous patBeg was
						patBegB = patRowsB % patternRows

						if patRowsB % patternRows == 0:
							if startBedB == 'b': startBedB = 'f'
							else: startBedB = 'b'
						patRowsB += 1
					if startCondition is not None:
						if startConB == 1: startConB = 2
						else: startConB = 1
						args['startCondition'] = startConB
					
					setValues(argsB, {'startBed': startBedB, 'currentBed': currentBed, 'originBed': currentBed, 'homeBed': currentBed, 'patBeg': patBegB, 'offsetStart': offsetStart})

				k.comment(f'insert stitch pattern for bed {currentBed}')
				
				stitchPatFunc(k, length=(0.5 if pattern == 'interlock' else 1), c=c, **currArgs)
			
		# if 'extensions' in info: defaultSettings(k) #reset to defaults
		if 'extensions' in info:
			setSettings(k=k, speed=defaultExtensions['speed'], stitch=defaultExtensions['stitch'], roller=defaultExtensions['roller'], xferSpeed=defaultExtensions['xferSpeed'], xferStitch=defaultExtensions['xferStitch'], xferRoller=defaultExtensions['xferRoller'], splitSpeed=defaultExtensions['splitSpeed'], splitStitch=defaultExtensions['splitStitch'], splitRoller=defaultExtensions['splitRoller'], wasteSpeed=defaultExtensions['wasteSpeed'], wasteStitch=defaultExtensions['wasteStitch'])


	print('\nDone.')


# -------------------
# colorwork functions

def insert_item(dic, item={}, pos=None):
	'''
	Insert a key, value pair into an ordered dictionary.
	Insert before the specified position.
	'''
	# from collections import OrderedDict
	# d = OrderedDict(dic)
	
	# insert anywhere if argument pos not given:
	if not pos or not len(dic):
		dic.update(item)
		return dic
	
	if not callable(pos): pos = lambda x: x == pos #change to lambda function so standardized
	d = dict()
	inserted = False
	
	item_k, item_v = list(item.items())[0]
	for key, val in dic.items():
		# insert key at stated position:
		# if not inserted and key > n: #insert here
		if not inserted and pos(key): #insert here
			d[item_k] = item_v
		
		d[key] = val
		
	return d

def colorworkTuck(n, direction, bed, tuckedNs, repRange):
	if bed == 'f': eligible = lambda x: x % 2 == 0
	else: eligible = lambda x: x % 2 != 0

	if all(tuckedNs.values()): #they've all been tucked on
		tuckedNs = dict(map(lambda x: (x[0], 0), tuckedNs.items()))

	if n in tuckedNs:
		if tuckedNs[n] > 0: #already been tucked on
			# if direction == '+': repTucks = {key:val for (key,val) in tuckedNs.items() if key >= n and (key-n) <= repRange and eligible(key)} #find the needle within repRange that has been tucked on least thus far
			if direction == '+': repTucks = {key:val for (key,val) in tuckedNs.items() if key in repRange and eligible(key)} #find the needle within repRange that has been tucked on least thus far
			else: repTucks = {key:val for (key,val) in tuckedNs.items() if key in repRange and eligible(key)}
			# else: repTucks = {key:val for (key,val) in tuckedNs.items() if key <= n and (n-key) <= repRange and eligible(key)}

			if not len(repTucks): return tuckedNs, None

			repTuck = min(repTucks.items(), key=lambda tN: tN[1])[0]
			tuckedNs[repTuck] += 1

			tuckedN = repTuck
		else:
			tuckedNs[n] += 1
			tuckedN = n
	else:
		tuckedNs = insert_item(tuckedNs, {n: 1}, lambda x: x > n)
		tuckedN = n

	return tuckedNs, tuckedN


def halfGaugeFairisle(k, r, edgeNeedles, needles, direction, bed, c, tuckedNs): #*#*#*
	k.comment('start fairisle')

	if r == 31 and bed == 'b': print('edgeNeedles:', edgeNeedles) #remove #debug

	# shiftStart = ((r%2)+1)*2
	shiftStart = (r%3)*2

	edgeNs = edgeNeedles.copy()

	if direction == '+': eligibleNs = range(edgeNeedles[0], edgeNeedles[-1]+1)
	else: eligibleNs = range(edgeNeedles[0], edgeNeedles[-1]-1, -1) #neg

	if r == 31 and bed == 'b': print('eligibleNs:', eligibleNs) #remove #debug

	if bed == 'f':
		adjust = 0
		if edgeNs[0] % 2 != 0:
			if direction == '+': edgeNs[0] += 1
			else: edgeNs[0] -= 1
		if edgeNs[-1] % 2 != 0:
			if direction == '+': edgeNs[-1] -= 1
			else: edgeNs[-1] += 1
	else:
		adjust = 1
		# adjust = -1
		if edgeNs[0] % 2 == 0:
			if direction == '+': edgeNs[0] += 1
			else: edgeNs[0] -= 1
		if edgeNs[-1] % 2 == 0:
			if direction == '+': edgeNs[-1] -= 1
			else: edgeNs[-1] += 1

	for idx, n in enumerate(needles):
		if idx == 0 and abs(edgeNs[0]-n) > 4: #need to tuck from first edge needle to first knit needle to prevent dropping loops
			if direction == '+':
				repRange = range(edgeNs[0], (edgeNs[0]+shiftStart+4 if (edgeNs[0]+shiftStart+4) < n+adjust else n+adjust)) #check

				for m in range(edgeNs[0]+shiftStart, n+adjust, 4):
					tuckedNs, tuckedN = colorworkTuck(m, direction, bed, tuckedNs, repRange)
					if tuckedN is None: continue
					k.tuck(direction, f'{bed}{tuckedN}', c)

					repRange = range(tuckedN+1, (m+8 if (m+8) < n+adjust else n+adjust))
			else:
				repRange = range(edgeNs[0], (edgeNs[0]-shiftStart-4 if (edgeNs[0]-shiftStart-4) > n+adjust else n+adjust), -1) #check

				for m in range(edgeNs[0]-shiftStart, n+adjust, -4):
					tuckedNs, tuckedN = colorworkTuck(m, direction, bed, tuckedNs, repRange)
					if tuckedN is None: continue
					k.tuck(direction, f'{bed}{tuckedN}', c)

					repRange = range(tuckedN-1, (m-8 if (m-8) > n+adjust else n+adjust), -1) #check
		
		if idx < len(needles)-1: #any needle but last needle
			if (abs(n-needles[idx+1]) > 4): #need to tuck from most recently knit needle to current knit needle to prevent dropping loops
				if shiftStart != 0 and (n+adjust) in eligibleNs: k.knit(direction, f'{bed}{n+adjust}', c)

				if direction == '+':
					repRange = range(n+adjust+1, (n+adjust+shiftStart+4 if (n+adjust+shiftStart+4) < (needles[idx+1]+adjust) else (needles[idx+1]+adjust))) #check

					for m in range(n+adjust+shiftStart, needles[idx+1]+adjust, 4):
						if m == n+adjust:
							tuckedN = n+adjust
							if m in eligibleNs: k.knit(direction, f'{bed}{m}', c)
						else:
							tuckedNs, tuckedN = colorworkTuck(m, direction, bed, tuckedNs, repRange)
							if tuckedN is None: continue
							k.tuck(direction, f'{bed}{tuckedN}', c)

						repRange = range(tuckedN+1, (m+8 if (m+8) < (needles[idx+1]+adjust) else (needles[idx+1]+adjust)))
				else:
					repRange = range(n+adjust-1, (n+adjust-shiftStart-4 if (n+adjust-shiftStart-4) > (needles[idx+1]+adjust) else (needles[idx+1]+adjust)), -1) #check

					for m in range(n+adjust-shiftStart, needles[idx+1]+adjust, -4):
						if m == n+adjust:
							tuckedN = n+adjust
							if m in eligibleNs: k.knit(direction, f'{bed}{m}', c)
						else:
							tuckedNs, tuckedN = colorworkTuck(m, direction, bed, tuckedNs, repRange)
							if tuckedN is None: continue
							k.tuck(direction, f'{bed}{tuckedN}', c)
							
						repRange = range(tuckedN-1, (m-8 if (m-8) > (needles[idx+1]+adjust) else (needles[idx+1]+adjust)), -1) #check
			elif idx > 0 or (n+adjust) in eligibleNs: k.knit(direction, f'{bed}{n+adjust}', c) #just knit it
		else: #last needle
			if abs(edgeNeedles[-1]-n) > 4: #need to tuck from last knit needle to last edge needle to prevent dropping loops
				if shiftStart != 0 and (n+adjust) in eligibleNs: k.knit(direction, f'{bed}{n+adjust}', c)

				if direction == '+':
					repRange = range(n+adjust+1, (n+adjust+shiftStart+4 if (n+adjust+shiftStart+4) < edgeNs[-1] else edgeNs[-1])) #check

					for m in range(n+adjust+shiftStart, edgeNs[-1], 4):
						if m == n+adjust:
							tuckedN = n+adjust
							if m in eligibleNs: k.knit(direction, f'{bed}{m}', c)
						else:
							tuckedNs, tuckedN = colorworkTuck(m, direction, bed, tuckedNs, repRange)
							if tuckedN is None: continue
							k.tuck(direction, f'{bed}{tuckedN}', c)

						repRange = range(tuckedN+1, (m+8 if (m+8) < edgeNs[-1] else edgeNs[-1]))
					k.miss(direction, f'{bed}{edgeNeedles[-1]}', c)
				else:
					repRange = range(n+adjust-1, (n+adjust-shiftStart-4 if (n+adjust-shiftStart-4) > edgeNs[-1] else edgeNs[-1]), -1) #check

					for m in range(n+adjust-shiftStart, edgeNs[-1], -4):
						if m == n+adjust:
							tuckedN = n+adjust
							if m in eligibleNs: k.knit(direction, f'{bed}{m}', c)
						else:
							tuckedNs, tuckedN = colorworkTuck(m, direction, bed, tuckedNs, repRange)
							if tuckedN is None: continue
							k.tuck(direction, f'{bed}{tuckedN}', c)

						repRange = range(tuckedN-1, (m-8 if (m-8) > edgeNs[-1] else edgeNs[-1]), -1) #check
					k.miss(direction, f'{bed}{edgeNeedles[-1]}', c)
			else: #last needle
				if n+adjust in eligibleNs: k.knit(direction, f'{bed}{n+adjust}', c)
				if n+adjust != edgeNeedles[-1]: k.miss(direction, f'{bed}{edgeNeedles[-1]}', c)

	k.comment('end fairisle')

	return tuckedNs


# def halfGaugeJacquard(k, needles, startN, endN, length, c, bed): #*#*#*
# 	for n in needles:
# 		k.knit(f'{bed}{n}')


def wasteBorder(k, startN, endN, rows, c, gauge, offLimits, lastTime, justTuck=False, missN=None):
	# offLimits = [nRange for nRange in offLimits if nRange != []] # remove empty lists

	k.rollerAdvance(0)

	toDrop = []

	interlockRows = rows+0.5 #* #ensure carrier ends on by main knitting to position for tuck after knitting first side of waste border #TODO: switch between +0.5 and -0.5

	if startN < endN: #starts on left side (pos)
		offLimits = [[n for n in nRange if n >= startN and n <= endN] for nRange in offLimits]  # remove irrelevant needles
		offLimits = [nRange for nRange in offLimits if nRange != []] # remove empty lists

		interlockStartN = startN #leftMostBorderN-borderWidthAdd

		for i in range(0, len(offLimits)+1):
			if i == len(offLimits): interlockEndN = endN #rightMostBorderN+borderWidthAdd
			else: interlockEndN = offLimits[i][0]-1
					
			if interlockEndN > endN: interlockEndN = endN #new #*

			# if interlockStartN > interlockEndN: break
			if interlockStartN > interlockEndN: interlockStartN = interlockEndN #new #check

			tuckStartN = interlockEndN + 1

			if (justTuck and (math.floor(tuckStartN/2)+1) % 2 != 0) or (not justTuck and (math.floor(tuckStartN/2)+1) % 2 == 0): firstTuckN = tuckStartN #TODO: maybe change to % gauge #?
			else: firstTuckN = tuckStartN + 1
		
			if firstTuckN % 2 == 0: #have *last* stitch knitted in waste border on left side be on front bed if leftN is even (meaning 1st empty needle to be tucked on would be odd) so it makes a diagonal when tucked thru/out main knitting
					if ((firstTuckN//gauge) % 2) == 0: interlockStartCondition = 2 #the way the interlock func code is written, ((leftN//gauge) % 2) == 0 [which corresponds with frontBed1 func] should happen second time around, so start with frontBed2 func
					else: interlockStartCondition = 1
			else: #last stitch on left side should be on back bed
				if (((firstTuckN-1)//gauge) % 2) == 0: interlockStartCondition = 2 #the way the interlock func code is written, (((leftN-1)//gauge) % 2) == 0 [which corresponds with backBed1 func] should happen second time around, so start with backBed2 func
				else: interlockStartCondition = 1

			interlock(k, interlockStartN, interlockEndN, interlockRows, c, gauge, startCondition=interlockStartCondition)

			if lastTime:
				for n in range(interlockStartN, interlockEndN+1):
					if n % gauge == 0: toDrop.append(f'f{n}')
					if (n+1) % gauge == 0: toDrop.append(f'b{n}')

			if i < len(offLimits):
				tuckEndN = offLimits[i][-1]

				if tuckEndN > endN: break #new #*

				interlockStartN = tuckEndN+1

				for tN in range(tuckStartN, interlockStartN):
					if (justTuck and (math.floor(tN/2)+1) % 2 != 0) or (not justTuck and (math.floor(tN/2)+1) % 2 == 0):
						if tN % gauge == 0: tuckBed = 'b' #empty on back bed
						else: tuckBed = 'f'

						if (tuckEndN-tN < 2) and ((((math.floor(interlockStartN/2)+1)//gauge) % 2) == 0) and (tN % gauge == interlockStartN % gauge): continue #if last tuck needle, skip if would knit on same bed for next interlock section

						toDrop.append(f'{tuckBed}{tN}')
						k.tuck('+', f'{tuckBed}{tN}', c)

		if missN is None: missN = endN+1
		k.miss('+', f'f{missN}', c) #get carrier out of way from main knitting
	else: #starting on right side (neg)
		offLimits = [[n for n in nRange if n <= startN and n >= endN] for nRange in offLimits] # remove irrelevant needles
		offLimits = [nRange for nRange in offLimits if nRange != []] # remove empty lists

		interlockStartN = startN #rightMostBorderN+borderWidthAdd

		for i in range(len(offLimits)-1, -2, -1):
			if i == -1: interlockEndN = endN #leftMostBorderN-borderWidthAdd
			else: interlockEndN = offLimits[i][-1]+1

			if interlockEndN < endN: interlockEndN = endN #new #*

			if interlockStartN < interlockEndN: interlockStartN = interlockEndN #new #check
			# if interlockStartN < interlockEndN: break

			tuckStartN = interlockEndN-1
			tuckEndN = offLimits[i][0]

			if (justTuck and (math.floor(tuckStartN/2)+1) % 2 != 0) or (not justTuck and (math.floor(tuckStartN/2)+1) % 2 == 0): firstTuckN = tuckStartN #TODO: maybe change to % gauge #?
			else: firstTuckN = tuckStartN-1

			if firstTuckN % 2 == 0: #have *first* stitch knitted in waste border on right side before tucking in middle be on front bed if rightN is even so it makes a diagonal after tucked thru/out main knitting
				if ((firstTuckN//gauge) % 2) == 0: interlockStartCondition = 2 #the way the interlock func code is written, ((rightN//gauge) % 2) == 0 [which corresponds with frontBed1 func] should happen second time around, so start with frontBed2 func
				else: interlockStartCondition = 1
			else:
				if (((firstTuckN-1)//gauge) % 2) == 0: interlockStartCondition = 2 #the way the interlock func code is written, (((rightN-1)//gauge) % 2) == 0 [which corresponds with backBed1 func] should happen second time around, so start with backBed2 func
				else: interlockStartCondition = 1

			interlock(k, interlockStartN, interlockEndN, interlockRows, c, gauge, startCondition=interlockStartCondition)

			if lastTime:
				for n in range(interlockEndN, interlockStartN+1):
					if n % gauge == 0: toDrop.append(f'f{n}')
					if (n+1) % gauge == 0: toDrop.append(f'b{n}')

			if tuckEndN < endN: break #new #*

			if i > -1:
				interlockStartN = tuckEndN-1

				for tN in range(tuckStartN, interlockStartN, -1):
					if (justTuck and (math.floor(tN/2)+1) % 2 != 0) or (not justTuck and (math.floor(tN/2)+1) % 2 == 0):
						if tN % gauge == 0: tuckBed = 'b' #empty on back bed
						else: tuckBed = 'f'

						if (tN-tuckEndN < 2) and ((((math.floor(interlockStartN/2)+1)//gauge) % 2) == 0) and (tN % gauge == interlockStartN % gauge): continue #if last tuck needle, skip if would knit on same bed for next interlock section

						toDrop.append(f'{tuckBed}{tN}')
						k.tuck('-', f'{tuckBed}{tN}', c)

		if missN is None: missN = endN-1
		k.miss('-', f'f{missN}', c) #get carrier out of way from main knitting

	k.rollerAdvance(rollerAdvance)

	return sortBedNeedles(toDrop)


#--------------------------
#--- PREPARING KNITTING ---
#--------------------------

#--- FUNCTION FOR BRINGING IN CARRIERS ---
def catchYarns(k, leftN, rightN, carriers, gauge=1, endOnRight=[], missNeedles={}, catchMaxNeedles=False):
	'''
	*k is knitout Writer
	*leftN is the left-most needle to knit on
	*rightN is the right-most needle to knit on
	*carriers is a list of the carriers to bring in
	*gauge is gauge
	*endOnRight is an optional list of carriers that should end on the right side of the piece (by default, any carriers not in this list will end on the left)
	*missNeedles is an optional dict with carrier as key and an integer needle number as value; indicates a needle that the given carrier should miss at the end to get it out of the way
	*catchMaxNeedles is a boolean that indicates whether or not the yarns should catch on intervals based on the number of carriers that shift for each carrier to reduce build up (True) or on as many needles as possible when being brought in (False)
	'''

	k.comment('catch yarns')
	if wasteSpeedNumber > 200: k.speedNumber(wasteSpeedNumber-100)
	else: k.speedNumber(100)

	for i, c in enumerate(carriers):
		k.incarrier(c)

		if c in endOnRight: passes = range(0, 5)
		else: passes = range(0, 4)

		frontCount = 1
		backCount = 1

		for h in passes:
			if frontCount % 2 != 0: frontCount = 0
			else: frontCount = 1
			if backCount % 2 != 0: backCount = 0
			else: backCount = 1

			if h % 2 == 0:
				for n in range(leftN, rightN+1):
					if n % gauge == 0 and ((catchMaxNeedles and ((n/gauge) % 2) == 0) or (((n/gauge) % len(carriers)) == i)):
						if frontCount % 2 == 0: k.knit('+', f'f{n}', c)
						elif n == rightN: k.miss('+', f'f{n}', c) #TODO: make boolean #?
						frontCount += 1
					elif (gauge == 1 or n % gauge != 0) and ((catchMaxNeedles and (((n-1)/gauge) % 2) == 0) or ((((n-1)/gauge) % len(carriers)) == i)):
						if backCount % 2 == 0: k.knit('+', f'b{n}', c)
						elif n == rightN: k.miss('+', f'f{n}', c)
						backCount += 1
					elif n == rightN: k.miss('+', f'f{n}', c)
			else:
				for n in range(rightN, leftN-1, -1):
					if n % gauge == 0 and ((catchMaxNeedles and ((n/gauge) % 2) != 0) or (((n/gauge) % len(carriers)) == i)):
						if frontCount % 2 != 0: k.knit('-', f'f{n}', c)
						elif n == leftN: k.miss('-', f'f{n}', c)
						frontCount += 1
					elif (gauge == 1 or n % gauge != 0) and ((catchMaxNeedles and (((n-1)/gauge) % 2) != 0) or ((((n-1)/gauge) % len(carriers)) == i)):
						if backCount % 2 != 0: k.knit('-', f'b{n}', c)
						elif n == leftN: k.miss('-', f'f{n}', c)
						backCount += 1
					elif n == leftN: k.miss('-', f'f{n}', c)

		if c in missNeedles:
			if c in endOnRight: k.miss('+', f'f{missNeedles[c]}', c)
			else: k.miss('-', f'f{missNeedles[c]}', c)


#--- FUNCTION FOR DOING ALL THINGS BEFORE CAST-ON (catch/initialize yarns, waste yarn, draw thread) ---
def drawThread(k, leftN, rightN, drawC, side='l', circular=False, missDraw=None, gauge=1):
	def posDraw(bed='f', addMiss=True):
		for n in range(leftN, rightN+1):
			if (n % gauge == 0 and bed=='f') or ((gauge == 1 or n % gauge != 0) and bed=='b'): k.knit('+', f'{bed}{n}', drawC)
			elif n == rightN: k.miss('+', f'{bed}{n}', drawC)
		if addMiss and missDraw is not None: k.miss('+', f'{bed}{missDraw}', drawC)


	def negDraw(bed='f', addMiss=True):
		for n in range(rightN, leftN-1, -1):
			if (n % gauge == 0 and bed=='f') or ((gauge == 1 or n % gauge != 0) and bed=='b'):  k.knit('-', f'{bed}{n}', drawC)
			elif n == leftN: k.miss('-', f'{bed}{n}', drawC)
		if addMiss and missDraw is not None: k.miss('-', f'{bed}{missDraw}', drawC)


	k.comment('draw thread')

	if side == 'r':
		if circular: negDraw('b', False)
		posDraw()
	else:
		if circular: posDraw('b', False)
		negDraw()


def wasteSection(k, leftN, rightN, closedCaston=True, wasteC='1', drawC='2', otherCs = [], gauge=1, endOnRight=[], firstNeedles={}, catchMaxNeedles=False, initial=True, drawMiddle=False, interlockLength=40):
	'''
	Does everything to prepare for knitting prior to (and not including) the cast-on.
		- bring in carriers
		- catch the yarns to make them secure
		- knit waste section for the rollers to catch
		- add draw thread
	Can also be used to produce a waste section to go in-between samples.

	*k is knitout Writer
	*leftN is the left-most needle to knit on
	*rightN is the right-most needle to knit on
	*closedCaston is a boolean that determines what happens with the draw thread (if True, drops back-bed needles and knits draw on front-bed; if False, doesn't drop and knits draw on both beds)
	*wasteC is an integer in string form indicating the carrier number to be used for the waste yarn
	*drawC is same as above, but for the draw thread carrier
	*otherCs is an *optional* list of other carriers that should be brought in/positioned with catchYarns (NOTE: leave empty if not initial wasteSection)
	*gauge is... gauge
	*endOnRight is an *optional* list of carriers that should be parked on the right side after the wasteSection (**see NOTE below for details about what to do if not initial**) — e.g.: endOnRight=['2', '3']
	*firstNeedles is an *optional* dictionary with carrier as key and a list of [leftN, rightN] as the value. It indicates the edge-most needles in the first row that the carrier is used in for the main piece. — e.g.: firstNeedles={'1': [0, 10]}
	*catchMaxNeedles is a boolean that determines whether or not the maximum number of needles (possible for the given gauge) will be knitted on for *every* carrier (yes if True; if False, knits on interval determined by number of carriers)
	*initial is a boolean that, if True, indicates that this wasteSection is the very first thing being knitted for the piece; otherwise, if False, it's probably a wasteSection to separate samples (and will skip over catchYarns)
	*drawMiddle is a boolean that, if True, indicates that a draw thread should be placed in the middle of the waste section (and no draw thread will be added at end, also no circular knitting, so only interlock)
	*interlockLength is the number of passes of interlock that should be included (note that, if not drawMiddle, 8 rows of circular will also be added onto the x number of interlockLength indicated)

	NOTE:
	if initial wasteSection, side (prior to this wasteSection) is assumed to be left for all carriers
	if not initial wasteSection, follow these guidelines for positioning:
		-> wasteC: if currently on right side (prior to this wasteSection), put it in 'endOnRight' list; otherwise, don't
		-> drawC:
			if not drawMiddle: if currently on left side, put it in 'endOnRight' list; otherwise, don't
			else: if currently on right side, put it in 'endOnRight' list; otherwise, don't
	'''
	carrierLocations = {}
	k.stitchNumber(stitchNumber)
	k.rollerAdvance(rollerAdvance)
	
	missWaste = None
	missDraw = None
	missOtherCs = {}
	if len(firstNeedles):
		if wasteC in firstNeedles:
			if wasteC in endOnRight:
				missWaste = firstNeedles[wasteC][1]
				carrierLocations[wasteC] = firstNeedles[wasteC][1]
			else:
				missWaste = firstNeedles[wasteC][0]
				carrierLocations[wasteC] = firstNeedles[wasteC][0]
		
		if drawC in firstNeedles:
			if drawC in endOnRight:
				missDraw = firstNeedles[drawC][1]
				carrierLocations[drawC] = firstNeedles[drawC][1]
			else:
				missDraw = firstNeedles[drawC][0]
				carrierLocations[drawC] = firstNeedles[drawC][0]

		if len(otherCs):
			for c in range(0, len(otherCs)):
				if otherCs[c] in firstNeedles:
					if otherCs[c] in endOnRight:
						missOtherCs[otherCs[c]] = firstNeedles[otherCs[c]][1]
						carrierLocations[otherCs[c]] = firstNeedles[otherCs[c]][1]
					else:
						missOtherCs[otherCs[c]] = firstNeedles[otherCs[c]][0]
						carrierLocations[otherCs[c]] = firstNeedles[otherCs[c]][0]

	carriers = [wasteC, drawC]
	carriers.extend(otherCs)
	carriers = list(set(carriers))

	carriers = [x for x in carriers if x is not None]

	if len(carriers) != len(carrierLocations):
		for c in carriers:
			if c not in carrierLocations:
				if c in endOnRight: carrierLocations[c] = rightN
				else: carrierLocations[c] = leftN

	if initial:
		catchEndOnRight = endOnRight.copy()

		if closedCaston and not drawMiddle:
			if drawC in endOnRight:
				catchEndOnRight.remove(drawC)
				if drawC in missOtherCs: missOtherCs[drawC] = firstNeedles[drawC][0] 
			else:
				catchEndOnRight.append(drawC)
				if drawC in missOtherCs: missOtherCs[drawC] = firstNeedles[drawC][1] 

		catchYarns(k, leftN, rightN, carriers, gauge, catchEndOnRight, missOtherCs, catchMaxNeedles)

	k.comment('waste section')
	k.speedNumber(wasteSpeedNumber)
	k.stitchNumber(wasteStitchNumber)

	if drawMiddle: interlockLength //= 2

	if drawC in endOnRight: drawSide = 'r'
	else: drawSide = 'l'

	if wasteC in endOnRight: #TODO: add extra pass if wasteC == drawC and closedCaston == True
		if initial and interlockLength > 24:
			interlock(k, rightN, leftN, 24, wasteC, gauge)
			k.pause('cut yarns')
			interlock(k, rightN, leftN, interlockLength-24, wasteC, gauge)
		else: interlock(k, rightN, leftN, interlockLength, wasteC, gauge)
		if drawMiddle:
			if drawC is not None: drawThread(k, leftN, rightN, drawC, side=drawSide, circular=True, missDraw=missDraw, gauge=gauge) #new

			if initial and interlockLength > 12:
				if interlockLength < 24:
					pauseAfter = 24-interlockLength
					interlock(k, rightN, leftN, pauseAfter, wasteC, gauge) # 20 32 (16) #12 interlockLength-8 # 12
					k.pause('cut yarns')
					interlock(k, rightN, leftN, interlockLength-pauseAfter, wasteC, gauge) # 8 interlockL 20- (32-20) 20-32 + 20+20
				else: interlock(k, rightN, leftN, interlockLength, wasteC, gauge)
			else:
				interlock(k, rightN, leftN, interlockLength, wasteC, gauge)
				if initial: k.pause('cut yarns')
		else:
			if initial: k.pause('cut yarns')
			circular(k, rightN, leftN, 8, wasteC, gauge)
		if missWaste is not None: k.miss('+', f'f{missWaste}', wasteC)
	else:
		if initial and interlockLength > 24:
			interlock(k, leftN, rightN, 24, wasteC, gauge)
			k.pause('cut yarns')
			interlock(k, leftN, rightN, interlockLength-24, wasteC, gauge)
		else: interlock(k, leftN, rightN, interlockLength, wasteC, gauge)
		if drawMiddle:
			if drawC is not None: drawThread(k, leftN, rightN, drawC, side=drawSide, circular=True, missDraw=missDraw, gauge=gauge) #new

			if initial and interlockLength > 12:
				if interlockLength < 24:
					pauseAfter = 24-interlockLength
					interlock(k, leftN, rightN, pauseAfter, wasteC, gauge) # 20 32 (16) #12 interlockLength-8 # 12
					k.pause('cut yarns')
					interlock(k, leftN, rightN, interlockLength-pauseAfter, wasteC, gauge) # 8 interlockL 20- (32-20) 20-32 + 20+20
				else: interlock(k, leftN, rightN, interlockLength, wasteC, gauge)
			else:
				interlock(k, leftN, rightN, interlockLength, wasteC, gauge)
				if initial: k.pause('cut yarns')
		else:
			if initial: k.pause('cut yarns')
			circular(k, leftN, rightN, 8, wasteC, gauge)
		if missWaste is not None: k.miss('-', f'f{missWaste}', wasteC)

	if closedCaston and not drawMiddle:
		for n in range(leftN, rightN+1):
			if (n + 1) % gauge == 0: k.drop(f'b{n}')

	if not drawMiddle and drawC is not None: drawThread(k, leftN, rightN, drawC, side=drawSide, circular=(not closedCaston), missDraw=missDraw, gauge=gauge)

	resetSettings(k)
	return carrierLocations


#--------------------------------------
#--- CASTONS / BINDOFFS / PLACEMENT ---
#--------------------------------------

#--- FUNCTION FOR CASTING ON CLOSED TUBES (zig-zag) ---
def singleBedCaston(k, startN, endN, c, bed='f', gauge=1):
	'''
	*k is the knitout Writer
	*startN is the initial needle to cast-on
	*endN is the last needle to cast-on (inclusive)
	*c is the carrier to use for the cast-on
	*bed is the bed on which the cast-on should occur
	*gauge is gauge

	- alternating knit cast-on
	- total of 2 passes; carrier will end on the side it started
	'''
	k.comment('single bed cast-on')
	k.speedNumber(speedNumber)

	if gauge == 1 or bed == 'f': condition = lambda n: n % gauge == 0
	else: condition = lambda n: n % gauge != 0

	if endN > startN: #first pass is pos
		dir1 = '+'
		dir2 = '-'
		needleRange1 = range(startN, endN+1)
		needleRange2 = range(endN, startN-1, -1)
	else: #first pass is neg
		dir1 = '-'
		dir2 = '+'
		needleRange1 = range(startN, endN-1, -1)
		needleRange2 = range(endN, startN+1)

	for n in needleRange1:
		if condition and (((n/gauge) % 2) == 0): k.knit(dir1, f'{bed}{n}', c)
		elif n == endN: k.miss(dir1, f'{bed}{n}', c)
	for n in needleRange2:
		if condition and (((n/gauge) % 2) != 0): k.knit(dir2, f'{bed}{n}', c)
		elif n == startN: k.miss(dir2, f'{bed}{n}', c)

	k.comment('begin main piece')


#--- FUNCTION FOR CASTING ON CLOSED TUBES (zig-zag) ---
def closedTubeCaston(k, startN, endN, c, gauge=1):
	'''
	*k is the knitout Writer
	*startN is the initial needle to cast-on
	*endN is the last needle to cast-on (inclusive)
	*c is the carrier to use for the cast-on
	*gauge is gauge

	- only one pass; carrier will end on the side opposite to which it started
	'''
	k.comment('closed tube cast-on')
	k.speedNumber(speedNumber)

	if endN > startN: #pass is pos
		direction = '+'
		bed1 = 'f'
		bed2 = 'b'
		condition1 = lambda n: n % gauge == 0
		condition2 = lambda n: (n % gauge != 0 or gauge == 1)
		needleRange = range(startN, endN+1)
	else: #pass is neg
		direction = '-'
		bed1 = 'b'
		bed2 = 'f'
		condition1 = lambda n: (n % gauge != 0 or gauge == 1)
		condition2 = lambda n: n % gauge == 0
		needleRange = range(startN, endN-1, -1)

	k.rack(0.25)

	for n in needleRange:
		if condition1(n): k.knit(direction, f'{bed1}{n}', c)
		if condition2(n): k.knit(direction, f'{bed2}{n}', c)

	k.rack(0)
	k.comment('begin main piece')


#--- FUNCTION FOR CASTING ON OPEN TUBES ---
def openTubeCaston(k, startN, endN, c, gauge=1):
	'''
	*k is the knitout Writer
	*startN is the initial needle to cast-on
	*endN is the last needle to cast-on (inclusive)
	*c is the carrier to use for the cast-on
	*gauge is gauge

	- total of 6 passes knitted circularly (3 on each bed); carrier will end on the side it started
	- first 4 passes are alternating cast-on, last 2 are extra passes to make sure loops are secure
	'''
	k.comment('open tube cast-on')
	k.speedNumber(speedNumber)

	if endN > startN: #first pass is pos
		dir1 = '+'
		dir2 = '-'
		needleRange1 = range(startN, endN+1)
		needleRange2 = range(endN, startN-1, -1)
	else: #first pass is neg
		dir1 = '-'
		dir2 = '+'
		needleRange1 = range(startN, endN-1, -1)
		needleRange2 = range(endN, startN+1)

	for n in needleRange1:
		if n % gauge == 0 and (((n/gauge) % 2) == 0):
			k.knit(dir1, f'f{n}', c)
		elif n == endN: k.miss(dir1, f'f{n}', c)
	for n in needleRange2:
		if (gauge == 1 or n % gauge != 0) and ((((n-1)/gauge) % 2) == 0):
			k.knit(dir2, f'b{n}', c)
		elif n == startN: k.miss(dir2, f'b{n}', c)

	for n in needleRange1:
		if n % gauge == 0 and (((n/gauge) % 2) != 0):
			k.knit(dir1, f'f{n}', c)
		elif n == endN: k.miss(dir1, f'f{n}', c)
	for n in needleRange2:
		if (gauge == 1 or n % gauge != 0) and ((((n-1)/gauge) % 2) != 0):
			k.knit(dir2, f'b{n}', c)
		elif n == startN: k.miss(dir2, f'b{n}', c)

	#two final passes now that loops are secure
	for n in needleRange1:
		if n % gauge == 0: k.knit(dir1, f'f{n}', c)
		elif n == endN: k.miss(dir1, f'f{n}', c)
	for n in needleRange2:
		if (n+1) % gauge == 0: k.knit(dir2, f'b{n}', c)
		elif n == startN: k.miss(dir2, f'b{n}', c)

	k.comment('begin main piece')


#--- FUNCTION FOR TAIL AT END OF BINDOFF ---
def bindoffTail(k, lastNeedle, dir, c, bed='b', shortrowing=False):
	'''
	*TODO
	'''
	otherDir = '-'
	miss1 = lastNeedle+1
	miss2 = lastNeedle-1
	if dir == '-':
		otherDir = '+'
		miss1 = lastNeedle-1
		miss2 = lastNeedle+1

	k.comment('tail')
	if shortrowing: k.rollerAdvance(100)
	else: k.rollerAdvance(200)

	k.miss(dir, f'{bed}{miss1}', c)
	k.pause('tail?')

	for i in range(0, 6):
		k.knit(otherDir, f'{bed}{lastNeedle}', c)
		k.miss(otherDir, f'{bed}{miss2}', c)
		k.knit(dir, f'{bed}{lastNeedle}', c)
		k.miss(dir, f'{bed}{miss1}', c)

	k.outcarrier(c)
	k.pause(f'cut C{c}')

	k.addRollerAdvance(200)
	k.drop(f'{bed}{lastNeedle}')


#--- SECURE BINDOFF FUNCTION (can also be used for decreasing large number of stitches) ---
def bindoff(k, count, xferNeedle, c, side='l', doubleBed=True, asDecMethod=False, emptyNeedles=[]):
	'''
	*TODO
	'''
	if not asDecMethod: k.comment('bindoff')

	def posLoop(op=None, bed=None): #v
		for x in range(xferNeedle, xferNeedle+count):
			if op == 'knit':
				if f'{bed}{x}' not in emptyNeedles: k.knit('+', f'{bed}{x}', c)
			elif op == 'xfer':
				receive = 'b'
				if bed == 'b': receive = 'f'
				if f'{bed}{x}' not in emptyNeedles: k.xfer(f'{bed}{x}', f'{receive}{x}')
			else:
				if x == xferNeedle + count - 1 and not asDecMethod: break

				k.xfer(f'b{x}', f'f{x}') #don't have to worry about empty needles here because binding these off
				k.rack(-1)
				k.xfer(f'f{x}', f'b{x+1}')
				k.rack(0)
				if x != xferNeedle:
					if x > xferNeedle+3: k.addRollerAdvance(-50)
					k.drop(f'b{x-1}')
				k.knit('+', f'b{x+1}', c)

				if asDecMethod and len(emptyNeedles) and x == xferNeedle+count-1 and f'b{x+1}' in emptyNeedles: #transfer this to a non-empty needle if at end and applicable
					if f'f{x+1}' not in emptyNeedles: k.xfer(f'b{x+1}', f'f{x+1}')
					else:
						for z in range(x+2, x+7): #TODO: check what gauge should be
							if f'f{z}' not in emptyNeedles:
								k.rack(z-(x+1))
								k.xfer(f'b{x+1}', f'f{z}')
								k.rack(0)
								break
							elif f'b{z}' not in emptyNeedles:
								k.xfer(f'b{x+1}', f'f{x+1}')
								k.rack((x+1)-z)
								k.xfer(f'f{x+1}', f'b{z}')
								k.rack(0)
								break

				if x < xferNeedle+count-2: k.tuck('-', f'b{x}', c)
				if not asDecMethod and (x == xferNeedle+3 or (x == xferNeedle+count-2 and xferNeedle+3 > xferNeedle+count-2)): k.drop(f'b{xferNeedle-1}')
	#--- end posLoop func ---#^


	def negLoop(op=None, bed=None): #v
		for x in range(xferNeedle+count-1, xferNeedle-1, -1):
			if op == 'knit':
				if f'{bed}{x}' not in emptyNeedles: k.knit('-', f'{bed}{x}', c)
			elif op == 'xfer':
				receive = 'b'
				if bed == 'b': receive = 'f'
				if f'{bed}{x}' not in emptyNeedles: k.xfer(f'{bed}{x}', f'{receive}{x}')
			else:
				if x == xferNeedle and not asDecMethod: break

				k.xfer(f'b{x}', f'f{x}')
				k.rack(1)
				k.xfer(f'f{x}', f'b{x-1}')
				k.rack(0)
				if x != xferNeedle+count-1:
					if x < xferNeedle+count-4: k.addRollerAdvance(-50)
					k.drop(f'b{x+1}')
				k.knit('-', f'b{x-1}', c)

				if asDecMethod and len(emptyNeedles) and x == xferNeedle-2 and f'b{x-1}' in emptyNeedles: #transfer this to a non-empty needle if at end and applicable
					if f'f{x-1}' not in emptyNeedles: k.xfer(f'b{x-1}', f'f{x-1}')
					else:
						for z in range(x-2, x-7, -1): #TODO: check what gauge should be
							if f'f{z}' not in emptyNeedles:
								k.rack(z-(x+1))
								k.xfer(f'b{x-1}', f'f{z}')
								k.rack(0)
								break
							elif f'b{z}' not in emptyNeedles:
								k.xfer(f'b{x-1}', f'f{x-1}')
								k.rack((x+1)-z)
								k.xfer(f'f{x-1}', f'b{z}')
								k.rack(0)
								break

				if x > xferNeedle+1: k.tuck('+', f'b{x}', c)
				if not asDecMethod and (x == xferNeedle+count-4 or (x == xferNeedle+1 and xferNeedle+count-4 < xferNeedle+1)): k.drop(f'b{xferNeedle+count}')
	#--- end negLoop func ---#^


	if side == 'l':
		if not asDecMethod:
			posLoop('knit', 'f')
			if doubleBed: negLoop('knit', 'b')

		xferSettings(k)
		posLoop('xfer', 'f')
		k.rollerAdvance(50)
		k.addRollerAdvance(-50)
		if not asDecMethod: k.tuck('-', f'b{xferNeedle-1}', c)
		k.knit('+', f'b{xferNeedle}', c)
		posLoop()

		if not asDecMethod: bindoffTail(k, xferNeedle+count-1, '+', c)
	else:
		xferNeedle = xferNeedle-count + 1

		if not asDecMethod:
			negLoop('knit', 'f')
			if doubleBed: posLoop('knit', 'b')

		xferSettings(k)
		negLoop('xfer', 'f')
		k.rollerAdvance(50)
		k.addRollerAdvance(-50)
		if not asDecMethod: k.tuck('+', f'b{xferNeedle+count}', c)
		k.knit('-', f'b{xferNeedle+count-1}', c)
		negLoop()

		if not asDecMethod: bindoffTail(k, xferNeedle, '-', c)


def halfGaugeOpenBindoff(k, count, xferNeedle, c, side='l', asDecMethod=False, xtraSecure=False):
	'''
	*k is knitout Writer
	*count is the number of *TODO
	*xferNeedle is the first (edge-most) needle involved in the bindoff
	*c is the carrier being used for the binding off
	*side is the side on which the bind off starts; valid values are 'l' (left) and 'r' (right)
	*asDecMethod is *TODO
	'''

	if xferNeedle % 2 == 0:
		bed1 = 'f'
		bed2 = 'b'
	else:
		bed1 = 'b'
		bed2 = 'f'
	
	if asDecMethod:
		if side == 'l': k.comment(f'open dec {count} on left (bed {bed1}) by bindoff ({xferNeedle} -> {xferNeedle+count})')
		else: k.comment(f'open dec {count} on right by bindoff ({xferNeedle} -> {xferNeedle-count})')
	else:
		k.pause('bindoff') #TODO: make sure this pause actually happens
		k.comment('open-tube bindoff')
	k.rollerAdvance(50)

	if side == 'l':
		adjust = 2
		if bed1 == 'f': rack = 2
		else: rack = -2
		dir1 = '+'
		dir2 = '-'
		otherEdgeN = xferNeedle+count-1
		if asDecMethod: otherEdgeN += 1
		bindRange1 = range(xferNeedle, otherEdgeN, 2)
		if (bed2 == 'b' and otherEdgeN % 2 != 0) or (bed2 == 'f' and otherEdgeN % 2 == 0):
			smallRack = 1
			bindRange2 = range(otherEdgeN, xferNeedle+1, -2)
		else:
			smallRack = -1
			bindRange2 = range(otherEdgeN-1, xferNeedle, -2)
	else:
		adjust = -2
		if bed1 == 'f': rack = -2
		else: rack = 2
		dir1 = '-'
		dir2 = '+'
		otherEdgeN = xferNeedle-count+1
		if asDecMethod: otherEdgeN -= 1
		bindRange1 = range(xferNeedle, otherEdgeN, -2)
		if (bed2 == 'b' and otherEdgeN % 2 != 0) or (bed2 == 'f' and otherEdgeN % 2 == 0):
			bindRange2 = range(otherEdgeN, xferNeedle-1, 2)
		else:
			bindRange2 = range(otherEdgeN+1, xferNeedle, 2)

	for n in bindRange1:
		k.tuck(dir2, f'{bed1}{n-(adjust//2)}', c)

		if xtraSecure:
			k.tuck(dir2, f'{bed2}{n-adjust}', c)

		k.xfer(f'{bed1}{n}', f'{bed2}{n}')
		if abs(n-otherEdgeN) != 1 or asDecMethod: #skip if 1 in from otherEdgeN (note: only applicable if count % 2 == 0, since xferNeedle & otherEdgeN would have different parity)
			k.rack(rack)
			k.xfer(f'{bed2}{n}', f'{bed1}{n+adjust}')
			k.rack(0)
			k.drop(f'{bed1}{n-(adjust//2)}') #TODO: maybe k.addRollerAdvance(-50) #?

			if xtraSecure: k.drop(f'{bed2}{n-adjust}')

			k.knit(dir1, f'{bed1}{n+adjust}', c)

	if asDecMethod:
		k.miss(dir2, f'f{otherEdgeN}', c) #miss carrier out of the way
		resetSettings(k)
	else:
		k.rack(rack//2)
		if count % 2 != 0: #note: if count % 2 != 0, xferNeedle & otherEdgeN have same parity
			k.tuck(dir1, f'{bed1}{otherEdgeN+(adjust//2)}', c)
			k.xfer(f'{bed1}{otherEdgeN}', f'{bed2}{otherEdgeN-(adjust//2)}')
			k.rack(0)
			k.drop(f'{bed1}{otherEdgeN+(adjust//2)}') #TODO: maybe k.addRollerAdvance(-50) #?
			k.knit(dir2, f'{bed2}{otherEdgeN-(adjust//2)}', c)
		else: #xferNeedle & otherEdgeN have different parity (aka abs(n-otherEdgeN) != 1, so skipped last bit)
			k.drop(f'{bed1}{otherEdgeN-adjust}') #drop the tuck that was skipped #TODO: maybe k.addRollerAdvance(-50) #? 
			k.tuck(dir1, f'{bed2}{otherEdgeN+(adjust//2)}', c)
			k.xfer(f'{bed2}{otherEdgeN-(adjust//2)}', f'{bed1}{otherEdgeN}')
			k.rack(0)
			k.xfer(f'{bed1}{otherEdgeN}', f'{bed2}{otherEdgeN}')
			k.drop(f'{bed2}{otherEdgeN+(adjust//2)}') #TODO: maybe k.addRollerAdvance(-50) #?
			k.knit(dir2, f'{bed2}{otherEdgeN}', c)

		for n in bindRange2:
			k.tuck(dir1, f'{bed2}{n+(adjust//2)}', c)
			k.xfer(f'{bed2}{n}', f'{bed1}{n}')
			k.rack(rack)
			k.xfer(f'{bed1}{n}', f'{bed2}{n-adjust}') #+rack
			k.rack(0)
			k.drop(f'{bed2}{n+(adjust//2)}') #TODO: maybe k.addRollerAdvance(-50) #?
			k.knit(dir2, f'{bed2}{n-adjust}', c)

		bindoffTail(k, xferNeedle-(adjust//2), dir2, c, bed2)


def halfGaugeRib1x1Bindoff(k, count, xferNeedle, c, side='l'):
	k.comment('rib bindoff')
	k.rollerAdvance(100)
	
	if xferNeedle % 2 == 0:
		bed1 = 'f'
		bed2 = 'b'
	else:
		bed1 = 'b'
		bed2 = 'f'

	if side == 'l':
		adjust = 2
		if bed1 == 'f': rack = 2
		else: rack = -2
		dir1 = '+'
		dir2 = '-'
		otherEdgeN = xferNeedle+count-1

		bindRange1 = range(xferNeedle, otherEdgeN, 2)
		if (bed2 == 'b' and otherEdgeN % 2 != 0) or (bed2 == 'f' and otherEdgeN % 2 == 0):
			smallRack = 1
			bindRange2 = range(otherEdgeN, xferNeedle, -2)
		else:
			smallRack = -1
			bindRange2 = range(otherEdgeN-1, xferNeedle, -2)
	else:
		adjust = -2
		if bed1 == 'f': rack = -2
		else: rack = 2
		dir1 = '-'
		dir2 = '+'
		otherEdgeN = xferNeedle-count+1
		bindRange1 = range(xferNeedle, otherEdgeN, -2)

		if (bed2 == 'b' and otherEdgeN % 2 != 0) or (bed2 == 'f' and otherEdgeN % 2 == 0):
			bindRange2 = range(otherEdgeN, xferNeedle, 2)
		else:
			bindRange2 = range(otherEdgeN+1, xferNeedle, 2)

	k.comment(f'bindoff {bed1} bed')
	for n in bindRange1:
		k.tuck(dir2, f'{bed1}{n-(adjust//2)}', c)
		k.xfer(f'{bed1}{n}', f'{bed2}{n}')

		k.rollerAdvance(0) #counteract drop
		k.drop(f'{bed1}{n-(adjust//2)}') #TODO: see if need addRollerAdvance -100 for this too
		k.rollerAdvance(100)
		k.knit(dir1, f'{bed2}{n}', c)
		
		if abs(n-otherEdgeN) != 1: #skip if 1 in from otherEdgeN (note: only applicable if count % 2 == 0, since xferNeedle & otherEdgeN would have different parity)
			k.rollerAdvance(0) #counteract tuck
			k.rack(rack)
			k.tuck(dir2, f'{bed1}{n+(adjust//2)}', c)
			k.xfer(f'{bed2}{n}', f'{bed1}{n+adjust}')
			k.rack(0)
			k.drop(f'{bed1}{n+(adjust//2)}')

			k.rollerAdvance(100)
			k.knit(dir1, f'{bed1}{n+adjust}', c) #knit on bed1 #TODO: try knitting this in other direction

	k.rack(rack//2)
	if count % 2 != 0: #note: if count % 2 != 0, xferNeedle & otherEdgeN have same parity #TODO: add tucks to this too
		k.xfer(f'{bed1}{otherEdgeN}', f'{bed2}{otherEdgeN-(adjust//2)}')
		k.rack(0)
		k.knit(dir2, f'{bed2}{otherEdgeN-(adjust//2)}', c)
	else:
		k.xfer(f'{bed2}{otherEdgeN-(adjust//2)}', f'{bed1}{otherEdgeN}')
		k.rack(0)
		k.xfer(f'{bed1}{otherEdgeN}', f'{bed2}{otherEdgeN}')
		k.knit(dir2, f'{bed2}{otherEdgeN}', c)

	k.comment(f'bindoff {bed2} bed')
	for n in bindRange2:
		k.rollerAdvance(0) #counteract tuck
		k.tuck(dir1, f'{bed2}{n+(adjust//2)}', c)
		k.xfer(f'{bed2}{n}', f'{bed1}{n}')

		k.drop(f'{bed2}{n+(adjust//2)}')
		k.rollerAdvance(100)
		k.knit(dir2, f'{bed1}{n}', c) #knit on bed1

		k.rollerAdvance(0) #counteract tuck
		k.rack(rack)
		k.tuck(dir1, f'{bed1}{n+(adjust//2)}', c)
		k.xfer(f'{bed1}{n}', f'{bed2}{n-adjust}') #+rack
		k.rack(0)
		k.drop(f'{bed1}{n+(adjust//2)}')

		k.rollerAdvance(100)
		k.knit(dir2, f'{bed2}{n-adjust}', c) #knit on bed2

	bindoffTail(k, xferNeedle-(adjust//2), dir2, c, bed2)


#--- FINISH BY DROP FUNCTION ---
def dropFinish(k, frontNeedleRanges=[], backNeedleRanges=[], carriers=[], rollOut=True, emptyNeedles=[], direction='+', borderC=None, borderStPat=None):
	'''
	*k is knitout Writer
	*frontNeedleRanges is a list of [leftN, rightN] pairs for needles to drop on the front bed; if multiple sections, can have sub-lists as so: [[leftN1, rightN1], [leftN2, rightN2], ...], or just [leftN, rightN] if only one section
	*backNeedleRanges is same as above, but for back bed
	*carriers is list of carriers to take out (optional, only if you want to take them out using this function)
	*rollOut is an optional boolean parameter indicating whether extra roller advance should be added to roll the piece out
	*emptyNeedles is an optional list of needles that are not currently holding loops (e.g. if using stitch pattern), so don't waste time dropping them
	*direction is an optional parameter to indicate which direction the first pass should have (valid values are '+' or '-'). (NOTE: this is an important value to pass if borderC is included, so know which direction to knit first with borderC). #TODO: maybe just add a knitout function to find line that last used the borderC carrier
	*borderC is an optional carrier that will knit some rows of waste yarn before dropping, so that there is a border edge on the top to prevent the main piece from unravelling (NOTE: if borderC is None, will not add any border)
	*borderStPat is *TODO
	'''

	k.comment('drop finish')

	outCarriers = carriers.copy()

	if len(carriers):
		if borderC is not None and borderC in carriers: outCarriers.remove(borderC) # remove so can take it out at end instead 
		for c in outCarriers: k.outcarrier(c)

	def knitBorder(posNeedleRange, posBed, negNeedleRange, negBed): #v
		beg = 0
		length = 16 #16 rows of waste #TODO: maybe make this a parameter?

		if direction == '-':
			beg += 1
			length += 1
			side = 'r'
		else: side = 'l'

		def knitBorderPos(needleRange, bed):
			for n in range(needleRange[0], needleRange[1]+1):
				if f'{bed}{n}' not in emptyNeedles: k.knit('+', f'{bed}{n}', borderC)
		
		def knitBorderNeg(needleRange, bed):
			for n in range(needleRange[1], needleRange[0]-1, -1):
				if f'{bed}{n}' not in emptyNeedles: k.knit('-', f'{bed}{n}', borderC)
		
		if borderStPat is not None and len(frontNeedleRanges) and len(backNeedleRanges): #TODO: have option for single bed stitch pattern
			stitchPatternTube(k, leftN=posNeedleRange[0], rightN=posNeedleRange[1], c=borderC, wasteC=None, side=side, patterns=[borderStPat], defaultLength=16, wasteDivider=False)
		else:
			for r in range(beg, length):
				if r % 2 == 0: knitBorderPos(posNeedleRange, posBed)
				else: knitBorderNeg(negNeedleRange, negBed)
	#--- end knitBorder func ---#^


	if borderC is not None:
		if len(frontNeedleRanges) and len(backNeedleRanges):
			needleRanges1 = frontNeedleRanges
			bed1 = 'f'
			needleRanges2 = backNeedleRanges
			bed2 = 'b'
		else:
			if len(frontNeedleRanges):
				needleRanges1 = frontNeedleRanges
				bed1 = 'f'
				needleRanges2 = frontNeedleRanges
				bed2 = 'f'
			else:
				needleRanges1 = backNeedleRanges
				bed1 = 'b'
				needleRanges2 = backNeedleRanges
				bed2 = 'b'

		if type(needleRanges1[0]) == int: #just one range (one section)
			knitBorder(needleRanges1, bed1, needleRanges2, bed2)
		else:
			for nr in range(0, len(needleRanges1)):
				knitBorder(needleRanges1[nr], bed1, needleRanges2[nr], bed2)

	def dropOnBed(needleRanges, bed): #v
		if type(needleRanges[0]) == int: #just one range (one section)
			if rollOut and (needleRanges is backNeedleRanges or not len(backNeedleRanges)): k.addRollerAdvance(2000) #TODO: determine what max roller advance is
			for n in range(needleRanges[0], needleRanges[1]+1):
				if f'{bed}{n}' not in emptyNeedles: k.drop(f'{bed}{n}')
		else: #multiple ranges (multiple sections, likely shortrowing)
			for nr in needleRanges:
				if rollOut and needleRanges.index(nr) == len(needleRanges)-1 and (needleRanges is backNeedleRanges or not len(backNeedleRanges)): k.addRollerAdvance(2000) #TODO: determine what max roller advance is
				for n in range(nr[0], nr[1]+1):
					if f'{bed}{n}' not in emptyNeedles: k.drop(f'{bed}{n}')
	#--- end dropOnBed func ---#^


	if len(frontNeedleRanges): dropOnBed(frontNeedleRanges, 'f')
	if len(backNeedleRanges): dropOnBed(backNeedleRanges, 'b')

	if borderC is not None and borderC in carriers: k.outcarrier(borderC)


#----------------------------------
#--- SHAPING (INC/DEC) & BINDOFF---
#----------------------------------
def notEnoughNeedlesDecCheck(k, decNeedle, otherEdgeNeedle, count, c, gauge=1, rearrange=True): #TODO: note that this is not applicable in this way for gauge == 1 and dec == 2 (only need to worry if width == 1 [not 2]) #check if enough needles to dec (for when dec == 2) #NOTE: should only do this after *all* dec #NOTE: should knit through stacked loops if dec by > 2 on both side and width isn't big enough
	'''
	# *decNeedle and otherEdgeNeedle reference front bed for gauge > 1
	'''
	# if gauge > 1:
	# 	if decNeedle % 2 != 0: decNeedle -= 1
	# 	if otherEdgeNeedle % 2 != 0: otherEdgeNeedle -= 1

	# width = abs(decNeedle-otherEdgeNeedle)
	width = abs(decNeedle-otherEdgeNeedle)+1

	if gauge == 2:
		if count == 1: minWidth = 5
		elif count == 2: minWidth = 8
		else: minWidth = 1
		if (count == 1 and width < minWidth) or (count == 2 and width < minWidth): #not enough
			if rearrange:
				k.comment(f'not enough needles, will rearrange')
				if decNeedle-otherEdgeNeedle > 0: #right side
					for n in range(decNeedle-(minWidth-1), otherEdgeNeedle):
						if n % gauge == 0:
							bed = 'f'
							otherBed = 'b'
							rack = -1
						else:
							bed = 'b'
							otherBed = 'f'
							rack = 1
						k.knit('+', f'{bed}{n}', c)
						k.rack(rack)
						k.xfer(f'{bed}{n}', f'{otherBed}{n+1}')
						k.rack(0)
				else:
					for n in range(decNeedle+(minWidth-1), otherEdgeNeedle, -1):
						if n % gauge == 0:
							bed = 'f'
							otherBed = 'b'
							rack = 1
						else:
							bed = 'b'
							otherBed = 'f'
							rack = -1
						k.knit('-', f'{bed}{n}', c)
						k.rack(rack)
						k.xfer(f'{bed}{n}', f'{otherBed}{n-1}')
						k.rack(0)
			return True
		else: return False
	elif gauge == 1: print('\n#TODO: find width and pattern')

	# if (gauge == 2 and width < 6) or (gauge == 1 and width < 2): #not enough needles #TODO: determine if should be width <= 6
	# 	bAdjust = 0
	# 	if gauge > 1: bAdjust = 1

	# 	if decNeedle-otherEdgeNeedle > 0: #right side
	# 		originalFN = decNeedle-(3*gauge)
	# 		originalBN = decNeedle-(3*gauge)+bAdjust
	# 		newFNLoc = decNeedle-(3*gauge)+gauge
	# 		newBNLoc = decNeedle-(3*gauge)+gauge+bAdjust

	# 		k.comment(f'not enough needles, shifting loop on f{originalFN} to f{newFNLoc} and b{originalBN} to b{newBNLoc}')

	# 		for n in range(newBNLoc, originalFN-1, -1):
	# 			if n % gauge == 0: k.knit('-', f'f{n}', c)
	# 		for n in range(originalFN, newBNLoc+1):
	# 			if (n+1) % gauge == 0: k.knit('+', f'b{n}', c)
			
	# 		k.rack(-gauge) #check
	# 		k.xfer(f'f{originalFN}', f'b{newFNLoc}')
	# 		k.rack(gauge)
	# 		k.xfer(f'b{originalBN}', f'f{newBNLoc}')
	# 		k.rack(0)
	# 		k.xfer(f'f{newBNLoc}', f'b{newBNLoc}')
	# 		k.xfer(f'b{newFNLoc}', f'f{newFNLoc}')
	# 		#TODO: maybe knit through them, since they're stacked? probably don't need to, though

	# 	else: #left side
	# 		originalFN = decNeedle+(3*gauge)
	# 		originalBN = decNeedle+(3*gauge)+bAdjust
	# 		newFNLoc = decNeedle+(3*gauge)-gauge
	# 		newBNLoc = decNeedle+(3*gauge)-gauge+bAdjust

	# 		k.comment(f'not enough needles, shifting loop on f{originalFN} to f{newFNLoc} and b{originalBN} to b{newBNLoc}')

	# 		for n in range(newFNLoc, originalBN+1):
	# 			if (n+1) % gauge == 0: k.knit('+', f'b{n}', c)
	# 		for n in range(originalBN, newFNLoc-1, -1):
	# 			if n % gauge == 0: k.knit('-', f'f{n}', c)

	# 		k.rack(gauge)
	# 		k.xfer(f'f{originalFN}', f'b{newFNLoc}')
	# 		k.rack(-gauge)
	# 		k.xfer(f'b{originalBN}', f'f{newBNLoc}')
	# 		k.rack(0)
	# 		k.xfer(f'f{newBNLoc}', f'b{newBNLoc}')
	# 		k.xfer(f'b{newFNLoc}', f'f{newFNLoc}')
	# 		#TODO: maybe knit through them, since they're stacked? probably don't need to, though


def shapeXferDoubleBedHalfGauge(k, xferType, count, edgeNeedle, side='l', c=None):
	'''
	*k in knitout Writer
	*xferType is the type of shaping that's happening - valid values are 'dec' (decreasing) and 'inc' (increasing)
	*count is number of needles to dec
	*edgeNeedle is the edge-most needle being xferred
	*side is side to xfer on

	NOTE: only for dec/xfer inc method, <= 4
	'''
	if edgeNeedle % 2 == 0: #edge needle is on front bed
		if side == 'l':
			edgeNeedleF = edgeNeedle
			edgeNeedleB = edgeNeedle+1
		else:
			edgeNeedleF = edgeNeedle
			edgeNeedleB = edgeNeedle-1
		
		rack1st = -1
		rack2nd = 1
		#variable naming convention based on count == 1
		bed1 = 'f'
		bed2 = 'b'
		needle1 = edgeNeedleF
		needle2 = edgeNeedleB
	else: #edge needle is on back bed
		if side == 'l':
			edgeNeedleB = edgeNeedle
			edgeNeedleF = edgeNeedle+1
		else:
			edgeNeedleB = edgeNeedle
			edgeNeedleF = edgeNeedle-1

		rack1st = 1
		rack2nd = -1
		#variable naming convention based on count == 1
		bed1 = 'b'
		bed2 = 'f'
		needle1 = edgeNeedleB
		needle2 = edgeNeedleF

	if count == 1: #aka 1 loop on one bed, 1 needle
		if (xferType == 'inc' and side == 'l') or (xferType == 'dec' and side == 'r'): #left side inc or right side dec
			k.rack(rack2nd)
			k.xfer(f'{bed1}{needle1}', f'{bed2}{needle2}')
			k.rack(0)

			if xferType == 'dec': return [f'{bed2}{needle2}'], [f'{bed2}{needle2}'] #stacked loops & twisted stitch (twist edge-most needle so it doesn't fall off)
			else: return [f'{bed1}{needle1}'] #empty needle (if inc)
		else: #right side inc or left side dec
			k.rack(rack1st)
			k.xfer(f'{bed1}{needle1}', f'{bed2}{needle2}')
			k.rack(0)

			if xferType == 'dec': return [f'{bed2}{needle2}'], [f'{bed2}{needle2}'] #stacked loops & twisted stitch (twist edge-most needle so it doesn't fall off)
			else: return [f'{bed1}{needle1}'] #empty needle (if inc)
	elif count == 2: #aka 1 loop, 2 needles
		if xferType == 'inc':
			if side == 'l': #left side inc
				k.rack(rack2nd)
				k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1-1}')

				k.rack(rack1st)
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2-1}')
				k.xfer(f'{bed2}{needle2-2}', f'{bed1}{needle2-3}')

				k.rack(rack2nd)
				k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1-1}')

				rack(0)

				return [f'{bed1}{needle1}', f'{bed2}{needle2}'] #twisted stitches
			else: #right side inc
				k.rack(rack1st)
				k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1+1}')

				k.rack(rack2nd)
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2+1}')
				k.xfer(f'{bed2}{needle2+2}', f'{bed1}{needle2+3}')

				k.rack(rack1st)
				k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1+1}')

				rack(0)

				return [f'{bed1}{needle1}', f'{bed2}{needle2}'] #twisted stitches
		else: #dec
			if side == 'l': #left side dec
				k.rack(rack2nd)
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2+1}')
				k.xfer(f'{bed2}{needle2+2}', f'{bed1}{needle2+3}')

				k.rack(rack1st)
				k.xfer(f'{bed1}{needle2+1}', f'{bed2}{needle2+2}')
				k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1+1}')

				k.rack(rack2nd)
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2+1}')

				k.rack(0)
				return [f'{bed2}{needle2+2}', f'{bed1}{needle2+3}'], [f'{bed1}{needle2+1}'] #stacked, twisted
			else: #right side dec
				k.rack(rack1st)
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2-1}')
				k.xfer(f'{bed2}{needle2-2}', f'{bed1}{needle2-3}')

				k.rack(rack2nd)
				k.xfer(f'{bed1}{needle2-1}', f'{bed2}{needle2-2}')
				k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1-1}')

				k.rack(rack1st)
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2-1}')

				k.rack(0)
				return [f'{bed2}{needle2-2}', f'{bed1}{needle2-3}'], [f'{bed1}{needle2-1}'] #stacked, twisted
	elif count == 3 or count == 4: #count == 4
		if xferType == 'inc':
			if side == 'l': #left side inc
				k.rack(rack2nd*2)
				if count == 4: k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1-2}') #skip if 3
				k.xfer(f'{bed1}{needle1+2}', f'{bed2}{needle1}')

				k.rack(rack1st*2)
				if count == 4: k.xfer(f'{bed2}{needle2-3}', f'{bed1}{needle2-5}') #skip if 3
				k.xfer(f'{bed2}{needle2-1}', f'{bed1}{needle2-3}')
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2-2}')
	
				k.rack(rack2nd*2)
				k.xfer(f'{bed1}{needle1-1}', f'{bed2}{needle1-3}')

				k.rack(0)
				if count == 3: return [f'{bed2}{needle2-2}', f'{bed2}{needle2}', f'{bed1}{needle1+2}'] #twisted stitches
				else: return [f'{bed2}{needle2-2}', f'{bed1}{needle1}', f'{bed2}{needle2}', f'{bed1}{needle1+2}']
			else: #right side inc
				k.rack(rack1st*2)
				if count == 4: k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1+2}')
				k.xfer(f'{bed1}{needle1-2}', f'{bed2}{needle1}')

				k.rack(rack2nd*2)
				if count == 4: k.xfer(f'{bed2}{needle2+3}', f'{bed1}{needle2+5}')
				k.xfer(f'{bed2}{needle2+1}', f'{bed1}{needle2+3}')
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2+2}')

				k.rack(rack1st*2)
				k.xfer(f'{bed1}{needle1+1}', f'{bed2}{needle1+3}')

				k.rack(0)
				if count == 3: return [f'{bed2}{needle2+2}', f'{bed2}{needle2}', f'{bed1}{needle1-2}'] #twisted stitches
				else: return [f'{bed2}{needle2+2}', f'{bed1}{needle1}', f'{bed2}{needle2}', f'{bed1}{needle1-2}']
		else: #dec
			if side == 'l': #left side dec
				k.rack(rack1st*2)
				k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1+2}')
				k.xfer(f'{bed1}{needle1+2}', f'{bed2}{needle1+4}')

				k.rack(rack2nd*2)
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2+2}')
				k.xfer(f'{bed2}{needle2+1}', f'{bed1}{needle2+3}')
				if count == 4: k.xfer(f'{bed2}{needle2+2}', f'{bed1}{needle2+4}') #skip if count == 3
				k.xfer(f'{bed2}{needle2+3}', f'{bed1}{needle2+5}')

				if count == 4:
					k.rack(rack1st*2)
					k.xfer(f'{bed1}{needle1+3}', f'{bed2}{needle1+5}')
					k.xfer(f'{bed1}{needle1+5}', f'{bed2}{needle1+7}')
					k.rack(0)
					return [f'{bed1}{needle2+3}', f'{bed2}{needle1+5}', f'{bed1}{needle2+5}', f'{bed2}{needle1+7}'], [f'{bed1}{needle2+3}'] #stacked-loop needles (first one is new edge-most needle) and twisted stitch
				else: #if count == 3
					k.rack(0)
					k.xfer(f'{bed1}{needle1+3}', f'{bed2}{needle1+3}')
					return [f'{bed2}{needle1+3}', f'{bed1}{needle2+3}', f'{bed1}{needle2+5}'], [f'{bed2}{needle1+3}'] #stacked and twisted
			else: #right side dec
				k.rack(rack2nd*2)
				k.xfer(f'{bed1}{needle1}', f'{bed2}{needle1-2}')
				k.xfer(f'{bed1}{needle1-2}', f'{bed2}{needle1-4}')

				k.rack(rack1st*2)
				k.xfer(f'{bed2}{needle2}', f'{bed1}{needle2-2}')
				k.xfer(f'{bed2}{needle2-1}', f'{bed1}{needle2-3}')
				if count == 4: k.xfer(f'{bed2}{needle2-2}', f'{bed1}{needle2-4}') #skip if count == 3
				k.xfer(f'{bed2}{needle2-3}', f'{bed1}{needle2-5}')

				if count == 4:
					k.rack(rack2nd*2)
					k.xfer(f'{bed1}{needle1-3}', f'{bed2}{needle1-5}')
					k.xfer(f'{bed1}{needle1-5}', f'{bed2}{needle1-7}')
					k.rack(0)
					return [f'{bed1}{needle2-3}', f'{bed2}{needle1-5}', f'{bed1}{needle2-5}', f'{bed2}{needle1-7}'], [f'{bed1}{needle2-3}'] #stacked-loop needles (first one is new edge-most needle) and twisted stitch
				else:
					k.rack(0)
					k.xfer(f'{bed1}{needle1-3}', f'{bed2}{needle1-3}')
					return [f'{bed2}{needle1-3}', f'{bed1}{needle2-3}', f'{bed1}{needle2-5}'], [f'{bed2}{needle1-3}']	#stacked and twisted
	# else: print('TODO')
	else:
		# bindNeedle = edgeNeedle

		# bindoff(k, count, bindNeedle, c, side, True, True)
		# return [], []
		print('TODO')
	

def decDoubleBed(k, count, decNeedle, c=None, side='l', gauge=1, emptyNeedles=[]):
	'''
	*k in knitout Writer
	*count is number of needles to dec
	*decNeedle is edge-most needle being decreased (so reference point for increasing)
	*c is carrier (optional, but necessary if dec > 2, so worth including anyway)
	*side is side to dec on
	*gauge is gauge
	*emptyNeedles is an optional list of needles that are not currently holding loops (e.g. if using stitch pattern), so don't waste time xferring them

	returns new edge-needle on given side based on decrease count, so should be called as so (e.g.):
	leftneedle = decDoubleBed(...)
	'''
	stackedLoopNeedles = []
	twistedStitches = []

	decMethod = 'xfer'
	if (count//gauge) > 2: decMethod = 'bindoff'

	if gauge == 1:
		edgeNeedleF = decNeedle
		edgeNeedleB = decNeedle
	else:
		if side == 'l':
			if decNeedle % 2 == 0:
				edgeNeedleF = decNeedle
				edgeNeedleB = decNeedle+1
			else:
				edgeNeedleB = decNeedle
				edgeNeedleF = decNeedle+1
		else:
			if decNeedle % 2 != 0:
				edgeNeedleB = decNeedle
				edgeNeedleF = decNeedle-1
			else:
				edgeNeedleF = decNeedle
				edgeNeedleB = decNeedle-1

	newEdgeNeedle = decNeedle
	if side == 'l':
		newEdgeNeedle += count
		k.comment(f'dec {count} on left ({decNeedle} -> {newEdgeNeedle})')
	else:
		newEdgeNeedle -= count
		k.comment(f'dec {count} on right ({decNeedle} -> {newEdgeNeedle})')

	if decMethod == 'xfer':
		xferSettings(k)

		if gauge == 1:
			if count == 1:
				if len(emptyNeedles): k.stoppingDistance(3.5)
				if side == 'l': #left side
					k.rack(1)
					if f'b{decNeedle}' not in emptyNeedles:
						k.addRollerAdvance(150)
						k.xfer(f'b{decNeedle}', f'f{decNeedle+1}')
					if f'b{decNeedle+1}' not in emptyNeedles:
						k.xfer(f'b{decNeedle+1}', f'f{decNeedle+2}')
					if f'f{decNeedle}' not in emptyNeedles:
						k.rack(-1)
						k.addRollerAdvance(100)
						k.xfer(f'f{decNeedle}', f'b{decNeedle+1}')
				else: #right side
					k.rack(-1)
					if f'b{decNeedle}' not in emptyNeedles:
						k.addRollerAdvance(150)
						k.xfer(f'b{decNeedle}', f'f{decNeedle-1}')
					if f'b{decNeedle-1}' not in emptyNeedles:
						k.xfer(f'b{decNeedle-1}', f'f{decNeedle-2}')
					if f'f{decNeedle}' not in emptyNeedles:
						k.rack(1)
						k.addRollerAdvance(100)
						k.xfer(f'f{decNeedle}', f'b{decNeedle-1}')
				k.rack(0)
				if len(emptyNeedles): k.stoppingDistance(2.5)
			elif count == 2:
				if len(emptyNeedles): k.stoppingDistance(3.5)
				if side == 'l':
					if f'b{decNeedle + 2}' not in emptyNeedles:
						k.addRollerAdvance(100)
						k.xfer(f'b{decNeedle+2}', f'f{decNeedle+2}')
					if f'b{decNeedle + 3}' not in emptyNeedles:
						k.xfer(f'b{decNeedle+3}', f'f{decNeedle+3}')
					k.rack(-1)
					if f'f{decNeedle}' not in emptyNeedles:
						k.addRollerAdvance(150)
						k.xfer(f'f{decNeedle}', f'b{decNeedle+1}')
					if f'f{decNeedle + 1}' not in emptyNeedles:
						k.xfer(f'f{decNeedle+1}', f'b{decNeedle+2}')
					if f'f{decNeedle + 2}' not in emptyNeedles or f'b{decNeedle + 2}' not in emptyNeedles: #note: it is *not* an accident that these needles don't match those referenced below
						k.xfer(f'f{decNeedle+2}', f'b{decNeedle+3}')
					k.rack(1)
					if f'b{decNeedle}' not in emptyNeedles:
						k.addRollerAdvance(100)
						k.xfer(f'b{decNeedle}', f'f{decNeedle+1}')
					if f'b{decNeedle+1}' not in emptyNeedles or f'f{decNeedle}' not in emptyNeedles: #note: it is *not* an accident that these needles don't match those referenced below
						k.xfer(f'b{decNeedle+1}', f'f{decNeedle+2}')
					k.rack(-1)
					if f'b{decNeedle}' not in emptyNeedles: #note: it is *not* an accident that this needle doesn't match those referenced below
						k.addRollerAdvance(50)
						k.xfer(f'f{decNeedle+1}', f'b{decNeedle+2}')
				else:
					if f'b{decNeedle-2}' not in emptyNeedles:
						k.addRollerAdvance(100)
						k.xfer(f'b{decNeedle-2}', f'f{decNeedle-2}')
					if f'b{decNeedle - 3}' not in emptyNeedles:
						k.xfer(f'b{decNeedle-3}', f'f{decNeedle-3}')
					k.rack(1)
					if f'f{decNeedle}' not in emptyNeedles:
						k.addRollerAdvance(150)
						k.xfer(f'f{decNeedle}', f'b{decNeedle-1}')
					if f'f{decNeedle - 1}' not in emptyNeedles:
						k.xfer(f'f{decNeedle-1}', f'b{decNeedle-2}')
					if f'f{decNeedle - 2}' not in emptyNeedles or f'b{decNeedle - 2}' not in emptyNeedles: #note: it is *not* an accident that these needles don't match those referenced below
						k.xfer(f'f{decNeedle-2}', f'b{decNeedle-3}')
					k.rack(-1)
					if f'b{decNeedle}' not in emptyNeedles:
						k.addRollerAdvance(100)
						k.xfer(f'b{decNeedle}', f'f{decNeedle-1}')
					if f'b{decNeedle-1}' not in emptyNeedles or f'f{decNeedle}' not in emptyNeedles: #note: it is *not* an accident that these needles don't match those referenced below
						k.xfer(f'b{decNeedle-1}', f'f{decNeedle-2}')
					k.rack(1)
					if f'b{decNeedle}' not in emptyNeedles: #note: it is *not* an accident that this needle doesn't match those referenced below
						k.addRollerAdvance(50)
						k.xfer(f'f{decNeedle-1}', f'b{decNeedle-2}')
				k.rack(0)
				if len(emptyNeedles): k.stoppingDistance(2.5)
		else:
			if gauge == 2:
				stackedLoopNeedles, twistedStitches = shapeXferDoubleBedHalfGauge(k, 'dec', count, decNeedle, side, c)
			else: print('\n#TODO') #add for other gauges
	else: #dec by more than 2 (or more than 4 if half gauge), bindoff method
		bindNeedle = decNeedle

		bindoff(k, count, bindNeedle, c, side, True, True, emptyNeedles)

	resetSettings(k)
	return newEdgeNeedle, stackedLoopNeedles, twistedStitches


def halfGaugeOpenDec(k, count, decNeedle, c, side='l', emptyNeedles=[]): #max count == 2 (#TODO: figure out what to do about count of 1 [gradual?])
	stackedLoopNeedles = []
	xferSettings(k)

	if side == 'l': #left side dec
		newEdgeNeedle = decNeedle + count
		k.comment(f'open dec {count} on left ({decNeedle} -> {newEdgeNeedle})')
		if decNeedle % 2 == 0: # front bed
			if count == 2: #TODO: test to make sure order not doesn't result in twist
				k.tuck('-', f'b{decNeedle}', c) #new #check
				k.rack(2)
				k.xfer(f'b{decNeedle+1}', f'f{decNeedle+3}')
			k.rack(-2)
			k.xfer(f'f{decNeedle}', f'b{decNeedle+2}')
			k.rack(0)
			k.xfer(f'b{decNeedle+2}', f'f{decNeedle+2}')
			stackedLoopNeedles.append(f'f{decNeedle+2}')
			if count == 2:
				k.xfer(f'f{decNeedle+3}', f'b{decNeedle+3}') #TODO: maybe do this before other rack 0 xfer
				k.drop(f'b{decNeedle}')
				stackedLoopNeedles.append(f'b{decNeedle+3}')
		else: # back bed
			if count == 2: #TODO: test to make sure order not doesn't result in twist
				k.tuck('-', f'f{decNeedle}', c)
				k.rack(-2)
				k.xfer(f'f{decNeedle+1}', f'b{decNeedle+3}')
				# k.miss('+', f'f{decNeedle+3}', c) #new location #check #TODO: maybe k.miss('+', f'f{decNeedle+2}', c) instead #? or k.tuck('+', f'f{decNeedle+4}', c) #?
			k.rack(2)
			k.xfer(f'b{decNeedle}', f'f{decNeedle+2}')
			k.rack(0)
			k.xfer(f'f{decNeedle+2}', f'b{decNeedle+2}')
			stackedLoopNeedles.append(f'b{decNeedle+2}')
			if count == 2:
				k.xfer(f'b{decNeedle+3}', f'f{decNeedle+3}') #TODO: maybe do this before other rack 0 xfer
				# k.miss('-', f'f{decNeedle+2}', c) #new #check #miss carrier back out of the way
				k.drop(f'f{decNeedle}') #new #check
				stackedLoopNeedles.append(f'f{decNeedle+3}')
	else: # right side dec
		newEdgeNeedle = decNeedle - count
		k.comment(f'open dec {count} on right ({decNeedle} -> {newEdgeNeedle})')
		if decNeedle % 2 == 0: # front bed
			if count == 2: #new #TODO: test to make sure order not doesn't result in twist
				k.rack(-2)
				k.xfer(f'b{decNeedle-1}', f'f{decNeedle-3}')
				k.miss('-', f'f{decNeedle-3}', c) #new #check #prevent accidental tuck
			k.rack(2)
			k.xfer(f'f{decNeedle}', f'b{decNeedle-2}')
			k.rack(0)
			k.xfer(f'b{decNeedle-2}', f'f{decNeedle-2}')
			stackedLoopNeedles.append(f'f{decNeedle-2}')
			if count == 2:
				k.xfer(f'f{decNeedle-3}', f'b{decNeedle-3}') #TODO: maybe do this before other rack 0 xfer
				k.miss('+', f'f{decNeedle-2}', c) #new #check #miss carrier back out of the way
				stackedLoopNeedles.append(f'b{decNeedle-3}')
		else:
			if count == 2: #new #TODO: test to make sure order not doesn't result in twist
				k.rack(2)
				k.xfer(f'f{decNeedle-1}', f'b{decNeedle-3}')
				k.miss('-', f'f{decNeedle-3}', c) #new #check #prevent accidental tuck
			k.rack(-2)
			k.xfer(f'b{decNeedle}', f'f{decNeedle-2}')
			k.rack(0)
			k.xfer(f'f{decNeedle-2}', f'b{decNeedle-2}')
			stackedLoopNeedles.append(f'b{decNeedle-2}')
			if count == 2:
				k.xfer(f'b{decNeedle-3}', f'f{decNeedle-3}') #TODO: maybe do this before other rack 0 xfer
				k.miss('+', f'f{decNeedle-2}', c) #new #check #miss carrier back out of the way
				stackedLoopNeedles.append(f'f{decNeedle-3}')

	resetSettings(k)

	return newEdgeNeedle, stackedLoopNeedles
	# return [f'{bed2}{needle2-2}', f'{bed1}{needle2-3}'], [f'{bed1}{needle2-1}'] #stacked, twisted




def incDoubleBed(k, count, edgeNeedle, c, side='l', gauge=1, emptyNeedles=[], incMethod='xfer', splitType='double'):
	'''
	*k in knitout Writer
	*count is number of needles to inc
	*edgeNeedle is *current* edge-most needle before inc occurs (so reference point for increasing)
	*c is carrier
	*side is side to inc on
	*gauge is gauge
	*emptyNeedles is an optional list of needles that are not currently holding loops (e.g. if using stitch pattern), so don't place loops on those
	*incMethod is the chosen method for increasing, options are: 'xfer', 'zig-zag', and 'twist'
	*splitType is *TODO

	returns 1) new edge-needle on given side based on inc count and 2) list of now-empty needles to perform twisted stitches on, so should be called as so (e.g.):
	leftneedle, twistedStitches = incDoubleBed(...)
	'''
	if count > 2: incMethod = 'zig-zag' #default since no code for inc > 2 by xfer #TODO: add split for gauge 2 count 2

	if gauge == 1:
		edgeNeedleF = edgeNeedle
		edgeNeedleB = edgeNeedle
	else:
		if side == 'l': #left side
			if edgeNeedle % 2 == 0:
				edgeNeedleF = edgeNeedle
				edgeNeedleB = edgeNeedle+1
			else:
				edgeNeedleB = edgeNeedle
				edgeNeedleF = edgeNeedle+1
		else: #right side
			if edgeNeedle % 2 != 0:
				edgeNeedleB = edgeNeedle
				edgeNeedleF = edgeNeedle-1
			else:
				edgeNeedleF = edgeNeedle
				edgeNeedleB = edgeNeedle-1

	newEdgeNeedle = edgeNeedle
	if side == 'l': #left side
		if incMethod == 'split' and splitType == 'gradual':
			newEdgeNeedle -= 1
			k.comment(f'inc 1 on left ({edgeNeedle} -> {newEdgeNeedle}) by gradual split')
		else:
			newEdgeNeedle -= count
			k.comment(f'inc {count} on left ({edgeNeedle} -> {newEdgeNeedle}) by {incMethod}')
	else: #right side
		if incMethod == 'split' and splitType == 'gradual':
			newEdgeNeedle += 1
			k.comment(f'inc 1 on right ({edgeNeedle} -> {newEdgeNeedle}) by gradual split')
		else:
			newEdgeNeedle += count
			k.comment(f'inc {count} on right ({edgeNeedle} -> {newEdgeNeedle}) by {incMethod}')

	twistedStitches = []
	if incMethod == 'xfer':
		xferSettings(k)

		if gauge == 1:
			if side == 'r': shift = -1
			else: shift = 1

			if count > 2: #TODO: maybe remove this since no count > 2 for xfer single?
				if f'b{edgeNeedleB}' not in emptyNeedles: twistedStitches.append(f'b{edgeNeedleB}')
				if f'f{edgeNeedleF}' not in emptyNeedles: twistedStitches.append(f'f{edgeNeedleF}')

			if f'b{(edgeNeedleB)-(shift*count)+(shift*gauge)}' not in emptyNeedles: twistedStitches.append(f'b{(edgeNeedleB)-(shift*count)+(shift*gauge)}')
			if f'f{edgeNeedleF-(shift*count)+(shift*gauge)}' not in emptyNeedles: twistedStitches.append(f'f{edgeNeedleF-(shift*count)+(shift*gauge)}')

			if count == 1:
				if side == 'l':
					k.rack(-1)
					if f'b{edgeNeedle}' not in emptyNeedles: k.xfer(f'b{edgeNeedle}', f'f{edgeNeedle-1}')
					k.rack(0)
					k.addRollerAdvance(-100)
					k.miss('+', f'f{edgeNeedle}', c) #ensures order of xfers that is least likely to drop stitches (edge-most needle first)
					k.xfer(f'f{edgeNeedle}', f'b{edgeNeedle}')
					k.xfer(f'f{edgeNeedle-1}', f'b{edgeNeedle-1}')
					k.rack(-1)
					k.xfer(f'b{edgeNeedle}', f'f{edgeNeedle-1}')
				else: #right side
					k.rack(1)
					k.xfer(f'b{edgeNeedle}', f'f{edgeNeedle+1}')
					k.rack(0)
					k.addRollerAdvance(-100)
					k.miss('+', f'f{edgeNeedle}', c)
					k.xfer(f'f{edgeNeedle}', f'b{edgeNeedle}')
					k.xfer(f'f{edgeNeedle-1}', f'b{edgeNeedle-1}')
					k.rack(-1)
					k.xfer(f'b{edgeNeedle}', f'f{edgeNeedle-1}')
			elif count == 2:
				if side == 'l': #left side
					k.rack(-1)
					k.xfer(f'b{edgeNeedle}', f'f{edgeNeedle-1}')
					k.rack(1)
					k.xfer(f'f{edgeNeedle-1}', f'b{edgeNeedle-2}')
					k.xfer(f'f{edgeNeedle+1}', f'b{edgeNeedle}')
					k.rack(0)
					k.xfer(f'b{edgeNeedle-2}', f'f{edgeNeedle-2}')
					k.rack(-1)
					k.xfer(f'b{edgeNeedle}', f'f{edgeNeedle-1}')
					k.rack(0)
					k.xfer(f'b{edgeNeedle+1}', f'f{edgeNeedle+1}')
					k.rack(1)
					k.xfer(f'f{edgeNeedle-1}', f'b{edgeNeedle-2}')
					k.xfer(f'f{edgeNeedle+1}', f'b{edgeNeedle}')
				else: #right side
					k.rack(1)
					k.xfer(f'b{edgeNeedle}', f'f{edgeNeedle+1}')
					k.rack(-1)
					k.xfer(f'f{edgeNeedle+1}', f'b{edgeNeedle+2}') #TODO: determine which order is better
					k.xfer(f'f{edgeNeedle-1}', f'b{edgeNeedle}')
					k.rack(0)
					k.xfer(f'b{edgeNeedle+2}', f'f{edgeNeedle+2}')
					k.rack(1)
					k.xfer(f'b{edgeNeedle}', f'f{edgeNeedle+1}')
					k.rack(0)
					k.xfer(f'b{edgeNeedle-1}', f'f{edgeNeedle-1}')
					k.rack(-1)
					k.xfer(f'f{edgeNeedle-1}', f'b{edgeNeedle}')
					k.xfer(f'f{edgeNeedle+1}', f'b{edgeNeedle+2}')
			k.rack(0)
		else:
			if gauge == 2:
				twistedStitches = shapeXferDoubleBedHalfGauge(k, 'inc', count, edgeNeedle, side, c)
			#TODO: add for other gauges
		resetSettings(k)
	elif incMethod == 'zig-zag':
		k.rack(0.25) #half-rack for knitout (note: could do true half rack for kniterate - 0.5 - but then wouldn't look right in visualizer)
		if side == 'l':
			for x in range(edgeNeedle-1, edgeNeedle-count-1, -1):
				if f'b{x}' not in emptyNeedles: k.knit('-', f'b{x}', c)
				if f'f{x}' not in emptyNeedles: k.knit('-', f'f{x}', c)
		else:
			for x in range(edgeNeedle+1, edgeNeedle+count+1):
				if f'f{x}' not in emptyNeedles: k.knit('+', f'f{x}', c)
				if f'b{x}' not in emptyNeedles: k.knit('+', f'b{x}', c)
		k.rack(0)
	elif incMethod == 'split': #TODO: add stuff for empty needle check
		k.speedNumber(splitSpeedNumber)
		if gauge == 1:
			if side == 'l':
				k.rack(1)
				k.split('+', f'f{edgeNeedle}', f'b{edgeNeedle-1}', c)
				k.rack(0)
				k.split('+', f'b{edgeNeedle-1}', f'f{edgeNeedle-1}', c)
			else:
				k.rack(-1)
				k.split('-', f'f{edgeNeedle}', f'b{edgeNeedle+1}', c)
				k.rack(0)
				k.split('-', f'b{edgeNeedle+1}', f'f{edgeNeedle+1}', c)
		else: # gauge > 1
			if count == 1 or (splitType == 'gradual'):
				if side == 'l':
					if edgeNeedleF < edgeNeedleB: #leftN == edgeN
						k.deleteLastOp(kwd_s=f'knit - f{edgeNeedleF}', breakCondition=lambda op: 'knit + ' in op)
						k.rack(1)
						k.split('-', f'f{edgeNeedleF}', f'b{edgeNeedleB-2}', c)
					else:
						k.deleteLastOp(kwd_s=f'knit - b{edgeNeedleB}', breakCondition=lambda op: 'knit + ' in op)
						k.rack(-1)
						k.split('-', f'b{edgeNeedleB}', f'f{edgeNeedleF-2}', c)
					k.rack(0)
				else:
					if edgeNeedleB > edgeNeedleF: #meaning edgeNeedle % 2 != 0 (aka it's on back bed)
						k.deleteLastOp(kwd_s=f'knit + b{edgeNeedleB}', breakCondition=lambda op: 'knit - ' in op)
						k.rack(1)
						k.split('+', f'b{edgeNeedleB}', f'f{edgeNeedleF+2}', c)
					else: #meaning edgeNeedle % 2 == 0 (aka it's on front bed)
						k.deleteLastOp(kwd_s=f'knit + f{edgeNeedleF}', breakCondition=lambda op: 'knit - ' in op)
						k.rack(-1)
						k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleB+2}', c)
					k.rack(0)
			elif count == 2:
				if side == 'l': #left side
					if splitType == 'xfer': #original split style (includes xfers)
						k.deleteLastOp(kwd_s=f'knit - f{edgeNeedleF}', breakCondition=lambda op: 'knit + ' in op)
						k.deleteLastOp(kwd_s=f'knit - b{edgeNeedleB}', breakCondition=lambda op: 'knit + ' in op)
						if edgeNeedleF > edgeNeedleB: k.split('-', f'f{edgeNeedleF}', f'b{edgeNeedleF}', c)
						k.split('-', f'b{edgeNeedleB}', f'f{edgeNeedleB}', c)
						if edgeNeedleF < edgeNeedleB: k.split('-', f'f{edgeNeedleF}', f'b{edgeNeedleF}', c)

						k.rack(-gauge)
						if edgeNeedleF > edgeNeedleB:
							k.tuck('-', f'f{edgeNeedleF-1}', c)
							k.tuck('-', f'b{edgeNeedleF-2-gauge}', c)

						k.xfer(f'b{edgeNeedleF}', f'f{edgeNeedleF-gauge}')
						if edgeNeedleF > edgeNeedleB:
							k.drop(f'b{edgeNeedleF-2-gauge}')
							k.drop(f'f{edgeNeedleF-1}')

						k.rack(gauge)
						if edgeNeedleF < edgeNeedleB:
							k.tuck('-', f'b{edgeNeedleB-1}', c)
							k.tuck('-', f'f{edgeNeedleB-2-gauge}', c)

						k.xfer(f'f{edgeNeedleB}', f'b{edgeNeedleB-gauge}')

						if edgeNeedleF < edgeNeedleB:
							k.drop(f'f{edgeNeedleB-2-gauge}')
							k.drop(f'b{edgeNeedleB-1}')
						k.rack(0)
					elif splitType == 'double': #split from the split
						if edgeNeedleF < edgeNeedleB: #meaning edgeNeedle % 2 == 0 (aka it's on front bed)
							k.deleteLastOp(kwd_s=f'knit - f{edgeNeedleF}', breakCondition=lambda op: 'knit + ' in op)
							k.rack(1)
							k.split('-', f'f{edgeNeedleF}', f'b{edgeNeedleB-2}', c)
							k.rack(-1)
							k.split('-', f'b{edgeNeedleB-2}', f'f{edgeNeedleF-2}', c)
						else: #meaning edgeNeedle % 2 != 0 (aka it's on back bed)
							k.deleteLastOp(kwd_s=f'knit - b{edgeNeedleB}', breakCondition=lambda op: 'knit + ' in op)
							k.rack(-1)
							k.split('-', f'b{edgeNeedleB}', f'f{edgeNeedleF-2}', c)
							k.rack(1)
							k.split('-', f'f{edgeNeedleB-2}', f'b{edgeNeedleF-2}', c)
						k.rack(0)
					elif splitType == 'knit': #split, knit thru xferred loop, split it again
						if edgeNeedleF < edgeNeedleB:
							k.deleteLastOp(kwd_s=f'knit - f{edgeNeedleF}', breakCondition=lambda op: 'knit + ' in op)
							k.rack(1)
							k.split('-', f'f{edgeNeedleF}', f'b{edgeNeedleB-2}', c)
							k.knit('+', f'b{edgeNeedleB-2}', c) # '+' or '-' #?
							k.rack(-1)
							k.split('-', f'b{edgeNeedleB-2}', f'f{edgeNeedleF-2}', c)
						else:
							k.deleteLastOp(kwd_s=f'knit - b{edgeNeedleB}', breakCondition=lambda op: 'knit + ' in op)
							k.rack(-1)
							k.split('-', f'b{edgeNeedleB}', f'f{edgeNeedleF-2}', c)
							k.knit('+', f'f{edgeNeedleF-2}', c) # '+' or '-' #?
							k.rack(1)
							k.split('-', f'f{edgeNeedleB-2}', f'b{edgeNeedleF-2}', c)
						k.rack(0)
				else: #right side
					if splitType == 'xfer':
						k.deleteLastOp(kwd_s=f'knit + f{edgeNeedleF}', breakCondition=lambda op: 'knit - ' in op)
						k.deleteLastOp(kwd_s=f'knit + b{edgeNeedleB}', breakCondition=lambda op: 'knit - ' in op)
						if edgeNeedleF < edgeNeedleB: k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleF}', c)
						k.split('+', f'b{edgeNeedleB}', f'f{edgeNeedleB}', c)
						if edgeNeedleF > edgeNeedleB: k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleF}', c)

						k.rack(-gauge)
						if edgeNeedleF < edgeNeedleB:
							k.tuck('+', f'f{edgeNeedleB+1}', c)
							k.tuck('+', f'b{edgeNeedleB+2+gauge}', c)
						
						k.xfer(f'f{edgeNeedleB}', f'b{edgeNeedleB+gauge}')

						if edgeNeedleF < edgeNeedleB:
							k.drop(f'b{edgeNeedleB+2+gauge}')
							k.drop(f'f{edgeNeedleB+1}')
						
						k.rack(gauge)
						if edgeNeedleF > edgeNeedleB:
							k.tuck('+', f'b{edgeNeedleF+1}', c)
							k.tuck('+', f'f{edgeNeedleF+2+gauge}', c)

						k.xfer(f'b{edgeNeedleF}', f'f{edgeNeedleF+gauge}')

						if edgeNeedleF > edgeNeedleB:
							k.drop(f'f{edgeNeedleF+2+gauge}')
							k.drop(f'b{edgeNeedleF+1}')
						k.rack(0)
						#TODO: make sure it knits on 1 in from new edgeNeedle in next pass
					elif splitType == 'double':
						if edgeNeedleB > edgeNeedleF: #meaning edgeNeedle % 2 != 0 (aka it's on back bed)
							k.deleteLastOp(kwd_s=f'knit + b{edgeNeedleB}', breakCondition=lambda op: 'knit - ' in op)
							k.rack(1)
							k.split('+', f'b{edgeNeedleB}', f'f{edgeNeedleF+2}', c)
							k.rack(-1)
							k.split('+', f'f{edgeNeedleF+2}', f'b{edgeNeedleB+2}', c)
						else: #meaning edgeNeedle % 2 == 0 (aka it's on front bed)
							k.deleteLastOp(kwd_s=f'knit + f{edgeNeedleF}', breakCondition=lambda op: 'knit - ' in op)
							k.rack(-1)
							k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleB+2}', c)
							k.rack(1)
							k.split('+', f'b{edgeNeedleB+2}', f'f{edgeNeedleF+2}', c)
						k.rack(0)
					elif splitType == 'knit':
						if edgeNeedleB > edgeNeedleF:
							k.deleteLastOp(kwd_s=f'knit + b{edgeNeedleB}', breakCondition=lambda op: 'knit - ' in op)
							k.rack(1)
							k.split('+', f'b{edgeNeedleB}', f'f{edgeNeedleF+2}', c)
							k.knit('-', f'f{edgeNeedleF+2}', c)
							k.rack(-1)
							k.split('+', f'f{edgeNeedleF+2}', f'b{edgeNeedleB+2}', c)
						else:
							k.deleteLastOp(kwd_s=f'knit + f{edgeNeedleF}', breakCondition=lambda op: 'knit - ' in op)
							k.rack(-1)
							k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleB+2}', c)
							k.knit('-', f'b{edgeNeedleB+2}', c)
							k.rack(1)
							k.split('+', f'b{edgeNeedleB+2}', f'f{edgeNeedleF+2}', c)
						k.rack(0)
			elif count > 2:
				print('\n#TODO')

		k.speedNumber(speedNumber)
	else: #just twisted stitches #TODO: ensure this works for gauge > 1
		if side == 'l': #left side
			for n in range(edgeNeedle-1, edgeNeedle-count-1, -1):
				if f'f{n}' not in emptyNeedles and (gauge == 1 or n % gauge == 0): twistedStitches.append(f'f{n}')
				if f'b{n}' not in emptyNeedles and (gauge == 1 or (n+1) % gauge == 0): twistedStitches.append(f'b{n}')
		else: #right side
			for n in range(edgeNeedle+1, edgeNeedle+count+1):
				if f'f{n}' not in emptyNeedles and (gauge == 1 or n % gauge == 0): twistedStitches.append(f'f{n}')
				if f'b{n}' not in emptyNeedles and (gauge == 1 or (n+1) % gauge == 0): twistedStitches.append(f'b{n}')

	return newEdgeNeedle, twistedStitches


#------------------------------
#--- WEIRD / FUN TECHNIQUES ---
#------------------------------

def spiral(k, startN, endN, c, length, sectionWidth=4, sectionHeight=2, bed='f', gauge='1'):
	'''
	*TODO
	*sectionWidth is the number of needles that will be brought in at a time during the shortrowing that creates the spiral
	*sectionHeight is the number of passes that will be knitted after bringing in each new section of needles (NOTE: must be an even number so that [if odd value is passed, will add 1 to it to force even value])
	'''
	k.comment('begin spiral')
	
	lastN = endN

	if endN > startN: #first pass is pos
		dir1 = '+'
		dir2 = '-'
		par = -1

		needleRange1 = range(startN, endN+1)
		needleRange2 = range(endN, startN-1, -1)
	else: #first pass is neg
		dir1 = '-'
		dir2 = '+'
		par = 1

		needleRange1 = range(startN, endN-1, -1)
		needleRange2 = range(endN, startN+1)


	def enoughNeedles(p, lastN): #neg: 1 or 9 #pos: 10 or 2
		if dir1 == '+':
			if lastN >= startN and (lastN-startN)+1 >= sectionWidth: return True
			else: return False
		else:
			if lastN >= endN and (startN-lastN)+1 >= sectionWidth: return True #for odd
			else: return False


	for p in range(0, length):
		k.comment(f'new spiral cycle')
		
		lastN = endN
		while enoughNeedles(p, lastN):
			if dir1 == '+':
				range1 = range(startN, lastN+1)
				range2 = range(lastN, startN-1, -1)
			else:
				range1 = range(startN, lastN-1, -1)
				range2 = range(lastN, startN+1)

			for n in range1:
				k.knit(dir1, f'{bed}{n}', c)
				if n == lastN and lastN != endN: k.tuck(dir1, f'{bed}{n-par}', c) #new
			for n in range2:
				k.knit(dir2, f'{bed}{n}', c)
			
			lastN += (par*sectionWidth)
		

#------------------------------------------------------------------------
#--- IMAGE PROCESSING / KNITTING WITH KNITOUT FOR CACTUS-ESQUE THINGS ---
#------------------------------------------------------------------------

def getColorworkData(imagePath): #assumes prescaled
	#1. Read image data from input path; resize based on gauge
	imgData = Image.open(imagePath).convert('L')
	
	imgData = imgData.resize((round(imgData.width*0.5), imgData.height), Image.NEAREST) #scale down to half the size for width so will work for half gauge

	imgData = imgData.transpose(Image.FLIP_TOP_BOTTOM) #so going from bottom to top

	print(f"\nreading colorwork image from path '{imagePath}'...")

	colCt = int(input(f"How many colors? "))
	if query_yes_no('Would you like to use dithering?'): palDither = Image.FLOYDSTEINBERG
	else: palDither = Image.NONE

	if query_yes_no('Would you like to use a custom palette?'):
		palData = []

		print(f"\nColor values must be either a color name in string form e.g. 'red', or rgb tuple e.g. '255, 0, 0'.")
		for col in range(1, colCt+1):
			color = input(f'Color #{col}: ')
			if ',' in color: palData.append(tuple(map(int, color.split(',')))) #rgb tuple aka '255, 0, 0'
			else: palData.append(ImageColor.getcolor(color, 'P')) #string e.g. 'red'
		
		# palData.extend([(255, 255, 255)]*(256-len(palData)))

		imgData = imgData.convert('RGB')

		imgDataPal = imgData.getcolors()

		palMap = []

		for idx, p in enumerate(palData):
			if p in imgDataPal: palMap.append([p, p])
			else:
				colDists = list(map(lambda x: colorDistance(x[1], p, returnRGBs=True), imgDataPal))

				closestCol = imgDataPal[colDists.index(min([x for x in colDists if x[1] not in palData], key=lambda x: x[0]))][1]

				print(f"\nColor '{p}' not in image, so using closest existing color '{closestCol}' as proxy.")

				palData[idx] = closestCol #replace it with color that's actually in the image
		
		palData.extend([palData[0]]*(256-len(palData)))
		palData = sum([list(x) for x in palData], [])

		pal = Image.new('P', (1, 1))
		pal.putpalette(palData)

		imgData = imgData.quantize(colors=colCt, palette=pal, dither=palDither)
		# imgData = imgData.convert('P', palette=pal, dither=palDither, colors=colCt)
	else: imgData = imgData.convert('P', palette=Image.ADAPTIVE, dither=palDither, colors=colCt) 

	palette = imgData.getcolors() #remove #debug

	main_col = max(palette, key=lambda p: p[0])[1]
	# def get_dominant_color(pil_img):
  #   img = pil_img.copy()
  #   img.convert("RGB")
  #   img.resize((1, 1), resample=0)
  #   dominant_color = img.getpixel((0, 0))
  #   return dominant_color

	# print('palette:', palette) #remove #debug
	
	rows = []

	for r in range(0, imgData.height):
		row = {}
		n = -0.5 #start here
		for x in range(0, imgData.width):
			n += 0.5
			px = imgData.getpixel((x, r))

			if px not in row: row[px] = [] #initiate

			# row[px].append(n)
			row[px].append(float(x)) #new

		rows.append(row)

	return rows, main_col


plaitInfo = {'count': 0, 'assigned': 0, 'f': [], 'b': [], 'lastRows': {}, 'carriers': [], 'carrierPark': {}} #global

def insertStitchPattern(k, stitchPat, needles, passEdgeNs, bed, side='l', c='1'): #now works for colorwork too
	'''
	*k is knitout Writer
	*stitchPat is an object with information pertaining to the stitch pattern section we're inserting
	*needles is a list of the needles that will be knitting the stitch pattern (can be a list with sub-lists if knitting multiple rows)
	*passEdgeNs are the edge-most needles in the current pass as a *whole* (not just the stitch pattern section)
	*bed specifies the needle bed that will knit the stitch pattern — valid values are 'f' (front bed) and 'b' (back bed)
	*side is the we're starting on — valid values are 'l' (left) and 'r' (right)
	*c is the carrier

	- Reads an image (white background, flat blobs of color to indicate a stitch pattern)
	- default stitch pattern is jersey (so if no blob, will treat as jersey)
	'''
	patName = stitchPat.pattern

	if patName == 'interlock': patLength = 0.5
	else: patLength = 1

	patFuncReturns = {'garter': ['side']}

	stitchPatFunc = globals()[patName]


	def get_parameters(func):
		keys = func.__code__.co_varnames[:func.__code__.co_argcount][::-1]
		sorter = {j: i for i, j in enumerate(keys[::-1])} 
		
		params = sorted([i for i in keys], key=sorter.get)
		return params
	

	if stitchPat.info['count'] == 0 and patName == 'rib' and stitchPat.args['secureStartN'] == True:
		seq = stitchPat.args['sequence']
		if type(needles[0]) == list: stNeedles = needles[0].copy()
		else: stNeedles = needles.copy()

		if side == 'l': stStartN = stNeedles[0]
		else: stStartN = stNeedles[-1]

		switchBeds = str.maketrans('fb', 'bf')
		if seq[stStartN % len(seq)] == bed: stitchPat.args['sequence'] = seq.translate(switchBeds)


	def postFuncUpdate(returns, updates): #v
		if returns == None and not len(updates): stitchPat.update(returns)
		else:
			if returns is None:stitchPat.update(updates)
			elif type(returns) == tuple: #multiple return values
				results = {}
				for val in returns:
					results[patFuncReturns[patName][returns.index(val)]] = val
				if len(updates): results.update(updates)

				stitchPat.update(results)
			else:
				results = {patFuncReturns[patName][0]: returns}
				if len(updates): results.update(updates)
				stitchPat.update(results) #one return value
	#--- end postFuncUpdate func ---#^


	plaiting = False
	carrierCondition = 1
	if 'plaitC' in stitchPat.info and stitchPat.info['plaitC'] is not None:
		plaiting = True
		patC = [c, stitchPat.info['plaitC']]
		if (bed == 'f' and stitchPat.info['plaitCside'] == 'r') or (bed == 'b' and stitchPat.info['plaitCside'] == 'l'): carrierCondition = 2
	else: patC = c
		
	if type(needles[0]) == list: #meaning multiple rows
		length = len(needles)


		def startAndEndNs(p):
			if p > 0:
				if 'secureStartN' in stitchPat.args:
					stitchPat.args['secureStartN'], stitchPat.args['secureEndN'] = stitchPat.args['secureEndN'], stitchPat.args['secureStartN']
			if (side == 'l' and p % 2 == 0) or (side == 'r' and p % 2 != 0): return needles[p][0], needles[p][-1]
			else: return needles[p][-1], needles[p][0]
		

		for p in range(0, length):
			if carrierCondition == 1:
				if p < length-1 or (length % 2 == 0): carrier = patC
				else: carrier = c
			else:
				if p > 0: carrier = patC
				else: carrier = c
			postFuncInfo = {}
			startN, endN = startAndEndNs(p)

			if p == (length-1):
				if endN > startN: finalDirection = '+'
				else: finalDirection = '-'

			if type(carrier) == list: plaitInfo['carrierPark'][stitchPat.info['plaitC']] = endN #if knitting with a plaitC in this pass, update it's parked location

			if 'homeBed' in stitchPat.args:
				if p < (length-1):
					if 'patternRows' in stitchPat.args:
						if stitchPat.info['count'] % stitchPat.args['patternRows'] != (stitchPat.args['patternRows']-1): #if not going to reset
							stitchPat.args['homeBed'] = None #so won't xfer back
						elif stitchPat.args['homeBed'] is None:
							stitchPat.args['homeBed'] = bed #reset it
							postFuncInfo = {'currentBed': bed}
					else: #for rib
						stitchPat.args['homeBed'] = None
				elif stitchPat.args['homeBed'] is None:
					stitchPat.args['homeBed'] = bed #reset it back to the actual homeBed
					postFuncInfo = {'currentBed': bed}

			result = stitchPatFunc(k, startN=startN, endN=endN, length=patLength, c=carrier, **stitchPat.args) #keep redefining until end
			postFuncUpdate(result, postFuncInfo)

			if p < length-1:
				k.rollerAdvance(0)
				if endN > startN:
					if endN != passEdgeNs[1]: #rightN, pos pass
						if (bed == 'f' and (endN+1) % 2 == 0) or (bed == 'b' and (endN+1) % 2 != 0): k.tuck('+', f'{bed}{endN+1}', c)
						elif endN+1 != passEdgeNs[1]: k.tuck('+', f'{bed}{endN+2}', c)
					else:
						if bed == 'f':
							otherBed = 'b'
							otherBedEndN = (endN-1 if (endN % 2 == 0) else endN)
						else:
							otherBed = 'f'
							otherBedEndN = (endN if (endN % 2 == 0) else endN-1)
						k.tuck('-', f'{otherBed}{otherBedEndN}', c)
						k.miss('+', f'{bed}{endN}', c)
				elif endN < startN:
					if endN != passEdgeNs[0]: #leftN, posPass
						if (bed == 'f' and (endN-1) % 2 == 0) or (bed == 'b' and (endN-1) % 2 != 0): k.tuck('-', f'{bed}{endN-1}', c)
						elif endN-1 != passEdgeNs[0]: k.tuck('-', f'{bed}{endN-2}', c)
					else:
						if bed == 'f':
							otherBed = 'b'
							otherBedEndN = (endN+1 if (endN % 2 == 0) else endN)
						else:
							otherBed = 'f'
							otherBedEndN = (endN if (endN % 2 == 0) else endN+1)
						k.tuck('+', f'{otherBed}{otherBedEndN}', c)
						k.miss('-', f'{bed}{endN}', c)
				k.rollerAdvance(rollerAdvance)
			else:
				if plaiting: #get it out of way in case of any future tucks that are meant to prevent holes
					if stitchPat.info['plaitCside'] == 'r' and (needles[p][-1] != passEdgeNs[1]) and finalDirection == '+': #TODO: maybe only miss if there's another pass coming directly up?
						k.comment(f'miss plaitC ({stitchPat.info["plaitC"]}) out of way before finishing row')
						k.rollerAdvance(0)
						k.miss('-', f'f{needles[p][-1]-3}', stitchPat.info['plaitC'])
						plaitInfo['carrierPark'][stitchPat.info['plaitC']] = needles[p][-1]-3
						lastMissOp = k.deleteLastOp(kwd_s=['miss', f'{c} {stitchPat.info["plaitC"]}'], breakCondition=lambda op: ';begin ' in op, returnOp=True)
						if lastMissOp:
							lastMissInfo = lastMissOp.split(' ')
							k.miss(lastMissInfo[1], lastMissInfo[2], c)
						k.rollerAdvance(rollerAdvance)
					elif stitchPat.info['plaitCside'] == 'l' and (needles[p][0] != passEdgeNs[0]) and finalDirection == '-':
						k.comment(f'miss plaitC ({stitchPat.info["plaitC"]}) out of way before finishing row')
						k.rollerAdvance(0)
						k.miss('+', f'f{needles[p][0]+3}', stitchPat.info['plaitC'])
						plaitInfo['carrierPark'][stitchPat.info['plaitC']] = needles[p][0]+3
						lastMissOp = k.deleteLastOp(kwd_s=['miss', f'{c} {stitchPat.info["plaitC"]}'], breakCondition=lambda op: ';begin ' in op, returnOp=True)
						if lastMissOp:
							lastMissInfo = lastMissOp.split(' ')
							k.miss(lastMissInfo[1], lastMissInfo[2], c)
						k.rollerAdvance(rollerAdvance)
	else:
		if side == 'l':
			startN = needles[0]
			endN = needles[-1]
		else:
			startN = needles[-1]
			endN = needles[0]

		result = stitchPatFunc(k, startN=startN, endN=endN, length=patLength, c=c, **stitchPat.args)

		postFuncUpdate(result, {})

class StitchPatDetails:
	def __init__(self, pattern, args, info, color):
		self.pattern = pattern
		self.args = args
		self.info = info
		self.color = color


def genericUpdate(self, returns):
	if returns is not None:
		for (key, val) in returns.items():
			if key in self.info: self.info[key] = val
			elif key in self.args: self.args[key] = val
	self.info['count'] += 1


def garterUpdate(self, returns):
	genericUpdate(self, returns)

	if self.args['homeBed'] is None: self.args['currentBed'] = self.args['startBed']

	if self.info['count'] % self.args['patternRows'] == 0:
		if self.args['startBed'] == 'f': self.args['startBed'] = 'b'
		else: self.args['startBed'] = 'f'
	

def interlockUpdate(self, returns): # def interlock(k, startN, endN, length, c, gauge=1, startCondition=1, emptyNeedles=[])
	genericUpdate(self, returns)

	if self.args['startCondition'] == 1: self.args['startCondition'] = 2
	else: self.args['startCondition'] = 1


def ribUpdate(self, returns):
	genericUpdate(self, returns)

	if self.args['homeBed'] is None: self.args['currentBed'] = None


def laceUpdate(self, returns):
	genericUpdate(self, returns)

	self.args['offsetStart'] = self.args['patBeg'] #whatever the previous patBeg was
	self.args['patBeg'] = self.info['count'] % self.args['patternRows']


def jerseyUpdate(self, returns):
	genericUpdate(self, returns)


def getStitchData(k, bed, shapeData, imagePath='graphics/stitch-pat-map.png', stitchPatterns={}, colorArgs={}, gauge=2):
	patDetails = []
	stitchPatColors = []
	

	def get_parameters(func): #v
		alreadyCovered = ['k', 'startN', 'endN', 'length', 'c']
		keys = func.__code__.co_varnames[:func.__code__.co_argcount][::-1]
		sorter = {j: i for i, j in enumerate(keys[::-1])}

		if func.__defaults__ is not None:
			values = func.__defaults__[::-1]
			kwargs = {i: j for i, j in zip(keys, values)}
			if 'homeBed' in kwargs: kwargs['homeBed'] = bed #change default to bed arg passed in main func
			if 'startBed' in kwargs: kwargs['startBed'] = bed #change default to bed arg passed in main func
			if 'originBed' in kwargs: kwargs['originBed'] = bed #will always stay the same
			if 'currentBed' in kwargs: kwargs['currentBed'] = bed #change default to bed arg passed in main func
			if 'gauge' in kwargs: kwargs['gauge'] = gauge #change the default to gauge arg passed in main func
		else: kwargs = None
		
		sorted_args = {i: 'undefined' for i in sorted(keys, key=sorter.get) if i not in alreadyCovered}

		if kwargs is not None:
			for i in sorted_args:
				if i in kwargs: sorted_args[i] = kwargs[i]
		
		return sorted_args
	#--- end get_parameters func ---#^


	for (pattern, color) in stitchPatterns.items():
		params = get_parameters(globals()[pattern])

		if type(color) == list:
			for col in color:
				args = params.copy()
				info = {'count': 0, 'passes': 1}
				if col in colorArgs:
					patArgs = colorArgs[col]
					for arg in patArgs:
						if arg in args: args[arg] = patArgs[arg]
						elif arg == 'length' or arg == 'passes': info['passes'] = patArgs[arg] #TODO: refine this
						elif arg == 'features':
							if 'plaiting' in patArgs[arg]:
								info['plaitC'] = None #would be updated if carrier available
								if bed == 'b': info['plaitCside'] = 'r' #might be reassigned later
								else: info['plaitCside'] = 'l'
			
						elif arg == 'extensions':
							if 'stitchNumber' in patArgs[arg]: info['stitchNumber'] = patArgs[arg]['stitchNumber']
							if 'rollerAdvance' in patArgs[arg]: info['rollerAdvance'] = patArgs[arg]['rollerAdvance']
							if 'speedNumber' in patArgs[arg]: info['speedNumber'] = patArgs[arg]['speedNumber']

				pat = StitchPatDetails(pattern, args, info, col) #new col

				if pat.pattern == 'garter': pat.update = garterUpdate.__get__(pat)
				elif pat.pattern == 'rib': pat.update = ribUpdate.__get__(pat)
				elif pat.pattern == 'interlock': pat.update = interlockUpdate.__get__(pat) #TODO: get this working
				elif pat.pattern == 'lace': pat.update = laceUpdate.__get__(pat) #TODO: get this working
				elif pat.pattern == 'jersey': pat.update = jerseyUpdate.__get__(pat)
				else: print(f'TODO: add support for {pat.pattern}')

				patDetails.append(pat)
				stitchPatColors.append(col)
		else:
			args = params.copy()
			info = {'count': 0, 'passes': 1}
			if color in colorArgs:
				patArgs = colorArgs[color]
				for arg in patArgs:
					if arg in args: args[arg] = patArgs[arg]
					elif arg == 'length' or arg == 'passes': info['passes'] = patArgs[arg] #TODO: refine this
					elif arg == 'features':
							if 'plaiting' in patArgs[arg]:
								info['plaitC'] = None #would be updated if carrier available
								if bed == 'b': info['plaitCside'] = 'r'
								else: info['plaitCside'] = 'l'

			pat = StitchPatDetails(pattern, args, info, color) #new color

			if pat.pattern == 'garter': pat.update = garterUpdate.__get__(pat)
			elif pat.pattern == 'rib': pat.update = ribUpdate.__get__(pat)
			elif pat.pattern == 'interlock': pat.update = interlockUpdate.__get__(pat) #TODO: get this working
			elif pat.pattern == 'lace': pat.update = laceUpdate.__get__(pat) #TODO: get this working
			elif pat.pattern == 'jersey': pat.update = jerseyUpdate.__get__(pat)
			else: print(f'TODO: add support for {pat.pattern}')

			patDetails.append(pat)
			stitchPatColors.append(color)

	# check to see if there are any non-integer values for 'passes' or < 1 values
	jerseyPasses = 1
	if any(pat.info['passes'] < 1 or pat.info['passes'] % 1 != 0 for pat in patDetails):
		print('\nWARNING: scaling up by 2.')
		jerseyPasses = 2 #TODO: make it possible to scale up by more than two
		for pat in patDetails:
			pat.info['passes'] = int(pat.info['passes']*2)
	else:
		for pat in patDetails:
			if 'plaitC' in pat.info and pat.info['passes'] < 2:
				print(f'\nWARNING: changing pass count for a {pat.pattern} section with plaiting from {pat.info["passes"]} to {pat.info["passes"]+1} so plaiting carrier can be consistently parked and retrieved on the same side.')
				pat.info['passes'] += 1
	
	imgData = Image.open(imagePath)

	# check to ensure length and width of stitchPatImg is same as shapeImg
	imgHeight = imgData.height
	imgWidth = imgData.width
	rescale = False
	vertScale = 1
	horizScale = 1

	if imgHeight != shapeData.height:
		vertScale = shapeData.height/imgHeight
		rescale = True
	if imgWidth != shapeData.width:
		horizScale = shapeData.width/imgWidth
		rescale = True
	
	if jerseyPasses > 1:
		horizScale *= jerseyPasses
		rescale = True
	
	if rescale:
		imgData = imgData.resize((round(imgData.width*horizScale), round(imgData.height*vertScale)), Image.NEAREST) #scale image to size of shape img 
		imgHeight = imgData.height
		imgWidth = imgData.width

	imgData = imgData.transpose(Image.FLIP_TOP_BOTTOM) #so going from bottom to top
	
	return imgData, patDetails, stitchPatColors, jerseyPasses


#--- FUNCTION TO PROCESS/ANALYZE IMAGE THAT INDICATES STITCH PATTERN LOCATIONS ON CACTUS ---
def imgToStitchPatternMap(k, imgData, stitchPatColors, stitchPatCount):
	'''
	*k is knitout Writer
	*imgData is the data we got from processing the stitch pattern img in getStitchData func
	*stitchPatColors is the data describing the colors/stitch patterns that the getStitchData func returned
	*stitchPatCount is the total number of stitch patterns used in the piece
	'''

	#------------
	imgHeight = imgData.height
	imgWidth = imgData.width

	palData = []

	for color in stitchPatColors:
		if type(color) == str: palData.append(ImageColor.getcolor(color, 'P'))
		elif type(color) == tuple and len(color) == 3: palData.append(color)
		else: raise ValueError(f"color values in stitchPatterns must be either a color name in string form e.g. 'red', or rgb tuple e.g. (255, 0, 0). Value: {color} is not valid.")

	# im_arr = np.array(imgData)
	# stitchPatColors_arr = np.asarray(stitchPatColors)
	# unique_colors = np.unique(im_arr.reshape(-1, im_arr.shape[-1]), axis=0)
	# intersection = np.array([x for x in set(tuple(x) for x in stitchPatColors_arr) & set(tuple(x) for x in unique_colors)])
	# set_difference = set(tuple(x) for x in stitchPatColors_arr).difference(tuple(x) for x in unique_colors)
	# print(unique_colors.shape, stitchPatColors_arr.shape, intersection.shape)
	# print('set_difference:', set_difference)

	palData.extend([(255, 255, 255)]*(256-len(palData)))
	palData = sum([list(x) for x in palData], [])

	pal = Image.new('P', (1, 1))
	pal.putpalette(palData)

	imgData = imgData.convert('RGB')
	imgData = imgData.quantize(stitchPatCount+1, palette=pal, dither=0)

	palette = imgData.getcolors()

	quantized_colors = [x for count, x in imgData.convert('RGB').getcolors()]

	bg_RGB = next((x for x in quantized_colors if x not in stitchPatColors), None)

	excluded_stitch_pats = list(filter((lambda x: x not in quantized_colors), stitchPatColors))

	if len(excluded_stitch_pats):
		print(f'\nWARNING: the following stitch pattern colors have been excluded: {excluded_stitch_pats}')
		# palette = [(count, idx) for idx, (count, key) in enumerate(palette)]
		# stitchPatDetails = [patDet for patDet in stitchPatDetails if patDet.color not in excluded_stitch_pats]

	if bg_RGB is not None: bg = palette[-1][1] #key for background color (white)
	else: bg = None #no bg

	# if len(palette) == stitchPatCount: bg = None #no bg
	# else: bg = len(palette)-1 #key for background color (white)

	rows = []
	for r in range(0, imgHeight):
		pat = None
		patNs = []
		row = {}
		for x in range(0, imgWidth):
			px = imgData.getpixel((x, r))
			if px != bg:
				if pat is None or px == pat:
					patNs.append(x)
					if x == imgWidth-1:
						row[pat] = patNs #dict with pattern idx and needles
						rows.append(row)
				else:
					row[pat] = patNs #dict with pattern idx and needles
					patNs = []
					patNs.append(x)
					if x == imgWidth-1: rows.append(row)

				pat = px
			else: #background, not stitch pattern
				if not len(patNs) and x < imgWidth-1: continue
				elif len(patNs):
					row[pat] = patNs #dict with pattern idx and needles
					patNs = []
					pat = None

				if x == imgWidth-1:
					rows.append(row)

	return rows


#--- MAIN FUNCTION TO PROCESS/ANALYZE CACTUS-ESQUE IMAGE AND OUTPUT KNITOUT ---
def shapeImgToKnitout(k, imagePath='graphics/knitMap.png', gauge=2, scale=1, maxShortrowCount=1, addBindoff=True, excludeCarriers=[], addBorder=True, stitchPatternsFront={'imgPath': None, 'patterns': {}, 'colorArgs': {}}, stitchPatternsBack={'imgPath': None, 'patterns': {}, 'colorArgs': {}}, colorImgFront=None, colorImgBack=None, incMethod='split', openShaping=False, closedCaston=True, openBindoff=False):
	'''
	*k is knitout Writer
	*imagePath is the path to the image that contains the piece data
	*gauge is gauge
	*scale is an optional parameter to scale the image to a larger or smaller size (NOTE: doesn't actually change the image file itself, just the data extracted from it)
	*maxShortRowCount is the max number of shortrows that will be knit per section at a time (NOTE: might end up being less than max at certain points, depending on if a new section comes up or a section ends etc.)
	*addBindoff is a boolean that indicates whether the piece should be finished will a bindoff or just by dropping
	*excludeCarriers is an optional list of carriers that will not be eligible to use in this piece
	*addBorder is a boolean that indicates whether or not a wasteBorder should be added with tucks across the main piece to secure increases
	*stitchPatternFront is a dictionary containing data about any stitch patterns that will be inserted on the shape on the front bed (detected by processing an image) using the following information (key value pairs in dict):
		- 'imgPath': (default is None; if 'imgPath' is None, the function automatically assumes that no stitch patterns will be used on the front of the piece [even if there are values passed in the dict keys])
		- 'patterns': another dict, with strings indicating the particular stitch pattern as the key (the string should exactly match the name defined for the function that implements that stitch pattern [e.g. 'garter' for garter ... should be that straightforward]) and the color used in the image to denote that stitch pattern as the value. If there are multiple blobs of colors all mapped to a particular stitch pattern, those colors can be stored in a list. Note that the only off-limits color is 'white' and stitch pattern is 'jersey', since white should be the background color of the image and jersey is the default stitch pattern to will be mapped to any white space that overlaps with the shape. To make things easier, it is important that if there is white space slicing all the way through a blob of color at any point, it should be separated into two separate blobs, each with a unique color. Also, note that the color can either be a generic name such as 'red' or 'yellow' (so the color should be the true form of that, e.g. rgb (255, 0, 0) for red and rgb (255, 255, 0) for yellow) or an RGB tuple such as (255, 0, 0) for red or even something more specific like (91, 102, 193) for a dusty lavender.
			- so yeah, here's what that might look like: { 'garter': ['red', 'blue'], 'interlock': 'green', 'rib': ['black', (91, 102, 193), (149, 193, 91)] }
			- as of now, supported stitch patterns are: 'garter', 'interlock', and (very soon!) rib (also jersey, the default)
		- 'colorArgs': a list containing specific information about a particular blob of color in the image, with the color as the key and a sub-dictionary for the information as the value. The information should directly corresponding with a parameter in the function that executes the stitch pattern mapped to the color in 'patterns' (explained above); see the particular stitch pattern function definition for eligible parameter names (which should be the key in the sub-dict) and valid corresponding values (which should be the value in the sub-dict). Note that the key is the color, not the stitch pattern, so that you can specifying different information with different blobs of the same stitch pattern (e.g. 1 row of alternating knit-purl garter for one blob, and 4 for another).
			- that might look something like this: {'red': {'patternRows': 1}, 'blue': {'patternRows': 4}, 'black': {'sequence': '1x1'}}
	*stitchPatternsBack is the same as stitchPatternsFront, except for stitch patterns on the back bed
	*colorImgFront is TODO
	*colorImgBack is TODO
	*incMethod is a string indicating the increasing method that should be used in the piece — valid values are 'split', 'xfer', and 'zig-zag' (NOTE: this might be overridden if a large amount of needles are involved in a particular increase [e.g. automatically zig-zag if > 4 needles in inc])
	*openShaping is TODO
	*closedCaston is a boolean that indicates whether we are using a closed cast-on (True) or open cast-on (False)
	*openBindoff is a boolean that indicates whether we are using an open bindoff (True) or closed bindoff (False)


	- Reads a shape image (black and white) and generates an array of rows containing pixel sub-arrays that either have the value 0 (black - shape) or 255 (white - background)
	- Optionally, also reads/processes a stitch pattern image (well, calls the function 'imgToStitchPattern' to read it)
	- Goes through each row and separates each chunk of black pixels into sections (based on whether there is white space separating sections of black pixels)
	- Goes through rows again and assigns a carrier to each section, allowing for shortrowing; information is stored in 'pieceMap', with lists containing tuples for each section -- e.g. pieceMap[0] = [(1, [1, 2, 3]), (2, [10, 11, 12])] means row 0 uses carrier 1 on needles 1,2,3 and carrier 2 on needles 10,11,12
	- Finally, outputs a 'visualization' (just for, ya know, visualization purposes) with 0 being white space, and knitted mass indicated by carrier number
	'''

	''' TODO:
	[] fix problem where can't start off with shortrowing
	'''
	#1. Read image data from input path; resize based on gauge
	imgData = Image.open(imagePath).convert('L')

	if scale != 1: imgData = imgData.resize((round(imgData.width*scale), round(imgData.height*scale)), Image.NEAREST) #scale image according to passed 'scale' value, if scale != 1
	
	imgData = imgData.transpose(Image.FLIP_TOP_BOTTOM) #so going from bottom to top

	width = imgData.width


	plaitStPatsRows = []
	rawStDataF = None
	stitchPatDataF = None
	stitchPatDetailsF = []
	jerseyPassesF = 1

	rawStDataB = None
	stitchPatDataB = None
	stitchPatDetailsB = []
	jerseyPassesB = 1
	
	if stitchPatternsFront['imgPath'] is not None:
		rawStDataF, stitchPatDetailsF, stitchPatColorsF, jerseyPassesF = getStitchData(k, bed='f', shapeData=imgData, imagePath=stitchPatternsFront['imgPath'], stitchPatterns=stitchPatternsFront['patterns'], colorArgs=stitchPatternsFront['colorArgs'])
	
	if stitchPatternsBack['imgPath'] is not None:
		rawStDataB, stitchPatDetailsB, stitchPatColorsB, jerseyPassesB = getStitchData(k, bed='b', shapeData=imgData, imagePath=stitchPatternsBack['imgPath'], stitchPatterns=stitchPatternsBack['patterns'], colorArgs=stitchPatternsBack['colorArgs'])

	if jerseyPassesF > 1: #TODO: adjust this if add option to scale up jerseyPasses by > 2
		print('\nscaling up shape data to match front bed stitch data.')
		imgData = imgData.resize((round(imgData.width*jerseyPassesF), imgData.height), Image.NEAREST) #scale image to size of shape img
		width = imgData.width
		if rawStDataB is not None and jerseyPassesB == 1: #needs to be scaled horizontally too
			print(f'\nscaling up back bed stitch data horizontally and increasing back bed jersey pass count from {jerseyPassesB} to {jerseyPassesF} so it matches front bed stitch data.')
			jerseyPassesB = jerseyPassesF #so they match
			rawStDataB = rawStDataB.resize((round(rawStDataB.width*jerseyPassesF), (rawStDataB.height*jerseyPassesF)), Image.NEAREST)
	elif jerseyPassesB > 1: #jersey passes for back bed stitch data 
		print('\nscaling up shape data to match back bed stitch data.')
		imgData = imgData.resize((round(imgData.width*jerseyPassesB), imgData.height), Image.NEAREST) #scale image to size of shape img 
		width = imgData.width
		if rawStDataF is not None and jerseyPassesF == 1: #needs to be scaled horizontally too
			print(f'\nscaling up front bed stitch data horizontally and increasing front bed jersey pass count from {jerseyPassesF} to {jerseyPassesB} so it matches back bed stitch data.')
			jerseyPassesF = jerseyPassesB #so they match
			rawStDataF = rawStDataF.resize((round(rawStDataF.width*jerseyPassesB), rawStDataF.height), Image.NEAREST)
	
	if rawStDataF is not None:
		stitchPatDataF = imgToStitchPatternMap(k, imgData=rawStDataF, stitchPatColors=stitchPatColorsF, stitchPatCount=len(stitchPatDetailsF))
		# stitchPatDataF, stitchPatDetailsF = imgToStitchPatternMap(k, imgData=rawStDataF, stitchPatColors=stitchPatColorsF, stitchPatDetails=stitchPatDetailsF) # stitchPatDetailsF might get altered if a color isn't detected

		for idx, stDeets in enumerate(stitchPatDetailsF):
			if 'plaitC' in stDeets.info:
				stIdxRow1 = next((r for r, data in enumerate(stitchPatDataF) if idx in data.keys()), None)
				plaitStPatsRows.append([stIdxRow1, idx, 'f'])
				plaitInfo['f'].append(idx)
				plaitInfo['count'] += 1
		
	if rawStDataB is not None:
		stitchPatDataB = imgToStitchPatternMap(k, imgData=rawStDataB, stitchPatColors=stitchPatColorsB, stitchPatCount=len(stitchPatDetailsB))
		# stitchPatDataB, stitchPatDetailsB = imgToStitchPatternMap(k, imgData=rawStDataB, stitchPatColors=stitchPatColorsB, stitchPatDetails=stitchPatDetailsB)

		for idx, stDeets in enumerate(stitchPatDetailsB):
			if 'plaitC' in stDeets.info:
				stIdxRow1 = next((r for r, data in enumerate(stitchPatDataB) if idx in data.keys()), None)
				stIdxRowLast = next((r for r, data in enumerate(stitchPatDataB) if idx in data.keys()), None)
				plaitStPatsRows.append([stIdxRow1, idx, 'b'])
				plaitInfo['b'].append(idx)
				plaitInfo['count'] += 1
	
	if len(plaitStPatsRows): plaitStPatsRows.sort(key=lambda info: info[0]) #sort by row


	colorworkDataF = None
	colorworkDataB = None

	mainCols = {}

	colorworkPalF = None
	colorworkPalB = None

	if colorImgFront is not None: #TODO: choose main carrier by 
		colorworkDataF, mainCols['f'] = getColorworkData(colorImgFront) #what is going on #TODO
		# stitchPatDetailsF.append(StitchPatDetails('fairisle'))
	if colorImgBack is not None:
		colorworkDataB, mainCols['b'] = getColorworkData(colorImgBack)
		# stitchPatDetailsB.append(StitchPatDetails('fairisle'))


	openDecData = None
	openDecAreas = {} #new
	if type(openShaping) == str: #path to image indicating openShaping areas
		openDecData = Image.open(openShaping).convert('L')

		# if scale != 1: openDecData = openDecData.resize((openDecData.width*scale, openDecData.height*scale), Image.NEAREST) #scale image according to passed 'scale' value, if scale != 1
		if openDecData.height != imgData.height or openDecData.width != imgData.width: #scale image to size of shape img
			print('\nrescaling openDecData to size of shape img.')
			openDecData = openDecData.resize((imgData.width, imgData.height), Image.NEAREST)
			# imgData.show() #remove
	
		openDecData = openDecData.transpose(Image.FLIP_TOP_BOTTOM) #so going from bottom to top
		
		for r in range(0, openDecData.height):
			openDecRow = []
			for x in range(0, openDecData.width):
				px = openDecData.getpixel((x, r))

				if px != 255: openDecRow.append(x) #not white
			
			if len(openDecRow): openDecAreas[r] = openDecRow

		openShaping = True #*	


	carrierCount = 1
	emptyNeedles = []
	takeOutAtEnd = [] #for carriers to take out at end, might be modified as carriers are taken out
	gradualSplit = 1*gauge #split count for when gradual split should be implemented
	maxSplit = 1*gauge #current max split count supported by doubleBedInc func

	if gauge > 1:
		for n in range(0, width):
			if n % gauge == 0: emptyNeedles.append(f'b{n}')
			elif (n-1) % gauge == 0: emptyNeedles.append(f'f{n}')
			else:
				emptyNeedles.append(f'f{n}')
				emptyNeedles.append(f'b{n}')


	class SectionInfo: #class for keeping track of section info
		def __init__(self, c):
			self.c = c #carrier used in section (constant)
			self.leftN = None #changing property based on left-most needle in section, used as reference when deciding which carrier to assign to a given section in the next row (same for rightN below)
			self.rightN = None
			self.row = None #new


	#2. Go through ndarray data and separate it into sections represented by lists containing respective needles (i.e. multiple sections if shortrowing)
	rows = [] #list for storing row-wise section data
	rowsTakenNeedles = []
	rowsEdgeNeedles = []

	maxNeedle = 0 #starts at zero, will be increased
	increasing = False #for now (value will be changed if increasing detected) #v
	leftDec = False
	rightDec = False #^

	castonLeftN = None
	castonRightN = None
	startDrop = []

	imgHeight = imgData.height
	imgWidth = imgData.width

	for r in range(0, imgHeight):
		leftmostN = None

		row = []
		section = []
		rowTakenNeedles = []

		n = -0.5 #start here
		for x in range(0, imgWidth):
			n += 0.5
			px = imgData.getpixel((x, r)) #TODO: have option for pixel than is grey (inc / dec of one needle for gauge 2 [so just front or back; keeping track])

			if px == 0: #black
				if leftmostN is None: leftmostN = n

				section.append(n)
				takenNeedle = int(n*gauge)
				if gauge == 1 or (takenNeedle % gauge == 0):
					rowTakenNeedles.append(f'f{takenNeedle}')
				if gauge == 1 or ((takenNeedle+1) % gauge == 0):
					rowTakenNeedles.append(f'b{takenNeedle}')

				if x == imgWidth - 1:
					row.append(section)

					if r == 0 and castonLeftN is None:
							castonLeftN, castonRightN = convertGauge(gauge, row[0][0], row[-1][len(row[-1])-1])
							if len(row) > 1: #multiple sections at the beginning
								for s in range(0, len(row)-1): # -1 so don't do last section
									sectEnd, sectStart = convertGauge(gauge, row[s][-1], row[s+1][0])
									startDrop.append([sectEnd+1, sectStart-1])

					if len(row) > carrierCount: carrierCount = len(row)

					if r > 0 and r < (imgHeight-1) and len(rows[len(rows)-1]) < len(rows[len(rows)-2]) and len(row) >= len(rows[len(rows)-2]): #if necessary, split prev row [-1] into multiple sections (based on number of sections in prev row to that [-2]) if current carrierCount >= # of sections in [-2]
						minus1Needles = rows[len(rows)-1]
						minus2Needles = rows[len(rows)-2]
						startPt = 1
						for n2 in range(startPt, len(minus2Needles)):
							for n1 in range(0, len(minus1Needles)):
								for i in range(1, len(minus1Needles[n1])):
									if minus2Needles[n2][0] == minus1Needles[n1][i]:
										minus1Needles[n1:n1+1] = minus1Needles[n1][:i], minus1Needles[n1][i:]
										startPt += 1
										break

					if n > maxNeedle: maxNeedle = n
					rowsEdgeNeedles.append(list(convertGauge(gauge=gauge, leftN=leftmostN, rightN=n)))

					rows.append(row)
					rowsTakenNeedles.append(rowTakenNeedles)
			else: #white pix
				if len(section) == 0: continue
				else:
					if section[len(section)-1] > maxNeedle: maxNeedle = section[len(section)-1]

					row.append(section)
					section = []
					newSection = False
					for i in range(x, imgWidth):
						if imgData.getpixel((i, r)) == 0: #black
							x = i
							newSection = True
							break

					if not newSection: #very last section
						# if r == 0: castonLeftN, castonRightN = convertGauge(gauge, row[0][0], row[0][len(row[0])-1])
						if r == 0:
							castonLeftN, castonRightN = convertGauge(gauge, row[0][0], row[-1][len(row[-1])-1])
							if len(row) > 1: #multiple sections at the beginning
								for s in range(0, len(row)-1): # -1 so don't do last section
									sectEnd, sectStart = convertGauge(gauge, row[s][-1], row[s+1][0])
									startDrop.append([sectEnd+1, sectStart-1])

						if len(row) > carrierCount: carrierCount = len(row)

						if r > 0 and r < (imgHeight-1) and len(rows[r-1]) < len(rows[r-2]) and len(row) >= len(rows[r-2]):
							startPt = 1
							minus1Needles = rows[r-1]
							minus2Needles = rows[r-2]
							for n2 in range(startPt, len(minus2Needles)):
								for n1 in range(0, len(minus1Needles)):
									for i in range(1, len(minus1Needles[n1])):
										if minus2Needles[n2][0] == minus1Needles[n1][i]:
											minus1Needles[n1:n1+1] = minus1Needles[n1][:i], minus1Needles[n1][i:]
											startPt += 1
											break
													
						rowsEdgeNeedles.append(list(convertGauge(gauge=gauge, leftN=leftmostN, rightN=row[-1][-1]))) #TODO: determine if still need this

						rows.append(row)
						rowsTakenNeedles.append(rowTakenNeedles)
						break #go to next row
	# -----------------------------

	maxNeedle = convertGauge(gauge, maxNeedle) #convert maxNeedle to gauge
	
	#3. Go through rows data and assign carriers to each section
	sections = [] #list for storing SectionInfo

	carrierOrder = [] #list for storing carrier order, helpful when want a certain carrier to be used e.g. always on left (will change if > 2 sections in piece)

	lowNumCs = 0

	if len(plaitInfo['f']):
		frontPlaitCs = len(plaitInfo['f'])
		backPlaitCs = len(plaitInfo['b'])
		availableCs = 6-carrierCount

		aCs = availableCs

		while lowNumCs < availableCs and aCs > 0:
			if lowNumCs % 2 == 0 or backPlaitCs == 0:
				frontPlaitCs -= 1
				lowNumCs += 1
			else: backPlaitCs -= 1
			aCs -= 1

	for cs in range(1, 7): #initialize sections (but won't add leftN & rightN until later)
		if len(carrierOrder) == carrierCount: break
		cStr = str(cs)
		if cStr in excludeCarriers or cs <= lowNumCs: continue
		else:
			sections.append(SectionInfo(cs))
			carrierOrder.append(cStr) #carrierOrder starts out as just [1, 2, 3]

	mainC = carrierOrder[0]

	availableCarriers = []
	for cs in range(6, 0, -1):
		cStr = str(cs)
		if cStr not in carrierOrder and cStr not in excludeCarriers: availableCarriers.append(cStr)

	wasteC = mainC

	if '5' in availableCarriers: #prioritize 5 as borderC since it seems to work well
		drawC = availableCarriers.pop(availableCarriers.index('5'))
		borderC = drawC
		takeOutAtEnd.append(drawC)
	elif len(availableCarriers):
		borderC = availableCarriers.pop() #it will be 6, since that's what would be left over in this case
		drawC = borderC
		takeOutAtEnd.append(drawC)
	else:
		borderC = None
		drawC = carrierOrder[-1] #whichever carrier comes in last
	
	otherCs = []
	for cs in carrierOrder:
		takeOutAtEnd.append(cs)
		if cs != drawC and cs != wasteC: otherCs.append(cs)

	print('\nmaxNeedle:', maxNeedle) #debug

	pieceMap = [] #list for storing overarching carrier/needles data for rows/sections

	#now finally going through rows

	mainCSection = 0 #might be redefined
	rightCarriers = [] #carriers to the right of main carrier

	firstNeedles = {mainC: [castonLeftN, castonRightN]}

	#for storing first and last rows each carrier appears in
	workingRows = {mainC: [0]}

	wasteWeights = {}
	wasteBoundaryExpansions = {} #TODO: simplify this... the way it is currently handled is kinda messy and confusing, + doesn't work for when multiple sections with simultaneous increasing #*#*#*#*

	colorworkCs = {}

	colorworkRowsF = []
	colorworkRowsB = []

	colorworkTucks = {'f': {}, 'b': {}}

	def replaceColorworkC(oldColRows, newColRows):
		oldColRows = newColRows


	def colorworkOverlap(r, bed, colData, leftN, rightN, c):
		sectData = {}

		if colData is not None:
			overlapSectCt = sum(any(cN <= rightN and cN >= leftN for cN in col_sect) for col_sect in colData[r].values())

			for colKey, colSect in colData[r].items():
				overlapNs = list(filter(lambda cN: cN <= rightN and cN >= leftN, colSect))
				# convert to gauge
				overlapNs = list(map(lambda cN: convertGauge(2, cN), overlapNs))

				# if colSect[0] <= rightN and colSect[-1] >= leftN: #colorwork overlaps
				if len(overlapNs): #colorwork overlaps
					if c not in colorworkCs: colorworkCs[c] = {}

					if colKey not in colorworkCs[c]:
						if colKey == mainCols[bed] or overlapSectCt == 1: #main color or only one section that overlaps
							colorworkCs[c][colKey] = c #use main carrier #TODO: make k == (whatever color is on front and back bed)
						elif len(availableCarriers):
							colorworkCs[c][colKey] = availableCarriers.pop() #new
							otherCs.append(colorworkCs[c][colKey]) #new
							takeOutAtEnd.append(colorworkCs[c][colKey])
						else: colorworkCs[c][colKey] = f'!{colKey}' #no carriers available #TODO: make this {}
						# else: print('\nWARNING: not enough available carriers for colorwork.') #remove #?

					sectData[colorworkCs[c][colKey]] = overlapNs

		return sectData #TODO: make this None if no overlap
	

	for r in range (0, len(rows)):
		rowMap = {}

		taken = [] #not sure if this is really needed, but it's just an extra step to absolutely ensure two sections in one row don't used same carrier

		colRowMapF, colRowMapB = {}, {}
		#loop through sections in row
		for i in reversed(range(0, len(rows[r]))): #go backwards so new carriers are added on left
			leftN = rows[r][i][0] #detect the left and right-most needle in each section for that row
			rightN = rows[r][i][len(rows[r][i]) - 1]

			match = False #bool that is toggled to True if the prev leftN & rightN for a carrier aligns with section (otherwise, use 'unusedC')
			unusedC = None #if above^ stays False, stores index (in reference to 'sections' list) of carrier that hasn't been used in piece yet

			for s in range(0, carrierCount):
				if s in taken: continue

				if sections[s].leftN is None: #leftN & rightN will still be 'None' (see class SectionInfo) if not used in piece yet
					if unusedC is None: unusedC = s #index of unused carrier, if needed
					continue
				
				if (leftN < sections[s].leftN and rightN < sections[s].leftN) or (leftN > sections[s].rightN and rightN > sections[s].rightN): continue #prev leftN & rightN for this carrier doesn't align with leftN & rightN of current section, so continue searching
				else: #it's a match!
					if not leftDec and (sections[s].leftN - leftN) < 0: leftDec = True

					if addBorder and (sections[s].leftN - leftN) > 0: #increase
						#detect if increasing is in the middle (overlapping with existing section) or on the side
						if not any(leftN in sect for sect in rows[r-1]): increasing = True #note: don't have to do if r>0 bc all section `leftN`s would be None at that point #TODO: make sure it detects increasing for in the middle

						if r not in wasteWeights: wasteWeights[r] = dict()
						
						if r - wasteWeightsRowCount > 0: pStart = r - wasteWeightsRowCount
						else: pStart = 0

						wasteRightBoundary = None
						expandBoundaryRow = None
						for p in range(pStart, r): #to make sure wasteWeights aren't knitted on taken needles
							if carrierOrder[s] in pieceMap[p]:
								relevantSection = pieceMap[p][carrierOrder[s]]
								sectionLeftN = relevantSection[0]
								if wasteRightBoundary is None or sectionLeftN <= wasteRightBoundary:
									expandBoundaryRow = None
									wasteRightBoundary = sectionLeftN-1
								elif sectionLeftN-1 > wasteRightBoundary and expandBoundaryRow is None: expandBoundaryRow = p

						if expandBoundaryRow is not None:
							if expandBoundaryRow in wasteBoundaryExpansions: wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, rightN=sections[s].leftN-1)
							else:
								wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, rightN=sections[s].leftN-1)

						wasteWeights[r]['left'] = list(convertGauge(gauge, leftN, wasteRightBoundary))
						if borderC not in firstNeedles: firstNeedles[borderC] = list(convertGauge(gauge, wasteRightBoundary+1, rightN))

					if not rightDec and (rightN - sections[s].rightN) < 0: rightDec = True

					if addBorder and rightN - sections[s].rightN > 0: #increase
						if not any(rightN in sect for sect in rows[r-1]): increasing = True

						if len(wasteWeights) == 0: rightCarriers.append(borderC) #meaning first wasteWeight is on the right
						if r not in wasteWeights: wasteWeights[r] = dict()
						
						if r - wasteWeightsRowCount > 0: pStart = r - wasteWeightsRowCount
						else: pStart = 0

						wasteLeftBoundary = None
						expandBoundaryRow = None
						for p in range(pStart, r): #to make sure wasteWeights aren't knitted on taken needles
							if carrierOrder[s] in pieceMap[p]:
								relevantSection = pieceMap[p][carrierOrder[s]]
								sectionRightN = relevantSection[len(relevantSection)-1]
								if wasteLeftBoundary is None or sectionRightN >= wasteLeftBoundary: # >= #?
									expandBoundaryRow = None
									wasteLeftBoundary = sectionRightN+1
								elif sectionRightN+1 < wasteLeftBoundary and expandBoundaryRow is None: expandBoundaryRow = p
						if expandBoundaryRow is not None:
							if expandBoundaryRow in wasteBoundaryExpansions: wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, leftN=sections[s].rightN+1)
							else:
								wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, leftN=sections[s].rightN+1)

						if wasteLeftBoundary is None:
							wasteLeftBoundary = leftN #new #check
						wasteWeights[r]['right'] = list(convertGauge(gauge, wasteLeftBoundary, rightN))
						if borderC not in firstNeedles: firstNeedles[borderC] = list(convertGauge(gauge, leftN, wasteLeftBoundary-1))

					sections[s].leftN = leftN
					sections[s].rightN = rightN
					sections[s].row = r #update row so know which is last
					newRowSection = {carrierOrder[s]: rows[r][i]}

					colSectF = colorworkOverlap(r, 'f', colorworkDataF, leftN, rightN, carrierOrder[s])
					colSectB = colorworkOverlap(r, 'b', colorworkDataB, leftN, rightN, carrierOrder[s])

					if len(colSectF): colRowMapF[carrierOrder[s]] = colSectF
					if len(colSectB): colRowMapB[carrierOrder[s]] = colSectB

					rowMap = {**newRowSection, **rowMap} #add new section to beginning of rowMap since looping in reverse
					taken.append(s)
					match = True
					break

			if not match: #need to use unusedC and add new carrier for shortrowing
				if carrierOrder[unusedC] != mainC:
					workingRows[carrierOrder[unusedC]] = [r]
					firstNeedles[carrierOrder[unusedC]] = rowsEdgeNeedles[r]
					if leftN > sections[mainCSection].rightN: rightCarriers.append(carrierOrder[unusedC])
					
					if r != 0: #new#*#* #TODO: do this for other side too
						lastRowMapKeys = list(pieceMap[r-1].keys())
						prevSectionEnd = pieceMap[r-1][lastRowMapKeys[len(lastRowMapKeys)-1]] #last needle of last section
						prevSectionEnd = prevSectionEnd[len(prevSectionEnd)-1]						

						if addBorder and rightN -  prevSectionEnd > 0: #increase
							increasing = True #new #check #*

							if len(wasteWeights) == 0: rightCarriers.append(borderC)

							if (r-1) not in wasteWeights: wasteWeights[r-1] = dict() #add wasteWeights in the row before new section
							
							if r-1 - wasteWeightsRowCount > 0: pStart = r-1 - wasteWeightsRowCount
							else: pStart = 0

							wasteLeftBoundary = None
							expandBoundaryRow = None
							for p in range(pStart, r-1): #to make sure wasteWeights aren't knitted on taken needles
								if carrierOrder[s] in pieceMap[p]:
									relevantSection = pieceMap[p][carrierOrder[s]]
									sectionRightN = relevantSection[len(relevantSection)-1]
									if wasteLeftBoundary is None or sectionRightN >= wasteLeftBoundary:
										wasteLeftBoundary = sectionRightN+1
									elif sectionRightN+1 < wasteLeftBoundary and expandBoundaryRow is None: expandBoundaryRow = p
							
							if expandBoundaryRow is not None:
								if expandBoundaryRow in wasteBoundaryExpansions: wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, leftN=sections[s].rightN+1)
								else:
									wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, leftN=sections[s].rightN+1)

							if wasteLeftBoundary is None: wasteLeftBoundary = prevSectionEnd + 1
							wasteWeights[r-1]['right'] = list(convertGauge(gauge, wasteLeftBoundary, rightN))
							if borderC not in firstNeedles: firstNeedles[borderC] = list(convertGauge(gauge, leftN, wasteLeftBoundary-1))

				taken.append(unusedC)
				sections[unusedC].leftN = leftN
				sections[unusedC].rightN = rightN
				newRowSection = {carrierOrder[unusedC]: rows[r][i]}

				colSectF = colorworkOverlap(r, 'f', colorworkDataF, leftN, rightN, carrierOrder[unusedC])
				colSectB = colorworkOverlap(r, 'b', colorworkDataB, leftN, rightN, carrierOrder[unusedC])

				if len(colSectF): colRowMapF[carrierOrder[unusedC]] = colSectF
				if len(colSectB): colRowMapB[carrierOrder[unusedC]] = colSectB

				rowMap = {**newRowSection, **rowMap} #add new section to beginning of rowMap since looping in reverse

		if r > 0 and len(taken) < len(pieceMap[-1]):
			for s in range(0, carrierCount):
				if s not in taken: sections[s].leftN, sections[s].rightN = None, None #reuse the carrier

		pieceMap.append(rowMap)

		if len(colRowMapF): colorworkRowsF.append(colRowMapF)
		if len(colRowMapB): colorworkRowsB.append(colRowMapB)
	# -----------------------

	if addBorder: print(f'\nincreasing is {increasing}') #debug

	if addBorder and not increasing:
		addBorder = False
		print('\ntoggling addBorder to False, since no increasing in piece')

	for sect in sections:
		workingRows[f'{sect.c}'].append(sect.row)

	if addBorder:
		wasteWeightsKeys = list(wasteWeights.keys()) #rows

		firstWasteWeightRow = wasteWeightsKeys[0]
		lastWasteWeightRow = wasteWeightsKeys[len(wasteWeightsKeys)-1]

		if borderC is None:
			for c, cRows in workingRows.items():
				if cRows[0] > lastWasteWeightRow or cRows[1] < firstWasteWeightRow:
					borderC = c
					if cRows[0] > lastWasteWeightRow: cRows[0] = firstWasteWeightRow
					else: cRows[1] = lastWasteWeightRow
					break
		else: workingRows[borderC] = [firstWasteWeightRow, lastWasteWeightRow]
		if borderC is None:
			print("\nWARNING: no carrier available for waste border, so can't do it. 'addBorder' is now False. :(")
			addBorder = False #if still no carrier available, don't add border

	global borderStartLeft
	borderStartLeft = True

	leftMostBorderN = 0 #temp
	rightMostBorderN = maxNeedle

	plaitBeforeBorder = None #for now
	prevBorderInfo = {}

	if len(plaitStPatsRows) > len(availableCarriers) and borderC is not None:
		if not addBorder:
			availableCarriers.append(borderC)
			borderC = None
			if borderC in rightCarriers: rightCarriers.remove(borderC)
		else:
			plaitsBeforeBorder = list(filter(lambda st: st[0] < workingRows[borderC][0], plaitStPatsRows))
			if len(plaitsBeforeBorder):
				if borderC > mainC: beforeBorderBed = 'b'
				else: beforeBorderBed = 'f'
				plaitBeforeBorder = next((st for st in plaitsBeforeBorder if st[-1] == beforeBorderBed), plaitsBeforeBorder[0])
				
			if plaitBeforeBorder is not None:
				print(f'\nadding borderC ({borderC}) back into availableCarriers so it can be used in some plaiting that happens before the border.')
				prevBorderInfo['firstNeedles'] = firstNeedles[borderC].copy()
				prevBorderInfo['workingRows'] = workingRows[borderC].copy()
				if borderC in rightCarriers:
					prevBorderInfo['side'] = 'r'
					rightCarriers.remove(borderC)
				else: prevBorderInfo['side'] = 'l'

	if len(plaitStPatsRows):
		plaitCsF = []
		plaitCsB = []
		if len(availableCarriers) or plaitBeforeBorder is not None:
			# check to make sure the plaiting isn't happening elsewhere
			for st in plaitStPatsRows:
				stRow1, stIdx, stBed = st

				if len(availableCarriers) or plaitBeforeBorder is not None:
					if st == plaitBeforeBorder:
						plaitC = borderC
						plaitBeforeBorder = None
					else:
						if stBed == 'f': plaitC = availableCarriers.pop()
						else: plaitC = availableCarriers.pop(0)
					plaitInfo['assigned'] += 1
					plaitInfo['carriers'].append(plaitC)
					if plaitC not in otherCs and plaitC != drawC: otherCs.append(plaitC)
					if plaitC not in takeOutAtEnd: takeOutAtEnd.append(plaitC)

					if stBed == 'f':
						plaitCsF.append(plaitC)
						stitchPatDetailsF[stIdx].info['plaitC'] = plaitC
						plaitInfo['lastRows'][plaitC] = len(stitchPatDataF)-1 - next((i for i, data in enumerate(reversed(stitchPatDataF)) if stIdx in data.keys()), 0)

						if stRow1 is not None:
							stIdxRow1 = stitchPatDataF[stRow1]
							stIdxLeftN = stIdxRow1[stIdx][0]
							stIdxRightN = stIdxRow1[stIdx][-1]

							firstNeedles[plaitC] = [stIdxLeftN, stIdxRightN]

							stPieceMapRow = pieceMap[stRow1]
							for sect in stPieceMapRow:
								sectLeftN, sectRightN = convertGauge(leftN=stPieceMapRow[sect][0], rightN=stPieceMapRow[sect][-1])
								if stIdxLeftN <= sectRightN and stIdxRightN >= sectLeftN: break #pattern overlaps
							
							foundIt = False
							for stRow in range(plaitInfo['lastRows'][plaitC], 0, -1):
								if foundIt: break
								for sect in pieceMap[stRow]:
									sectRowLeftN, sectRowRightN = convertGauge(leftN=pieceMap[stRow][sect][0], rightN=pieceMap[stRow][sect][-1])
									if stIdxLeftN <= sectRowRightN and stIdxRightN >= sectRowLeftN:
										plaitInfo['lastRows'][plaitC] = stRow
										foundIt = True #pattern overlaps
										break
							
							workingRows[plaitC] = [stRow1, plaitInfo['lastRows'][plaitC]]

							if abs(stIdxRightN-sectRightN) < abs(stIdxLeftN-sectLeftN):
								stitchPatDetailsF[stIdx].info['plaitCside'] = 'r'
								rightCarriers.append(plaitC)
							else: stitchPatDetailsF[stIdx].info['plaitCside'] = 'l'
						else: stitchPatDetailsF[stIdx].info['plaitCside'] = 'l'
					else:
						plaitCsB.append(plaitC)
						stitchPatDetailsB[stIdx].info['plaitC'] = plaitC
						plaitInfo['lastRows'][plaitC] = len(stitchPatDataB)-1 - next((i for i, data in enumerate(reversed(stitchPatDataB)) if stIdx in data.keys()), 0)

						if stRow1 is not None:
							stIdxRow1 = stitchPatDataB[stRow1]
							stIdxLeftN = stIdxRow1[stIdx][0]
							stIdxRightN = stIdxRow1[stIdx][-1]
							firstNeedles[plaitC] = [stIdxLeftN, stIdxRightN]

							stPieceMapRow = pieceMap[stRow1]
							for sect in stPieceMapRow:
								sectLeftN, sectRightN = convertGauge(leftN=stPieceMapRow[sect][0], rightN=stPieceMapRow[sect][-1])
								if stIdxLeftN <= sectRightN and stIdxRightN >= sectLeftN: break #pattern overlaps
							
							foundIt = False
							for stRow in range(plaitInfo['lastRows'][plaitC], 0, -1):
								if foundIt: break
								for sect in pieceMap[stRow]:
									sectRowLeftN, sectRowRightN = convertGauge(leftN=pieceMap[stRow][sect][0], rightN=pieceMap[stRow][sect][-1])
									if stIdxLeftN <= sectRowRightN and stIdxRightN >= sectRowLeftN:
										plaitInfo['lastRows'][plaitC] = stRow
										foundIt = True #pattern overlaps
										break

							workingRows[plaitC] = [stRow1, plaitInfo['lastRows'][plaitC]]

							if abs(stIdxLeftN-sectLeftN) < abs(stIdxRightN-sectRightN):
								stitchPatDetailsB[stIdx].info['plaitCside'] = 'l'
							else:
								stitchPatDetailsB[stIdx].info['plaitCside'] = 'r'
								rightCarriers.append(plaitC)
						else:
							stitchPatDetailsF[stIdx].info['plaitCside'] = 'r'
							rightCarriers.append(plaitC)
				else:
					print('\nneed another carrier for plaiting!') #debug

		if not len(availableCarriers) and plaitInfo['count'] != plaitInfo['assigned']:
			for st in plaitStPatsRows:
				stRow1, stIdx, stBed = st

				overlapC = None
				overlapSide = None
				overlapIdx = None #new
				if stBed == 'b':
					plaitList = plaitCsF
					otherPatDet = stitchPatDetailsF
					otherPatData = stitchPatDataF
					patDet = stitchPatDetailsB
					patData = stitchPatDataB
				else:
					plaitList = plaitCsB
					otherPatDet = stitchPatDetailsB
					otherPatData = stitchPatDataB
					patDet = stitchPatDetailsF
					patData = stitchPatDataF
				
				lastRow = len(patData)-1 - next((i for i, data in enumerate(reversed(patData)) if stIdx in data.keys()), 0)

				for carr, cR in workingRows.items():
					if overlapC is not None: break
					if carr != patDet[stIdx].info['plaitC'] and carr in plaitList and cR[0] <= lastRow and cR[1] >= stRow1: #overlaps
						sI = next((sK for sK, sD in enumerate(otherPatDet) if 'plaitC' in sD.info and sD.info['plaitC'] == carr), None) #TODO: do something if None

						if sI is None: continue
						overlapSect = None
						for sR in range(stRow1, lastRow+1):
							if stIdx in patData[sR] and sI in patData[sR]:
								stIdxLeftN = patData[sR][stIdx][0]
								stIdxRightN = patData[sR][stIdx][-1]
								otherStIdxLeftN = otherPatData[sR][sI][0]
								otherStIdxRightN = otherPatData[sR][sI][-1]
								if stIdxLeftN == otherStIdxLeftN and stIdxRightN == otherStIdxRightN:
									sRkeys = list(pieceMap[sR].keys())

									if otherPatDet[sI].info['plaitCside'] == 'l': #concerned about the left edge needle in the piece
										overlapSide = 'l'
										firstSect = sRkeys[0]

										for pC in sRkeys:
											if stIdxLeftN <= convertGauge(leftN=pieceMap[sR][pC][0]) and (pC == firstSect or stIdxLeftN > convertGauge(rightN=pieceMap[sR][sRkeys[sRkeys.index(pC)-1]][-1])): #pattern goes up to the left edge of the section (or goes past it, meaning the excess would just be cut off), and either it's the first section (so no sections to the left of it), or the pattern doesn't overflow into the previous section
												overlapSect = pC
											elif pC == overlapSect:
												overlapSect = None
												break
									else: #concerned about the right edge needle in the piece
										overlapSide = 'r'
										lastSect = sRkeys[-1]

										for pC in sRkeys:
											if stIdxRightN >= convertGauge(rightN=pieceMap[sR][pC][-1]) and (pC == lastSect or stIdxRightN < convertGauge(leftN=pieceMap[sR][sRkeys[sRkeys.index(pC)+1]][0])): #pattern goes up to the right edge of the section (or goes past it, meaning the excess would just be cut off), and either it's the last section (so no sections to the right of it), or the pattern doesn't overflow into the following section
												overlapSect = pC
											elif pC == overlapSect:
												overlapSect = None
												break

									if overlapSect is None: break
									else:
										overlapC = carr
										overlapIdx = sI
									# else: overlapC = carr

								else: continue

				if overlapC is not None:
					prevPlaitC = patDet[stIdx].info['plaitC']
					if patDet[stIdx].info['plaitC'] is None:
						print(f"\ndidn't have enough carriers to designate to individual plaiting sections, but found a carrier ({overlapC}) that can be used for two plaiting sections on either bed by knitting circularly with it.")
						plaitInfo['assigned'] += 1
					else: # remove it from all of the lists/dicts of carrier data
						# prevPlaitC = patDet[stIdx].info['plaitC']

						# print(f'\nusing carrier {overlapC} for two plaiting sections on either bed instead of also using carrier {prevPlaitC} to reduce carrier count, since we can. will be knitting circularly will {overlapC} for plaiting.')
						# plaitInfo['carriers'].remove(prevPlaitC)
						if prevPlaitC != borderC: # and prevPlaitC != wasteC #?#?#?
							if prevPlaitC == drawC: #use this one instead of overlapC since using it anyway
								otherCs.remove(overlapC)
								takeOutAtEnd.remove(overlapC)
								if overlapC in rightCarriers: rightCarriers.remove(overlapC)
								del workingRows[overlapC]
								del firstNeedles[overlapC]

								availableCarriers.append(overlapC)
								
								# firstNeedles[prevPlaitC] = [0, maxNeedle]
								# if (width+4) < 252:
								# 	firstNeedles[drawC][0] -= 2 #get it a bit more out of the way
								# 	firstNeedles[drawC][1] += 2
								# workingRows[prevPlaitC] = [0] #new #check #?
								# #TODO: maybe add something with rightCarriers #?

							else:
								otherCs.remove(prevPlaitC)
								takeOutAtEnd.remove(prevPlaitC)
								if prevPlaitC in rightCarriers: rightCarriers.remove(prevPlaitC)
								del workingRows[prevPlaitC]
								del firstNeedles[prevPlaitC]

								availableCarriers.append(prevPlaitC)
						else: #switch info back to borderC-based info
							if prevPlaitC == borderC:
								firstNeedles[prevPlaitC] = prevBorderInfo['firstNeedles']
								workingRows[prevPlaitC] = prevBorderInfo['workingRows']
								if prevBorderInfo['side'] == 'r' and prevPlaitC not in rightCarriers: rightCarriers.append(prevPlaitC) #add it back into rightCarriers since just based on behavior of borderC now 
					
					if prevPlaitC == drawC:
						print(f'\nusing carrier {prevPlaitC} for two plaiting sections on either bed instead of also using carrier {overlapC} to reduce carrier count, since we can. will be knitting circularly will {prevPlaitC} for plaiting.')
						plaitInfo['carriers'].remove(overlapC)
						del plaitInfo['lastRows'][overlapC]

						otherPatDet[overlapIdx].info['plaitC'] = prevPlaitC
						otherPatDet[overlapIdx].info['plaitCside'] = patDet[stIdx].info['plaitCside'] #TODO: check
					else:						
						if prevPlaitC is not None:
							print(f'\nusing carrier {overlapC} for two plaiting sections on either bed instead of also using carrier {prevPlaitC} to reduce carrier count, since we can. will be knitting circularly will {overlapC} for plaiting.')
							plaitInfo['carriers'].remove(prevPlaitC)
							del plaitInfo['lastRows'][prevPlaitC]

						patDet[stIdx].info['plaitC'] = overlapC
						patDet[stIdx].info['plaitCside'] = overlapSide

	needAnotherCarrier = False

	print('\nplaiting carriers:', plaitInfo['carriers']) #debug
	if plaitInfo['count'] != plaitInfo['assigned']:
		print(f'\nbefore starting the piece, {plaitInfo["count"]-plaitInfo["assigned"]} more carrier(s) needed for plaiting. Hopefully, some carriers will become available once they are out of use.')
		needAnotherCarrier = True
	else: print('\nthere are enough carriers to successfully knit the piece. yay!')

	leftDropWasteC = None
	rightDropWasteC = None

	if addBorder:
		if borderC != drawC:
			otherCs.append(borderC) #if not draw thread
			takeOutAtEnd.append(borderC)

		if width + 16 <= 252: borderWidthAdd = 8 #if have enough needles available (based on max width of piece), add 8 stitches to each side of waste border
		else: borderWidthAdd = math.floor((252-width)/4)*2 #otherwise, just do max number of extra needles available, split between two sides; round to even number so doesn't change parity of borders

		if not addBindoff: # have carrier on either side 
			if len(availableCarriers) and len(carrierOrder) > 1: #if available carriers and more than one section
				otherDropC = availableCarriers.pop()
				if otherDropC != drawC: otherCs.append(otherDropC) #if not draw thread
				takeOutAtEnd.append(otherDropC)
			else: otherDropC = None

			if 'left' in wasteWeights[lastWasteWeightRow]:
				if 'right' in wasteWeights[lastWasteWeightRow]: #both
					leftIncCarrier = next(c for c in pieceMap[lastWasteWeightRow] if convertGauge(leftN=pieceMap[lastWasteWeightRow][c][0]) == wasteWeights[lastWasteWeightRow]['left'][0])

					rightIncCarrier = next(c for c in pieceMap[lastWasteWeightRow] if convertGauge(rightN=pieceMap[lastWasteWeightRow][c][-1]) == wasteWeights[lastWasteWeightRow]['right'][1])

					lastWastePieceMapKeys = list(pieceMap[lastWasteWeightRow].keys())
					if lastWastePieceMapKeys.index(rightIncCarrier) > lastWastePieceMapKeys.index(leftIncCarrier): #right happens last
						if borderC not in plaitInfo['carriers']: rightDropWasteC = borderC
						leftDropWasteC = otherDropC #might be None
					elif lastWastePieceMapKeys.index(leftIncCarrier) > lastWastePieceMapKeys.index(rightIncCarrier): #left inc happens last (so waste weight ends on left side) 
						if borderC not in plaitInfo['carriers']: leftDropWasteC = borderC
						rightDropWasteC = otherDropC #might be None
					else: #they are equal, so need to find out which one happens last based on dir1 of the carrier
						if leftIncCarrier in rightCarriers: #ends on right, so right happens last
							if borderC not in plaitInfo['carriers']: rightDropWasteC = borderC
							leftDropWasteC = otherDropC #might be None
						else: #ends on left, so left happens last
							if borderC not in plaitInfo['carriers']: leftDropWasteC = borderC
							rightDropWasteC = otherDropC #might be None
				else: #just left (meaning last inc is on left side)
					if borderC not in plaitInfo['carriers']: leftDropWasteC = borderC
					rightDropWasteC = otherDropC #might be None
			else: #just right (meaning last inc is on right side)
				if borderC not in plaitInfo['carriers']: rightDropWasteC = borderC
				leftDropWasteC = otherDropC #might be None

			if rightDropWasteC is not None and rightDropWasteC not in rightCarriers: rightCarriers.append(rightDropWasteC)
		else:
			otherDropC = None
		# -------------------------------------

		leftBorderNs = list(filter(lambda w: 'left' in w, wasteWeights.values()))
		rightBorderNs = list(filter(lambda w: 'right' in w, wasteWeights.values()))

		firstNeedles[borderC] = [leftMostBorderN-borderWidthAdd, rightMostBorderN+borderWidthAdd] #add this so know to miss other carriers out of way here
		if otherDropC is not None: firstNeedles[otherDropC] = firstNeedles[borderC].copy() #to be altered

		if borderC in rightCarriers: borderStartLeft = False
	elif not addBorder and not addBindoff:
		if borderC is not None: #meaning there were leftover carriers
			if borderC == drawC:
				if borderC not in plaitInfo['carriers']: leftDropWasteC = borderC
			elif len(availableCarriers):
				leftDropWasteC = availableCarriers.pop()
			
			if len(carrierOrder) > 1:
				if borderC != drawC:
					if borderC not in plaitInfo['carriers']: rightDropWasteC = borderC
				elif len(availableCarriers): rightDropWasteC = availableCarriers.pop()

			if leftDropWasteC is not None:
				if leftDropWasteC != drawC: otherCs.append(leftDropWasteC)
				takeOutAtEnd.append(leftDropWasteC)
			if rightDropWasteC is not None:
				if rightDropWasteC not in rightCarriers: rightCarriers.append(rightDropWasteC)
				if rightDropWasteC != drawC: otherCs.append(rightDropWasteC)
				takeOutAtEnd.append(rightDropWasteC)

	print('\nCarriers used in main piece:', carrierOrder) #TODO: if not addBorder and addBindoff == True, take borderC out from takeOutAtEnd if not in carrierOrder (and take it out immediately if drawC or wasteC)
	print('\nborderC:', borderC, 'addBorder:', addBorder)
	print('\nleftDropWasteC:', leftDropWasteC, 'rightDropWasteC:', rightDropWasteC) #debug
	if addBorder:
		print('\nfirstWasteWeightRow:', firstWasteWeightRow) #debug
		print('\nwasteWeights:', wasteWeights) #debug #TODO: adjust since no longer includes carrier as key

	print('\navailableCarriers leftover:', availableCarriers) #debug 

	takenOutCarriers = []
	rightReusableCs = []
	reusableCarriers = availableCarriers.copy()

	#5. Add waste section and cast-on

	# alter first needles if they are within another carrier's knitting
	firstNeedlesBefore = firstNeedles.copy()

	for c in reversed(list(firstNeedles.keys())):
		if len(firstNeedlesBefore) == 1: break

		firstNeedlesBefore.popitem()
		leftMostBeforeN = min(firstNeedlesBefore.values(), key=lambda firstNs: firstNs[0])[0]
		rightMostBeforeN = max(firstNeedlesBefore.values(), key=lambda firstNs: firstNs[1])[1]

		if firstNeedles[c][0] > leftMostBeforeN: firstNeedles[c][0] = leftMostBeforeN
		if firstNeedles[c][1] < rightMostBeforeN: firstNeedles[c][1] = rightMostBeforeN

	if ((castonRightN/gauge)-(castonLeftN/gauge)) < 16: catchMaxNeedles = True #TODO: have it be is it is < 4 when divided by carriers length (but >= 16 otherwise), have it treat it as len(carriers)/2 #TODO: try changing this
	else: catchMaxNeedles = False

	wasteRightCarriers = rightCarriers.copy()

	if closedCaston: wasteRightCarriers.append(mainC) #have wasteSection func put main carrier (aka caston carrier) on right, side doing closedTubeCaston, so it will actually end on left (since closedTubeCaston is only one pass)

	if drawC not in firstNeedles: firstNeedles[drawC] = [0, maxNeedle]
	if (width+4) < 252:
		firstNeedles[drawC][0] -= 2 #get it a bit more out of the way
		firstNeedles[drawC][1] += 2
	
	print('\ndrawC:', drawC, 'wasteC:', wasteC, 'otherCs:', otherCs) #debug

	print('\nfirstNeedles:', firstNeedles) #debug
	print('\nworkingRows:', workingRows) #debug

	if len(startDrop) and wasteC not in wasteRightCarriers: wasteRightCarriers.append(wasteC) #since main carrier will start on right sdie

	wasteSection(k=k, leftN=castonLeftN, rightN=castonRightN, closedCaston=closedCaston, wasteC=wasteC, drawC=drawC, otherCs=otherCs, gauge=gauge, endOnRight=wasteRightCarriers, firstNeedles=firstNeedles, catchMaxNeedles=catchMaxNeedles)

	if len(startDrop):
		# for n in range(castonLeftN, startDrop[-1][-1]):
		# 	k.knit('+', f'f{n}', mainC)
		
		# drawThread(k, castonLeftN, castonRightN, drawC, side=drawSide, circular=(not closedCaston), gauge=gauge) #new

		k.comment('dropping unused loops from waste section')
		for sect in startDrop:
			for n in range(sect[0], sect[-1]+1):
				if n % gauge == 0: k.drop(f'f{n}')
				elif (n+1) % gauge == 0: k.drop(f'b{n}')


	if drawC not in carrierOrder and not addBorder and addBindoff:
		borderC = None

		if not openShaping or (not leftDec and not rightDec): #TODO: change this to work with multiple sections #*#*#*
			takeOutAtEnd.remove(drawC)
			k.outcarrier(drawC)
			takenOutCarriers.append(drawC)
		reusableCarriers.append(drawC) #left side

	if closedCaston:
		if len(startDrop):
			for sectC in reversed(pieceMap[0]):
				k.comment(f'caston for carrier {sectC}')
				n1, n2 = convertGauge(gauge, pieceMap[0][sectC][0], pieceMap[0][sectC][-1])
				if sectC in rightCarriers and sectC != mainC:
					tuckDrop = placeCarrier(k, leftN=n1, rightN=None, carrierOpts=[sectC], gauge=gauge)[0]
					closedTubeCaston(k, n1, n2, sectC, gauge) #starts negative, so want carrier to end on right side
				else:
					tuckDrop = placeCarrier(k, leftN=None, rightN=n2, carrierOpts=[sectC], gauge=gauge)[0]
					closedTubeCaston(k, n2, n1, sectC, gauge) #starts positive, so want carrier to end on left side
				
				if len(tuckDrop):
					k.rollerAdvance(0)
					for bn in tuckDrop:
						k.drop(bn)
					k.rollerAdvance(rollerAdvance)
			
			if mainC in rightCarriers:
				k.comment('extra pass to get carrier in correct spot')
				for n in range(startDrop[-1][-1], castonRightN): #get carrier in proper place
					if n % gauge == 0: k.knit('+', f'f{n}', mainC)
		else: closedTubeCaston(k, castonRightN, castonLeftN, mainC, gauge)
	else:
		if len(startDrop):
			for sectC in pieceMap[0]:
				k.comment(f'caston for carrier {sectC}')
				n1, n2 = convertGauge(gauge, pieceMap[0][sectC][0], pieceMap[0][sectC][-1])
				if sectC in rightCarriers or sectC == mainC:
					tuckDrop = placeCarrier(k, leftN=None, rightN=n2, carrierOpts=[sectC], gauge=gauge)[0]
					openTubeCaston(k, n2, n1, sectC, gauge) #starts negative, so want carrier to end on right side
				else:
					tuckDrop = placeCarrier(k, leftN=n1, rightN=None, carrierOpts=[sectC], gauge=gauge)[0]
					openTubeCaston(k, n1, n2, sectC, gauge) #starts positive, so want carrier to end on left side
				
				if len(tuckDrop):
					k.rollerAdvance(0)
					for bn in tuckDrop:
						k.drop(bn)
					k.rollerAdvance(rollerAdvance)

			if mainC not in rightCarriers:
				k.comment('extra pass to get carrier in correct spot')
				for n in range(castonRightN, startDrop[-1][-1], -1): #get carrier in proper place
					if n % gauge == 0: k.knit('-', f'f{n}', mainC)
		else: openTubeCaston(k, castonLeftN, castonRightN, mainC, gauge)

	#5. Convert generated data to knitout; also generate visualization of pieceMap data so can see what it would actually look like (0 == whitespace, other numbers == stitch knit with respective carrier number)
	visualization = [] #list for storing visualization

	#TODO: check what max short row count is that the kniterate can handle

	sectionIdx = 0
	shortrowCount = 0
	cycleEnd = maxShortrowCount
	endPoints = []

	switchDir = {} #TODO: have this reset when carrier is reassigned #*#*#*
	openSide = {}
	bothOpenXtraC = None #^

	for car in carrierOrder:
		switchDir[car] = None
		openSide[car] = None

	global toDrop #?
	toDrop = []

	global takenNeedles
	takenNeedles = []

	# global sanityDrop
	sanityDrop = []
	borderToDrop = []

	# global lastDropR
	lastDropR = len(pieceMap)-1

	# print('\npieceMap:') #remove #debug #v
	# for idx, pm in enumerate(pieceMap):
	# 	print(f'{idx}: {pm}')
	# print('\n') #^

	prevNeedles = {}

	for mapC in pieceMap[0]:
		prevNeedles[mapC] = convertGauge(gauge, pieceMap[0][mapC][0], pieceMap[0][mapC][-1])
	# nextNeedles = {} #new

	wKeys = list(wasteWeights.keys())

	#--- MAIN PART OF FUNCTION ---
	r = 0
	while r < len(pieceMap):
		sectionCount = len(pieceMap[r]) #number of sections in this row #TODO: adjust this for colorwork
		mapKeys = list(pieceMap[r].keys()) #carriers used in this row

		if (r+1) < len(pieceMap)-1 and (sectionCount < len(pieceMap[r+1]) or sectionCount > len(pieceMap[r+1])): sectionCountChangeNext = True #if new section coming up next, or section is ending & no longer exists next
		else: sectionCountChangeNext = False

		if sectionIdx == 0:
			visualization.append([])
			n0 = 0 #for whitespace (just for visualization, not knitout)
		else: n0 = endPoints.pop(0)

		carrier = mapKeys[sectionIdx]
		needles = pieceMap[r][mapKeys[sectionIdx]]

		k.comment(f'row: {r} (section {sectionIdx+1}/{sectionCount})')

		if carrier in rightCarriers: dir1, dir2 = '-', '+' #right side
		else: dir1, dir2 = '+', '-' #left side

		prevLeftN = None
		prevRightN = None
		xferL = 0
		xferR = 0

		global incMid
		incMid = False

		global placementLeft
		placementLeft = False

		twistedStitches = [] #might use later on if increasing

		n1, n2 = convertGauge(gauge, needles[0], needles[len(needles) - 1])


		#analyze stitchPatData (if applicable)
		def findPatterns(data): #v
			patterns = {}
			if data is not None and len(data[r]):
				for pat, patNs in data[r].items():
					patLeftN, patRightN = patNs[0], patNs[-1]

					if patLeftN <= n2 and patRightN >= n1: #pattern overlaps
						overlap = []
						if patLeftN >= n1: overlap.append(patLeftN)
						else: overlap.append(n1)

						if patRightN <= n2: overlap.append(patRightN)
						else: overlap.append(n2)
						patterns[pat] = overlap
			
			sorted_patterns = dict(sorted(patterns.items(), key=lambda item: item[1][0]))

			return sorted_patterns
		#--- end findPatterns func ---#^


		patternsF = findPatterns(stitchPatDataF)
		patternsB = findPatterns(stitchPatDataB)


		placementPass = []

		sectionFinished = False
		if r == len(pieceMap)-1 or (r < len(pieceMap)-1 and carrier not in pieceMap[r+1]): sectionFinished = True #TODO: alter this if ... #?

		finishOff = True
		if sectionFinished and r < len(pieceMap)-1:
			nextRowNeedles = [item for sublist in list(pieceMap[r+1].values()) for item in sublist]

			if (n1/gauge) in nextRowNeedles or (n2/gauge) in nextRowNeedles:
				finishOff = False
				print(f'\nNOTE: at row {r}, not finishing off carrier {carrier}, even though its section is finished, because some (or all) of the loops will be taken over by another carrier.')

		if r > 0 and carrier not in pieceMap[r-1]: #means this is a new section #might need to cast some needles on
			print(f'new section at row {r}, using carrier {carrier}.')
			lastLineC = k.returnLastOp(carrier=carrier, asDict=True)

			tuckDrop = []

			if lastLineC is not None and lastLineC['bn1']['needle'] is not None: #see if we need to place the carrier or change direction
				lastN = lastLineC['bn1']['needle']

				dist_from_n1, dist_from_n2 = abs(lastN-n1), abs(lastN-n2)

				min_dist = min(dist_from_n1, dist_from_n2)

				if dist_from_n1 != dist_from_n2:
					if (dir1 == '-' and min_dist == dist_from_n1) or (dir1 == '+' and min_dist == dist_from_n2):
						print('changing dir1 for new carrier.')
						dir1, dir2 = dir2, dir1
				
				if min_dist > 4:
					tuckDrop = placeCarrier(k, leftN=(n1 if dir1 == '+' else None), rightN=(n2 if dir1 == '-' else None), carrierOpts=[carrier], gauge=gauge)[0]

			if sectionIdx != 0 and sectionIdx != len(mapKeys)-1: #means that it is a new shortrow section that is not on the edge, so need to place carrier in correct spot
				if dir1 == '+': k.miss('+', f'f{n1-1}', carrier)
				else: k.miss('-', f'f{n2+1}', carrier)
				k.pause(f'cut C{carrier}')


			prevRowMapKeys = list(pieceMap[r-1].keys())
			prevRowNeedles = range(convertGauge(gauge=gauge, leftN=pieceMap[r-1][prevRowMapKeys[0]][0]), convertGauge(gauge=gauge, rightN=pieceMap[r-1][prevRowMapKeys[len(prevRowMapKeys)-1]][len(pieceMap[r-1][prevRowMapKeys[len(prevRowMapKeys)-1]])-1]))

			newNeedles = []
			needleRange = range(n1, n2+1)
			if dir1 == '-': needleRange = range(n2, n1-1, -1)
			for n in needleRange:
				if n not in prevRowNeedles: newNeedles.append(n)
			
			if len(newNeedles):
				k.comment('cast-on new needles')

				if openShaping: #TODO: make this based on img too!
					openTubeCaston(k, startN=newNeedles[0], endN=newNeedles[-1], c=carrier, gauge=2) #TODO: make sure this doesn't cause issues if new needles attached to existing section
				else:
					k.rack(0.25)
					for n in range(0, len(newNeedles)):
						if f'f{newNeedles[n]}' not in emptyNeedles: k.knit(dir1, f'f{newNeedles[n]}', carrier)
						if f'b{newNeedles[n]}' not in emptyNeedles: k.knit(dir1, f'b{newNeedles[n]}', carrier)
					k.rack(0)

				dir2 = '-'
				needleRange = range(n2, n1-1, -1)
				if dir1 == '-':
					dir2 = '+'
					needleRange = range(n1, n2+1)

				if not openShaping:
					k.comment('back pass to get carrier on correct side')
					for n in range(len(newNeedles)-1, -1, -1): #back pass to get carrier on correct side
						if f'b{newNeedles[n]}' not in emptyNeedles: k.knit(dir2, f'b{newNeedles[n]}', carrier)
			else:
				prevLeftN = prevRowNeedles[0]
				if prevLeftN < n1: xferL = prevLeftN - n1
			
			if len(tuckDrop):
				k.rollerAdvance(0)
				for bn in tuckDrop:
					k.drop(bn)
				k.rollerAdvance(rollerAdvance)

		if r < len(pieceMap)-1 and len(pieceMap[r+1]) > sectionCount and carrier in pieceMap[r+1]:
			futureMapKeys = list(pieceMap[r+1].keys())
			if sectionIdx == 0 and futureMapKeys.index(carrier) != 0: #means new left shortrow section coming
				futureNewSectionNeedles = pieceMap[r+1][futureMapKeys[0]]
				futureNewSectionRightN = convertGauge(gauge, rightN=futureNewSectionNeedles[len(futureNewSectionNeedles)-1])
				placementPass = [n1, futureNewSectionRightN] #knit up until futureLeftN on back bed #TODO: make sure it misses an extra needle here so not in the way #TODO: maybe plan ahead for future part to make up for extra pass on back bed in left shortrow section? #?

		if r > 0 and carrier in pieceMap[r-1]:
			prevLeftN, prevRightN = convertGauge(gauge, pieceMap[r-1][carrier][0], pieceMap[r-1][carrier][-1])
			prevNeedles[carrier] = [prevLeftN, prevRightN]

			if sectionCount > len(pieceMap[r-1]): #means new section here
				prevMapKeys = list(pieceMap[r-1].keys())

				if sectionIdx > 0 and mapKeys[sectionIdx-1] not in prevMapKeys: #means new left section was added before this section
					prevSectionEnd = convertGauge(gauge, rightN=pieceMap[r][mapKeys[sectionIdx-1]][len(pieceMap[r][mapKeys[sectionIdx-1]])-1])
					if prevLeftN < prevSectionEnd: prevLeftN = prevSectionEnd+1
				if sectionIdx < len(mapKeys)-1 and mapKeys[sectionIdx+1] not in prevMapKeys: #means new right section will be added after this section
					nextSectionStart = convertGauge(gauge, leftN=pieceMap[r][mapKeys[sectionIdx+1]][0])
					if prevRightN > nextSectionStart: prevRightN = nextSectionStart-1

			xferL = prevLeftN - n1 #dec/inc on left side (neg if dec) #*
			xferR = n2 - prevRightN #dec/inc on right side (neg if dec)

			if sectionCount < len(pieceMap[r-1]) and (xferL != 0 or xferR != 0): #a section was previously finished and we might need to change some things
				prevRowMapKeys = list(pieceMap[r-1].keys())

				for pC in prevRowMapKeys:
					if pC == carrier: continue
					elif pC not in mapKeys: #the section that was finished
						finishedSectNs = pieceMap[r-1][pC]

						finishedLeftN, finishedRightN = convertGauge(gauge, finishedSectNs[0], finishedSectNs[len(finishedSectNs) - 1])

						if n1 <= finishedRightN and n2 >= finishedLeftN:
							if prevLeftN > finishedRightN:
								xferL = finishedLeftN-n1 #section is to the left of it
								placementLeft = True
							else:
								prevRightN = finishedRightN #new
								xferR = n2-finishedRightN
								if dir1 == '-': #back pass to place carrier (for now; #TODO: have prev row just knit up until edge)
									k.comment('placement pass')
									for n in range(prevRightN+1, n2+1):
										if (n+1) % gauge == 0: k.knit('+', f'b{n}', carrier) #new
							# xferL = finishedLeftN-n1
							# placementLeft = True
							print('\nNOTE: adjusting for merged tube.')
						#TODO: check if need to add if n2 >= finishedLeftN
						if n2 > finishedRightN and n1 < finishedRightN: incMid = True #increasing in middle
		
		doublePass1 = False
		placeXtraC = False

		openDecSectL, openDecSectR = False, False
		if openShaping and gauge == 2:
			if (not len(openDecAreas) and xferL < 0) or (r in openDecAreas and n1 in openDecAreas[r]): openDecSectL = True
			if (not len(openDecAreas) and xferR < 0) or (r in openDecAreas and n2 in openDecAreas[r]): openDecSectR = True

		if switchDir[carrier] is None: #TODO: deal with this for when multiple shortrow sections
			if openShaping and gauge == 2:
				if openDecSectL: #decreasing; will be open
					openSide[carrier] = 'l' #new
					switchDir[carrier] = True #decreasing
				
				if openDecSectR: #decreasing; will be open
					if openSide[carrier] == 'l': openSide[carrier] = 'both'
					else: openSide[carrier] = 'r'
					switchDir[carrier] = True #decreasing
		else:
			switchDir[carrier] = not switchDir[carrier] #alternate

			# if (openSide[carrier] == 'l' and xferR < 0 and (not len(openDecAreas) or (r in openDecAreas and n2 in openDecAreas[r]))) or (openSide[carrier] == 'r' and xferL < 0 and (not len(openDecAreas) or (r in openDecAreas and n1 in openDecAreas[r]))):
			if (openSide[carrier] == 'l' and ((not len(openDecAreas) and xferR < 0) or (r in openDecAreas and n2 in openDecAreas[r]))) or (openSide[carrier] == 'r' and ((not len(openDecAreas) and xferL < 0) or (r in openDecAreas and n1 in openDecAreas[r]))):
				if len(reusableCarriers):
					bothOpenXtraC = {}
					if len(rightReusableCs): #prioritize carriers no longer in use but not yet taken out (currently parked on right side) --> will knit in neg direction
						carrierFromRight = True
						bothOpenXtraC['carrier'] = rightReusableCs.pop()

						reusableCarriers.remove(bothOpenXtraC['carrier']) #TODO: adjust this for shortrowing too

						if int(bothOpenXtraC['carrier']) < int(carrier): #should be on front bed
							bothOpenXtraC['bed'] = 'f'
						else:
							bothOpenXtraC['bed'] = 'b'
					elif len(takenOutCarriers): #bring in carrier that was taken out, it will knit with pos direction
						carrierFromRight = False

						bothOpenXtraC['carrier'] = takenOutCarriers.pop()
						reusableCarriers.remove(bothOpenXtraC['carrier'])
						k.incarrier(bothOpenXtraC['carrier']) #TODO: see if should do this down there instead

						if int(bothOpenXtraC['carrier']) < int(carrier): #should be on front bed
							bothOpenXtraC['bed'] = 'f'
						else:
							bothOpenXtraC['bed'] = 'b'

						takeOutAtEnd.append(bothOpenXtraC['carrier'])
					else: #not ideal... #but bring in new carrier #TODO: insert yarn in section at beginning / have extra carrier available for this --> knits in pos direction
						carrierFromRight = False

						bothOpenXtraC['carrier'] = reusableCarriers.pop()
						if bothOpenXtraC['carrier'] in availableCarriers: #if in availableCarriers, hasn't been used at all yet
							k.incarrier(bothOpenXtraC['carrier'])
							takeOutAtEnd.append(bothOpenXtraC['carrier'])

						if int(bothOpenXtraC['carrier']) < int(carrier): #should be on front bed
							bothOpenXtraC['bed'] = 'f'
						else:
							bothOpenXtraC['bed'] = 'b'
					
					if bothOpenXtraC['bed'] == 'f':
						if (dir1 == '+' and not switchDir[carrier]) or (dir1 == '-' and switchDir[carrier]): switchDir[carrier] = not switchDir[carrier] #since main carrier would have ended up on: 1) [dir1 == '+'] left side (aka most recently a neg pass), so need to make sure it has a positive pass this time or 2) [dir1 == '-'] right side (aka most recently a pos pass), so need to make sure it has a neg pass this time #check
						if (carrierFromRight and not switchDir[carrier]) or (not carrierFromRight and switchDir[carrier]): placeXtraC = True
					elif bothOpenXtraC['bed'] == 'b':
						if (dir1 == '+' and switchDir[carrier]) or (dir1 == '-' and not switchDir[carrier]): switchDir[carrier] = not switchDir[carrier] #new

						if (carrierFromRight and switchDir[carrier]) or (not carrierFromRight and not switchDir[carrier]): placeXtraC = True

					openSide[carrier] = 'both' #new

					if carrier in rightCarriers: rightCarriers.remove(carrier) #switch it so dir1 will be '+' from now on
					else: rightCarriers.append(carrier) # '-' from now on
				else: print(f"WARNING: can't have both sides be open since no reusable carriers. Sticking with open side {openSide}")
			elif openSide[carrier] == 'both':
				if xferR < 0 and len(openDecAreas) and r in openDecAreas and n2 not in openDecAreas[r]: openSide[carrier] = 'l' #new # if (openSide[carrier] == 'l' and xferR < 0 and (not len(openDecAreas) or (r in openDecAreas and n2 in openDecAreas[r]))) or (openSide[carrier] == 'r' and xferL < 0 and (not len(openDecAreas) or (r in openDecAreas and n1 in openDecAreas[r]))):
				if xferL < 0 and len(openDecAreas) and r in openDecAreas and n1 not in openDecAreas[r]:
					if openSide[carrier] == 'both': openSide[carrier] = 'r'
					else: openSide[carrier] = None #if also detected above that no longer open on right

		if switchDir[carrier]:
			if carrier in rightCarriers and openSide[carrier] == 'l': #add extra pass to get it to correct side + take it out of rightCarriers #TODO: figure out if need to update stuff for plaiting then
				print(f'Double pass for carrier {carrier} since the left side is open and it is moving out of rightCarriers') #new #debug
				rightCarriers.remove(carrier)
				doublePass1 = True
			elif carrier not in rightCarriers and openSide[carrier] == 'r':
				print(f'Double pass for carrier {carrier} since the right side is open and it is moving into rightCarriers') #new #debug
				rightCarriers.append(carrier)
				doublePass1 = True

		if addBorder: dropBorderKnits = (r==lastWasteWeightRow)

		if addBorder and sectionIdx == 0 and r in wKeys: #first section of the row
			k.comment(f'insert border for row {r}') #remove #?

			if r == lastWasteWeightRow:
				nextIncRow = r+1 #just knit one more row if about to drop waste border
			else:
				nextIncRow = wKeys[wKeys.index(r)+1]

				if (nextIncRow-r) > maxShortrowCount:
					dropBorderKnits = True #if big gap btw inc
					nextIncRow = r+maxShortrowCount

			takenNeedles = [] # reset

			finishedCs = [mapC for mapC in prevNeedles if mapC not in mapKeys]
			overlap_cs = []

			if len(finishedCs):
				for mapC in finishedCs:
					overlap_c = next((x for x in pieceMap[r] if prevNeedles[mapC][0] in pieceMap[r][x] or prevNeedles[mapC][-1] in pieceMap[r][x]), None)

					if overlap_c is not None:
						overlap_cs.append(overlap_c)
						takenNeedles.append(range(convertGauge(gauge, leftN=pieceMap[r][overlap_c][0]), convertGauge(gauge, rightN=pieceMap[r][overlap_c][-1])+1))

			for mapC in mapKeys:
				if mapC not in overlap_cs:
					if mapC in prevNeedles:
						takenNeedles.append(range(prevNeedles[mapC][0], prevNeedles[mapC][-1]+1)) #base it off of prev needles, so can increase over the border loops for security or not yet knit in space that will open up if decreasing
					else: takenNeedles.append([]) #empty list

			if borderStartLeft:
				wasteStartN = leftMostBorderN-borderWidthAdd
				wasteEndN = rightMostBorderN+borderWidthAdd
			else:
				wasteStartN = rightMostBorderN+borderWidthAdd
				wasteEndN = leftMostBorderN-borderWidthAdd		

			borderToDrop = wasteBorder(k, startN=wasteStartN, endN=wasteEndN, rows=nextIncRow-r, c=borderC, gauge=gauge, offLimits=takenNeedles, lastTime=dropBorderKnits, justTuck=False)

			borderStartLeft = not borderStartLeft #new #*			

		prevNeedles[carrier] = [n1, n2] #new #*

		if len(takenNeedles):
			if sectionIdx < len(takenNeedles): takenNeedles[sectionIdx] = range(n1, n2+1) #new #alter so based on inc/dec if adding border for tuck-over-split
			else: takenNeedles.append(range(n1, n2+1))

		bedCarriers = {'f': carrier, 'b': carrier} #default
		# if switchDir:
		if switchDir[carrier]:
			negBed = 'f'
			posBed = 'b'
			negBedCondition = lambda n: (n % gauge == 0)
			posBedCondition = lambda n: (n % gauge != 0 or gauge == 1)
		else:
			negBed = 'b'
			posBed = 'f'
			negBedCondition = lambda n: (n % gauge != 0 or gauge == 1)
			posBedCondition = lambda n: (n % gauge == 0)
		
		if bothOpenXtraC is not None: bedCarriers[bothOpenXtraC['bed']] = bothOpenXtraC['carrier']


		def leftShaping(leftC): #called from posBedPass func and happens *before* pos pass #v
			toDrop = []

			if xferL:
				if xferL > 0: #increase
					global borderStartLeft

					carrierOnLeft = borderStartLeft
					droppedTucks = False
					borderMissN = None

					nextTuckNs = []
							
					if xferL == gradualSplit: splitType = 'gradual'
					else: splitType = 'double'

					newLeftN, twistedLeft = incDoubleBed(k, count=xferL, edgeNeedle=prevLeftN, c=leftC, side='l', gauge=gauge, emptyNeedles=emptyNeedles, incMethod=incMethod, splitType=splitType)
					twistedStitches.extend(twistedLeft)

					if incMethod == 'split' and addBorder and xferL == gradualSplit: #since no split for > maxSplit yet
						if newLeftN % 2 == 0: k.knit('+', f'f{newLeftN}', leftC)
						else: k.knit('+', f'b{newLeftN}', leftC)

						if not borderStartLeft: #waste border carrier is currently parked on right side; get carrier to left side so can tuck over split
							tuckBorderToDrop = wasteBorder(k, startN=rightMostBorderN+borderWidthAdd, endN=newLeftN+1, rows=0, c=borderC, gauge=gauge, offLimits=takenNeedles, lastTime=False, justTuck=True, missN=newLeftN) #TODO: deal with lastTime #TODO
							toDrop.extend(tuckBorderToDrop)

							borderStartLeft = not borderStartLeft
						else:
							tuckBorderToDrop = wasteBorder(k, startN=leftMostBorderN-borderWidthAdd, endN=newLeftN, rows=0, c=borderC, gauge=gauge, offLimits=takenNeedles, lastTime=False, justTuck=True, missN=newLeftN) #TODO: deal with lastTime #TODO
							toDrop.extend(tuckBorderToDrop)

							# interlock(k, startN=leftMostBorderN-borderWidthAdd, endN=newLeftN-1, length=0.5, c=borderC, gauge=gauge, emptyNeedles=takenNeedles)

						if borderMissN is None: borderMissN = leftMostBorderN-4

						k.comment('tuck over split') #remove #?
						tuckOverDrop = k.tuckOverSplit(borderC, '+') #NOTE: currently has roller advance same as main... change?
						toDrop.extend(tuckOverDrop)

						tuckBorderToDrop = wasteBorder(k, startN=newLeftN-1, endN=leftMostBorderN-borderWidthAdd, rows=0, c=borderC, gauge=gauge, offLimits=takenNeedles, lastTime=False, justTuck=True, missN=leftMostBorderN-borderWidthAdd-1) #TODO: deal with lastTime #TODO
						toDrop.extend(tuckBorderToDrop)

						# interlock(k, startN=newLeftN-1, endN=leftMostBorderN-borderWidthAdd, length=0.5, c=borderC, gauge=gauge, emptyNeedles=takenNeedles)

						newLeftN, twistedLeft = incDoubleBed(k, count=xferL, edgeNeedle=newLeftN, c=leftC, side='l', gauge=gauge, incMethod='split', splitType='gradual')
						twistedStitches.extend(twistedLeft)

						borderStartLeft = True

					return toDrop
				else: #decrease
					if openDecSectL: #pos bed # posBedCondition(prevLeftN)
						if abs(xferL) <= 2: newLeftN, stackedLoopNeedles = halfGaugeOpenDec(k, abs(xferL), prevLeftN, leftC, 'l', emptyNeedles)
						else:
							if posBedCondition(prevLeftN): #force it to bindoff on the pos bed
								leftBindCt = abs(xferL)
								leftBindN = prevLeftN
							else:
								leftBindCt = abs(xferL)-1
								leftBindN = prevLeftN+1
								
							halfGaugeOpenBindoff(k, leftBindCt, leftBindN, leftC, 'l', asDecMethod=True) #TODO: test / check this (and add tucks)

							if openSide[carrier] == 'both' and dir1 == '-': #do this now because it was skipped otherwise #new #check #TODO: check if this should not just be if openSide == 'both'
								if posBedCondition(prevLeftN): #force it to bindoff on the neg bed
									leftBindCt = abs(xferL)-1
									leftBindN = prevLeftN+1
								else:
									leftBindCt = abs(xferL)
									leftBindN = prevLeftN

								halfGaugeOpenBindoff(k, leftBindCt, leftBindN, bedCarriers[negBed], 'l', asDecMethod=True, xtraSecure=True)
							
							newLeftN = prevLeftN + abs(xferL)					
					else:
						newLeftN, stackedLoopNeedles, twistedLeft = decDoubleBed(k, abs(xferL), prevLeftN, carrier, 'l', gauge, emptyNeedles)
						
						if len(twistedLeft) and dir1 == '+': twistedLeft = list(filter(lambda bn: bn[:1] == posBed, twistedLeft)) #because otherwise, will drop it

						twistedStitches.extend(twistedLeft)

					if dir1 == '-': #rightShaping happened first
						if xferL == -1 or xferL == -2: notEnoughNeedlesDecCheck(k, decNeedle=prevLeftN, otherEdgeNeedle=n2, count=abs(xferL), c=carrier, gauge=gauge)
					else:
						if xferL == -2 and abs(prevLeftN-(n2-1)) < 8 and xferR < 0: #TODO: #check if it applies for dec by 1 on either side, dec by > 3 on R, and inc (by xfer, ofc)
							knitStacked = []
							for bn in stackedLoopNeedles:
								needleNumber = int(bn[1:])
								if needleNumber < n1: k.knit('+', bn, leftC)
								elif bn[0] == 'b' or needleNumber > n2: knitStacked.append(bn) #TODO: make this align with posBed and negBed
							return knitStacked #TODO: make this a global variable or something instead maybe #?
		#--- end leftShaping func ---#^


		def rightShaping(rightC): #called from negBedPass func and happens *before* neg pass (unless otherwise specified) #v
			toDrop = []

			if xferR:
				if xferR > 0: #increase
					global borderStartLeft

					carrierOnLeft = borderStartLeft
					droppedTucks = False
					borderMissN = None

					nextTuckNs = []
						
					if xferR == maxSplit: splitType = 'gradual'
					else: splitType = 'double'

					newRightN, twistedRight = incDoubleBed(k, count=xferR, edgeNeedle=prevRightN, c=rightC, side='r', gauge=gauge, emptyNeedles=emptyNeedles, incMethod=incMethod, splitType=splitType)
					twistedStitches.extend(twistedRight)

					if incMethod == 'split' and addBorder and xferR == gradualSplit: #since no split for > maxSplit yet
						if newRightN % 2 == 0: k.knit('-', f'f{newRightN}', rightC)
						else: k.knit('-', f'b{newRightN}', rightC)

						if borderStartLeft: #waste border carrier is currently parked on left side; get carrier to right side so can tuck over split
							tuckBorderToDrop = wasteBorder(k, startN=leftMostBorderN-borderWidthAdd, endN=prevRightN-1, rows=0, c=borderC, gauge=gauge, offLimits=takenNeedles, lastTime=False, justTuck=True, missN=newRightN)
						
							toDrop.extend(tuckBorderToDrop)
							borderStartLeft = not borderStartLeft
						else:
							tuckBorderToDrop = wasteBorder(k, startN=rightMostBorderN+borderWidthAdd, endN=newRightN, rows=0, c=borderC, gauge=gauge, offLimits=takenNeedles, lastTime=False, justTuck=True, missN=newRightN+1)

							toDrop.extend(tuckBorderToDrop)
							# interlock(k, startN=rightMostBorderN+borderWidthAdd, endN=newRightN+1, length=0.5, c=borderC, gauge=gauge, emptyNeedles=takenNeedles)

						if borderMissN is None: borderMissN = rightMostBorderN+4

						k.comment('tuck over split')
						tuckOverDrop = k.tuckOverSplit(borderC, '-')
						toDrop.extend(tuckOverDrop)

						tuckBorderToDrop = wasteBorder(k, startN=newRightN+1, endN=rightMostBorderN+borderWidthAdd, rows=0, c=borderC, gauge=gauge, offLimits=takenNeedles, lastTime=False, justTuck=True, missN=rightMostBorderN+borderWidthAdd+1)

						toDrop.extend(tuckBorderToDrop)

						# interlock(k, startN=newRightN+1, endN=rightMostBorderN+borderWidthAdd, length=0.5, c=borderC, gauge=gauge, emptyNeedles=takenNeedles)

						newRightN, twistedRight = incDoubleBed(k, count=xferR, edgeNeedle=newRightN, c=rightC, side='r', gauge=gauge, incMethod='split', splitType='gradual')
						twistedStitches.extend(twistedRight)

						borderStartLeft = False

					return toDrop
				else: #decrease
					if openDecSectR:
						if abs(xferR) <= 2: newRightN, stackedLoopNeedles = halfGaugeOpenDec(k, abs(xferR), prevRightN, rightC, 'r', emptyNeedles)
						else:
							if negBedCondition(prevRightN): #force it to bindoff on the neg bed
								rightBindCt = abs(xferR)
								rightBindN = prevRightN
							else:
								rightBindCt = abs(xferR)-1
								rightBindN = prevRightN-1	

							halfGaugeOpenBindoff(k, rightBindCt, rightBindN, rightC, 'r', asDecMethod=True) #TODO: test / check this (and add tucks)

							if openSide[carrier] == 'both' and dir1 == '+':
								if negBedCondition(prevRightN): #force it to bindoff on the pos bed
									rightBindCt = abs(xferR)-1
									rightBindN = prevRightN-1	
								else:
									rightBindCt = abs(xferR)
									rightBindN = prevRightN

								halfGaugeOpenBindoff(k, rightBindCt, rightBindN, (bedCarriers['b'] if (prevRightN % 2 == 0) else bedCarriers['f']), 'r', asDecMethod=True, xtraSecure=True) #new #check
					
							newRightN = prevRightN - abs(xferR)
					else:
						newRightN, stackedLoopNeedles, twistedRight = decDoubleBed(k, abs(xferR), prevRightN, carrier, 'r', gauge, emptyNeedles)
						
						if len(twistedRight) and dir1 == '-': twistedRight = list(filter(lambda bn: bn[:1] == negBed, twistedRight)) #because otherwise, will drop it #TODO: maybe stitch to just if len(twistedRight) #?

						twistedStitches.extend(twistedRight)

					if dir1 == '+': #leftShaping happened first
						if xferR == -1 or xferR == -2: notEnoughNeedlesDecCheck(k, decNeedle=prevRightN, otherEdgeNeedle=n1, count=abs(xferR), c=carrier, gauge=gauge)
					else:
						if xferR == -2 and abs((prevRightN-1)-n1) < 8 and xferL < 0: #TODO: #check if it applies for dec by 1 on either side, dec by > 3 on L, and inc (by xfer, ofc)
							knitStacked = []
							for bn in stackedLoopNeedles:
								needleNumber = int(bn[1:])
								if needleNumber > n2: k.knit('-', bn, rightC)
								elif bn[0] == 'f' or needleNumber < n1: knitStacked.append(bn) #TODO: make this align with posBed & negBed
							return knitStacked
		#--- end rightShaping func ---#^


		def negBedPass(shaping=True): #v
			knitStacked = None

			rightMostN = n2
			if shaping:
				if openSide[carrier] != 'both' or dir1 == '-' or xferR >= 0 or xferR < -2: #TODO: figure out what to do with carriers to prevent tucks if xferR < -2
					if addBorder and xferR > 0: borderToDrop.extend(rightShaping(bedCarriers[negBed]))
					else: knitStacked = rightShaping(bedCarriers[negBed])
				else: rightMostN = prevRightN

				if incMethod != 'split' and dir1 == '+' and xferR > 0 and xferR < 2: #so can 1. get twisted stitches in *after* xfers, not before and 2. not have ladder #TODO: check if this interferes with anything for split
					for n in range(prevRightN+1, n2+1):
						if f'{posBed}{n}' not in emptyNeedles: k.knit('+', f'{posBed}{n}', bedCarriers[posBed])

			if prevLeftN is not None and ((dir1 == '-' and not doublePass1) or (dir1 == '+' and openShaping and gauge == 2 and xferL < -2)): leftMostN = prevLeftN
			else: leftMostN = n1


			def plainKnitNeg(passLeftN, passRightN): #v
				for n in range(passRightN, passLeftN-1, -1):
					twist = None
					if f'{negBed}{n}' in twistedStitches: twist = f'{negBed}{n}'

					if twist is not None:
						k.knit('-', twist, bedCarriers[negBed]) #to be twisted
						k.twist(twist, -rollerAdvance) #do twisted stitch now so can add another knit on that needle without additional knit being interpreted as twisted stitch
						twistedStitches.remove(twist) #get rid of it since we already twisted it
					elif f'{negBed}{n}' not in emptyNeedles and (dir1 == '+' or xferL <= 0 or n >= prevLeftN):
						k.knit('-', f'{negBed}{n}', bedCarriers[negBed]) #TODO: determine if best to knit over it if twisted stitch; maybe tuck instead? #if go to knit, add knit over for twisted fn too; else, have it be an 'else' after if twist is not none
					elif n == passLeftN: k.miss('-', f'{negBed}{n}', bedCarriers[negBed])
				
				if jerseyPassesB > 1:
					if jerseyPassesB % 2 == 1: #whole odd number (great!)
						currPassCt = jerseyPassesB
					elif jerseyPassesB % 2 == 0: #whole even number; will alternate between two odd numbers
						passCt1 = jerseyPassesB + 1
						passCt2 = jerseyPassesB - 1
						if r % 2 == 0: currPassCt = passCt1
						else: currPassCt = passCt2
					
					if currPassCt != 1: # (only tuck if doing more than one pass)
						if passLeftN > leftMostN:
							k.rollerAdvance(0)
							if negBedCondition(passLeftN-1) and f'{negBed}{passLeftN-1}' not in emptyNeedles: k.tuck('-', f'{negBed}{passLeftN-1}', bedCarriers[negBed])
							elif passLeftN-1 != leftMostN and f'{negBed}{passLeftN-2}' not in emptyNeedles: k.tuck('-', f'{negBed}{passLeftN-2}', bedCarriers[negBed])
							k.rollerAdvance(rollerAdvance)
						elif switchDir[carrier] is None or openSide[carrier] == 'r': #to prevent holes along edges where front and back bed meet #TODO: check to make sure this doesn't mess up stretchiness of e.g. garter; try increasing stitch size for these tucks in it does affect it #new #new openSide == 'r' #TODO: check
							posBedEndN = (leftMostN if (posBedCondition(leftMostN)) else leftMostN+1)
							if posBedEndN not in emptyNeedles:
								k.rollerAdvance(0)
								k.tuck('+', f'{posBed}{posBedEndN}', bedCarriers[negBed])
								k.miss('-', f'{posBed}{leftMostN}', bedCarriers[negBed]) #get it back out of the way
								k.rollerAdvance(rollerAdvance)
					
					for p in range(1, currPassCt):
						if p % 2 != 0:
							for n in range(passLeftN, passRightN+1):
								if f'{negBed}{n}' not in emptyNeedles and (dir1 == '+' or xferL <= 0 or n >= prevLeftN): k.knit('+', f'{negBed}{n}', bedCarriers[negBed])
								elif n == passRightN: k.miss('+', f'{negBed}{n}', bedCarriers[negBed])
								if p < currPassCt-1 and n == passRightN:
									if passRightN != n2:
										if negBedCondition(n+1) and f'{negBed}{n+1}' not in emptyNeedles: k.tuck('+', f'{negBed}{n+1}', bedCarriers[negBed])
										elif n+1 != n2 and f'{negBed}{n+2}' not in emptyNeedles: k.tuck('+', f'{negBed}{n+2}', bedCarriers[negBed])
									elif switchDir[carrier] is None or openSide[carrier] == 'l': #to prevent holes along edges where front and back bed meet
										posBedEndN = (n2 if posBedCondition(n2) else n2-1)
										if posBedEndN not in emptyNeedles:
											k.rollerAdvance(0)
											k.tuck('-', f'{posBed}{posBedEndN}', bedCarriers[negBed])
											k.miss('+', f'{posBed}{n2}', bedCarriers[negBed])
											k.rollerAdvance(rollerAdvance)
						else:
							for n in range(passRightN, passLeftN-1, -1):
								if f'{negBed}{n}' not in emptyNeedles and (dir1 == '+' or xferL <= 0 or n >= prevLeftN): k.knit('-', f'{negBed}{n}', bedCarriers[negBed])
								elif n == passLeftN: k.miss('-', f'{negBed}{n}', bedCarriers[negBed])
								if p < currPassCt-1 and n == passLeftN:
									if passLeftN != leftMostN: # removed (dir1 == '+' or xferL <= 0 or n >= prevLeftN) since assigning leftMostN deals with this
										if negBedCondition(n-1) and f'{negBed}{n-1}' not in emptyNeedles: k.tuck('-', f'{negBed}{n-1}', bedCarriers[negBed])
										elif n-1 != leftMostN and f'{negBed}{n-2}' not in emptyNeedles: k.tuck('-', f'{negBed}{n-2}', bedCarriers[negBed])
									elif switchDir[carrier] is None or openSide[carrier] == 'r': #prevent holes #skip if switchDir so beds aren't connect #TODO: still do this if not mean to be open on one side (aka keep track of which sides are open)
										posBedEndN = (leftMostN if posBedCondition(leftMostN) else leftMostN+1)
										if posBedEndN not in emptyNeedles:
											k.rollerAdvance(0)
											k.tuck('+', f'{posBed}{posBedEndN}', bedCarriers[negBed]) #TODO: probably remove 
											k.miss('-', f'{posBed}{leftMostN}', bedCarriers[negBed]) #get it back out of the way
											k.rollerAdvance(rollerAdvance)
			#--- end plainKnitNeg func ---#^


			if negBed == 'b':
				negPatterns = patternsB
				negPatDetails = stitchPatDetailsB
				negPatData = stitchPatDataB

				negColRows = colorworkRowsB
			else:
				negPatterns = patternsF
				negPatDetails = stitchPatDetailsF
				negPatData = stitchPatDataF
				
				negColRows = colorworkRowsF
						
			def fairisleKnitNeg(leftN, rightN): # (passLeftN, passRightN) if len(colRowMapF): colorworkRowsF.append(colRowMapF)
				if len(negColRows) and carrier in negColRows[r]:
					newColRows = None

					for colC, colNs in negColRows[r][carrier].items():
						if colC[0] == '!': #no carrier assigned yet
							if colorworkCs[carrier][int(colC[1:])][0] != '!': newColC = colorworkCs[carrier][int(colC[1:])] #already reassigned with pos
							elif len(reusableCarriers):
								newColC = reusableCarriers.pop()
								print(f'\nWARNING: reusing carrier {newColC} for colorwork section.')
							else: return False

							newColRows = deepcopy(negColRows)

							for colR, colS in enumerate(newColRows):
								if carrier in colS:
									if colC in colS[carrier]: newColRows[colR][carrier][newColC] = newColRows[colR][carrier].pop(colC)
							
							colorworkCs[carrier][colC] = newColC
							colorworkTucks[negBed] = halfGaugeFairisle(k, r, [rightMostN, leftMostN], list(reversed(colNs)), '-', negBed, newColC, colorworkTucks[negBed])
							continue
						
						# if colC == carrier and rightN > colNs[-1]: plainKnitNeg(colNs[-1]+1, rightN) #new
						
						colorworkTucks[negBed] = halfGaugeFairisle(k, r, [rightMostN, leftMostN], list(reversed(colNs)), '-', negBed, colC, colorworkTucks[negBed])

						# if colC == carrier and leftN < colNs[0]: plainKnitNeg(leftN, colNs[0]-1) #new

					if newColRows is not None: replaceColorworkC(negColRows, newColRows)

					return True
				else: return False


			if len(negPatterns):
				passRightN = rightMostN
				passLeftN = leftMostN

				for idx in reversed(list(negPatterns.keys())):
					patNs = negPatterns[idx].copy()
					patLeftN = patNs[0]
					patRightN = patNs[-1]

					if gauge==2 and patRightN-patLeftN==0 and ((negBed=='f' and patLeftN%2!=0) or (negBed=='b' and patLeftN%2==0)): continue #if only includes one needle and won't knit, skip it

					if patRightN < leftMostN: break #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0

					if passRightN > (patRightN+1):
						if not fairisleKnitNeg(patRightN+1, passRightN): plainKnitNeg(patRightN+1, passRightN)

					if patLeftN < leftMostN: patNs[0] = leftMostN #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0

					
					tuckDrop = []
					plaitC = None

					if 'plaitC' in negPatDetails[idx].info:
						plaitC = negPatDetails[idx].info['plaitC']
						if (negPatDetails[idx].info['plaitC'] == None or r == workingRows[negPatDetails[idx].info['plaitC']][0]):
							if plaitC is None:
								if len(reusableCarriers):
									plaitC = reusableCarriers.pop()
									negPatDetails[idx].info['plaitC'] = plaitC
									print(f'\nat row {r}, a reusable carrier ({plaitC}) was just assigned to a plaiting section on bed {negBed}.')
									plaitInfo['assigned'] += 1
									plaitInfo['carriers'].append(plaitC)
									plaitInfo['lastRows'][plaitC] = len(negPatData)-1 - next((i for i, data in enumerate(reversed(negPatData)) if idx in data.keys()), 0)

									if plaitC in takenOutCarriers:
										k.incarrier(plaitC)
										takenOutCarriers.remove(plaitC)
										takeOutAtEnd.append(plaitC)

							if plaitC is not None:
								if abs(patNs[0]-leftMostN) < abs(patNs[-1]-n2):
									negPatDetails[idx].info['plaitCside'] = 'l'
									tuckDrop = placeCarrier(k, leftN=patNs[0], rightN=None, carrierOpts=[plaitC], gauge=gauge)[0]
								else:
									negPatDetails[idx].info['plaitCside'] = 'r'
									tuckDrop = placeCarrier(k, leftN=None, rightN=patNs[-1], carrierOpts=[plaitC], gauge=gauge)[0]
							else: print(f'\nWARNING: at row {r}, we needed a carrier for plaiting but none were available. Note that the piece will have no plaiting in this section (bed {negBed}) until one does become available.')
						else: #tuck if far away
							if negPatDetails[idx].info['plaitCside'] == 'l': tuckDrop = placeCarrier(k, leftN=patNs[0], rightN=None, carrierOpts=[plaitC], gauge=gauge)[0]
							else: tuckDrop = placeCarrier(k, leftN=None, rightN=patNs[-1], carrierOpts=[plaitC], gauge=gauge)[0]

					if 'secureStartN' in negPatDetails[idx].args:
						if patNs[-1] == n2 or (gauge == 2 and patNs[-1] == n2-1): negPatDetails[idx].args['secureStartN'] = True
						else: negPatDetails[idx].args['secureStartN'] = False

						if patNs[0] == leftMostN or (gauge == 2 and patNs[0] == leftMostN+1): negPatDetails[idx].args['secureEndN'] = True
						else: negPatDetails[idx].args['secureEndN'] = False

					patPasses = 1

					if 'passes' in negPatDetails[idx].info and negPatDetails[idx].info['passes'] > 1: #if multiple passes per pass of jersey
						passCt = negPatDetails[idx].info['passes']
						patNeedles = []
						if passCt % 2 == 1: #whole odd number (great!)
							patPasses = passCt
							for p in range(0, passCt):
								patNeedles.append(patNs)
						elif passCt % 2 == 0: #whole even number; will alternate between two odd numbers
							passCt1 = passCt + 1
							passCt2 = passCt - 1

							if negPatDetails[idx].info['count'] % 2 == 0: currPassCt = passCt1
							else: currPassCt = passCt2
							patPasses = currPassCt
							for p in range(0, currPassCt):
								patNeedles.append(patNs)
					else: patNeedles = patNs

					plaitCsInTheWay = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNs[0] and loc <= patNs[-1]]
					if len(plaitCsInTheWay):
						k.rollerAdvance(0)
						for pC in plaitCsInTheWay:
							k.comment(f'miss plaitC ({pC[0]}) out of way of stitch pattern')
							if abs((patNs[0])-pC[1]) < abs((patNs[-1])-pC[1]):
								k.miss('-', f'f{patNs[0]-3}', pC[0])
								plaitInfo['carrierPark'][pC[0]] = patNs[0]-3
							else:
								k.miss('+', f'f{patNs[-1]+3}', pC[0]) #closer to right side, pos miss
								plaitInfo['carrierPark'][pC[0]] = patNs[-1]+3
						k.rollerAdvance(rollerAdvance)

					k.comment(f'insert stitch pattern for bed {negBed} ({patPasses} pass count)')

					if 'stitchNumber' in negPatDetails[idx].info: k.stitchNumber(negPatDetails[idx].info['stitchNumber'])

					insertStitchPattern(k, stitchPat=negPatDetails[idx], needles=patNeedles, passEdgeNs=[leftMostN, n2], bed='b', side='r', c=bedCarriers[negBed])

					if 'stitchNumber' in negPatDetails[idx].info: k.stitchNumber(stitchNumber) #reset

					if len(twistedStitches):
						for n in range(patNs[-1], patNs[0], -1): #TODO: have this be possible for if stitch pattern length > 1
							twist = None
							if f'b{n}' in twistedStitches: twist = f'b{n}'
							elif f'f{n}' in twistedStitches: twist = f'f{n}'
							if twist is not None:
								k.twist(twist, -rollerAdvance) #do twisted stitch now so can add another knit on that needle without additional knit being interpreted as twisted stitch
								twistedStitches.remove(twist) #get rid of it since we already twisted it

					if len(tuckDrop):
						k.rollerAdvance(0)
						for bn in tuckDrop:
							k.drop(bn)
						k.rollerAdvance(rollerAdvance)

					if plaitC is not None and sectionCountChangeNext and (sectionCount < len(pieceMap[r+1])):
						k.comment(f'miss plaitC out of way of upcoming new section')
						k.rollerAdvance(0)
						if negPatDetails[idx].info['plaitCside'] == 'l':
							k.miss('-', f'f{rowsEdgeNeedles[r][0]}', plaitC)
							plaitInfo['carrierPark'][plaitC] = rowsEdgeNeedles[r][0]
						else:
							k.miss('+', f'f{rowsEdgeNeedles[r][-1]}', plaitC)
							plaitInfo['carrierPark'][plaitC] = rowsEdgeNeedles[r][-1]
						k.rollerAdvance(rollerAdvance)
				
					passRightN = patLeftN-1

				# if passRightN > (patRightN+1):
				if passRightN >= passLeftN:
					if not fairisleKnitNeg(passLeftN, passRightN): plainKnitNeg(passLeftN, passRightN) # >= because patLeftN-1 not patLeftN
					# if carrier in negColData[r] and negColData[r][carrier][0] <= passRightN and negColData[r][carrier][-1] >= passLeftN:
					# 	colNs = negColData[r][carrier].copy()

					# 	if passRightN > colNs[-1]: plainKnitNeg(colNs[-1]+1, passRightN) #new

					# 	halfGaugeFairisle(k, list(filter(lambda cN: cN >= passRightN and cN <= passLeftN, colNs)), carrier, '-', negBed)

					# 	if passLeftN < colNs[0]: plainKnitNeg(patRightN+1, colNs[0]-1) #new
					# else: plainKnitNeg(passLeftN, passRightN) #new # >= because patLeftN-1 not patLeftN
			# else: plainKnitNeg(leftMostN, rightMostN) #new #leftMostN #*
			else:
				if not fairisleKnitNeg(leftMostN, rightMostN): plainKnitNeg(leftMostN, rightMostN) #new #leftMostN #*
			

			if knitStacked: #TODO: figure out if this is causing a float
				for bn in knitStacked:
					k.knit('-', bn, bedCarriers[negBed])

			if shaping and openSide[carrier] == 'both' and dir1 == '+' and xferR < 0 and xferR >= -2: #if skipped this before, do it now that carriers are on opposite sides
				if addBorder and xferR > 0: borderToDrop.extend(rightShaping(bedCarriers[posBed]))
				else: knitStacked = rightShaping(bedCarriers[posBed]) #TODO: deal with toDrop and knitStacked somewhere else now, I guess #^ (or maybe not #? since might not have those returns due to open dec) #TODO figure out if this should go before or after bit below #v
				
			if dir1 == '+' and openShaping and gauge == 2 and xferL < -2: #left shaping happened first & keep to complete open tube bindoff shaping on left for other bed
				if posBedCondition(prevLeftN): #force it to bindoff on the neg bed
					leftBindCt = abs(xferL)-1
					leftBindN = prevLeftN+1
				else:
					leftBindCt = abs(xferL)
					leftBindN = prevLeftN

				halfGaugeOpenBindoff(k, leftBindCt, leftBindN, bedCarriers[negBed], 'l', asDecMethod=True, xtraSecure=True) #TODO: test / check this (and add tucks) #prevLeftN+1 so it does other bed
		#--- end negBedPass func ---#^


		for n in range(n0, n1):
			visualization[r].append(0)

		if addBorder and r == lastDropR+2:
			if len(sanityDrop):
				sanityDrop = list(filter(lambda bn: bn not in rowsTakenNeedles[r], sanityDrop))

				k.comment(f'sanity drop') #debug
				for n in sanityDrop:
					k.drop(n)
				sanityDrop = []


		def posBedPass(shaping=True): #v
			global placementLeft

			knitStacked = None

			leftMostN = n1

			if shaping and (openSide[carrier] != 'both' or dir1 == '+' or xferL >= 0 or xferL < -2): #changed it so this will only happen *before* pass if pos first in case of 2 carriers for open dec, to prevent shaping from happening with both carriers are on same side #but just do it normally if increasing or if shaping by bindoff (bc will need carrier on left side for that) #TODO: if dir1 == '-', change to dir1 == '+' and posBed == negBed #? #TODO: if skipping this, make passLeftN prevLeftN (actually, also define leftMostN like rightMostN)
				if addBorder and xferL > 0: borderToDrop.extend(leftShaping(bedCarriers[posBed]))
				else: knitStacked = leftShaping(bedCarriers[posBed])
			elif dir1 != '+': leftMostN = prevLeftN

			if prevRightN is not None and ((dir1 == '+' and not doublePass1) or (dir1 == '-' and openShaping and gauge == 2 and xferR < -2 and prevRightN % 2 != 0)): rightMostN = prevRightN
			else: rightMostN = n2


			def plainKnitPos(passLeftN, passRightN): #v
				if placementLeft and passLeftN <= (prevLeftN-1):
					passLeftN = prevLeftN #for now
				
				if incMid and placementLeft and prevLeftN > passRightN:
					incDoubleBed(k, count=(prevLeftN-passRightN), edgeNeedle=prevLeftN-1, c=bedCarriers[posBed], side='l', gauge=gauge, emptyNeedles=emptyNeedles, incMethod='zig-zag')
					return

				for n in range(passLeftN, passRightN+1):
					twist = None
					if f'{posBed}{n}' in twistedStitches: twist = f'{posBed}{n}'

					if twist is not None:
						k.knit('+', twist, bedCarriers[posBed]) #to be twisted
						k.twist(twist, -rollerAdvance) #do twisted stitch now so can add another knit on that needle without additional knit being interpreted as twisted stitch
						twistedStitches.remove(twist) #get rid of it since we already twisted it
					elif (dir1 == '-' or xferR <= 0 or n <= prevRightN) and f'{posBed}{n}' not in emptyNeedles: #don't add the knits if increasing, since they will be added anyway thru increasing
						k.knit('+', f'{posBed}{n}', bedCarriers[posBed]) #TODO: determine if best to knit over it if twisted stitch; maybe tuck instead? #if go to knit, add knit over for twisted fn too; else, have it be an 'else' after if twist is not none
					elif n == passRightN: k.miss('+', f'{posBed}{n}', bedCarriers[posBed])
				
				if jerseyPassesF > 1:
					if jerseyPassesF % 2 == 1: #whole odd number (great!)
						currPassCt = jerseyPassesF
					elif jerseyPassesF % 2 == 0: #whole even number; will alternate between two odd numbers
						passCt1 = jerseyPassesF + 1
						passCt2 = jerseyPassesF - 1
						if r % 2 == 0: currPassCt = passCt1
						else: currPassCt = passCt2
					
					if currPassCt != 1: # (only tuck if doing more than one pass) #TODO: #check and decide if keep like this
						if passRightN < rightMostN:
							if posBedCondition(passRightN+1) and f'{posBed}{passRightN+1}' not in emptyNeedles: k.tuck('+', f'{posBed}{passRightN+1}', bedCarriers[posBed]) #pos bed
							elif passRightN+1 != rightMostN and f'{posBed}{passRightN+2}' not in emptyNeedles: k.tuck('+', f'{posBed}{passRightN+2}', bedCarriers[posBed])
						# elif switchDir is None or openSide == 'l':
						elif switchDir[carrier] is None or openSide[carrier] == 'l':
							negBedEndN = (rightMostN-1 if posBedCondition(rightMostN) else rightMostN)

							if negBedEndN not in emptyNeedles:
								k.rollerAdvance(0)
								k.tuck('-', f'{negBed}{negBedEndN}', bedCarriers[posBed])
								k.miss('+', f'{negBed}{rightMostN}', bedCarriers[posBed])
								k.rollerAdvance(rollerAdvance)

					for p in range(1, currPassCt): #won't execute if only one pass (already did it above)
						if p % 2 != 0:
							for n in range(passRightN, passLeftN-1, -1):
								if f'f{n}' not in emptyNeedles and (dir1 == '-' or xferR <= 0 or n <= prevRightN): k.knit('-', f'{posBed}{n}', bedCarriers[posBed])
								elif n == passLeftN: k.miss('-', f'{posBed}{n}', bedCarriers[posBed])

								if p < currPassCt-1 and n == passLeftN:
									if passLeftN != n1: #TODO: #check and decide if keep like this
										if posBedCondition(n-1) and f'{posBed}{n-1}' not in emptyNeedles: k.tuck('-', f'{posBed}{n-1}', bedCarriers[posBed]) #pos bed
										elif n-1 != n1 and f'{posBed}{n-2}' not in emptyNeedles: k.tuck('-', f'{posBed}{n-2}', bedCarriers[posBed]) #^
									elif switchDir[carrier] is None or openSide[carrier] == 'r':
										negBedEndN = (n1+1 if posBedCondition(n1) else n1)
										if negBedEndN not in emptyNeedles:
											k.rollerAdvance(0)
											k.tuck('+', f'{negBed}{negBedEndN}', bedCarriers[posBed])
											k.miss('-', f'{negBed}{n1}', bedCarriers[posBed])
											k.rollerAdvance(rollerAdvance)
						else:
							for n in range(passLeftN, passRightN+1):
								if f'{posBed}{n}' not in emptyNeedles and (dir1 == '-' or xferR <= 0 or n <= prevRightN): k.knit('+', f'{posBed}{n}', bedCarriers[posBed]) #TODO: see if condition and (dir1 == '-' or xferR <= 0 or n <= prevRightN) should still be met
								elif n == passRightN: k.miss('+', f'{posBed}{n}', bedCarriers[posBed])

								if p < currPassCt-1 and n == passRightN:
									if passRightN != rightMostN: # removed < and (dir1 == '-' or xferR <= 0 or n <= prevRightN) > since assigning rightMostN should take care of this
										k.rollerAdvance(0)
										if posBedCondition(n+1) and f'{posBed}{n+1}' not in emptyNeedles: k.tuck('+', f'{posBed}{n+1}', bedCarriers[posBed]) #pos bed
										elif n+1 != rightMostN and f'{posBed}{n+2}' not in emptyNeedles: k.tuck('+', f'{posBed}{n+2}', bedCarriers[posBed]) #pos bed
										k.rollerAdvance(rollerAdvance)
									elif switchDir[carrier] is None or openSide[carrier] == 'l':
										negBedEndN = (rightMostN-1 if (rightMostN % 2 == 0) else rightMostN)
										if negBedEndN not in emptyNeedles:
											k.rollerAdvance(0)
											k.tuck('-', f'{negBed}{otherBedEndN}', bedCarriers[posBed])
											k.miss('+', f'{negBed}{rightMostN}', bedCarriers[posBed])
											k.rollerAdvance(rollerAdvance)
			#--- end plainKnitPos func ---#^

			if posBed == 'f': #new
				posPatterns = patternsF
				posPatDetails = stitchPatDetailsF
				posPatData = stitchPatDataF

				# posColData = colorworkDataF
				posColRows = colorworkRowsF
			else:
				posPatterns = patternsB
				posPatDetails = stitchPatDetailsB
				posPatData = stitchPatDataB

				# posColData = colorworkDataB
				posColRows = colorworkRowsB #^
			
			def fairisleKnitPos(leftN, rightN): # (passLeftN, passRightN)
				if len(posColRows) and carrier in posColRows[r]:
					newColRows = None

					for colC, colNs in posColRows[r][carrier].items():
						if colC[0] == '!': #no carrier assigned yet
							if colorworkCs[carrier][int(colC[1:])][0] != '!': newColC = colorworkCs[carrier][int(colC[1:])] #already reassigned with neg fairisle
							elif len(reusableCarriers):
								newColC = reusableCarriers.pop()
								print(f'\nWARNING: reusing carrier {newColC} for colorwork section.')
							else: return False

							newColRows = deepcopy(posColRows)
							for colR, colS in enumerate(newColRows): #TODO: make this correspond with back bed new carrier
								if carrier in colS:
									if colC in colS[carrier]: newColRows[colR][carrier][newColC] = newColRows[colR][carrier].pop(colC)
							
							colorworkCs[carrier][colC] = newColC
							colorworkTucks[posBed] = halfGaugeFairisle(k, r, [leftMostN, rightMostN], colNs, '+', posBed, newColC, colorworkTucks[posBed])
							continue
						
						colorworkTucks[posBed] = halfGaugeFairisle(k, r, [leftMostN, rightMostN], colNs, '+', posBed, colC, colorworkTucks[posBed])

					if newColRows is not None: replaceColorworkC(posColRows, newColRows)

					return True
				else: return False

			if len(posPatterns):
				passLeftN = leftMostN
				passRightN = rightMostN

				for idx in list(posPatterns.keys()):
					patNs = posPatterns[idx].copy()
					patLeftN = patNs[0]
					patRightN = patNs[-1]

					if gauge==2 and patRightN-patLeftN==0 and ((posBed=='f' and patLeftN%2!=0) or (posBed=='b' and patLeftN%2==0)): continue #if only includes one needle and won't knit, skip it

					if patLeftN > rightMostN: break #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0

					if passLeftN < (patLeftN-1):
						if not fairisleKnitPos(passLeftN, patLeftN-1): plainKnitPos(passLeftN, patLeftN-1)

					if patRightN > rightMostN: patNs[-1] = rightMostN #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0
					
					tuckDrop = []
					plaitC = None

					if 'plaitC' in posPatDetails[idx].info:
						plaitC = posPatDetails[idx].info['plaitC']
						if (posPatDetails[idx].info['plaitC'] == None or r == workingRows[posPatDetails[idx].info['plaitC']][0]):
							if plaitC is None:
								if len(reusableCarriers):
									plaitC = reusableCarriers.pop()

									posPatDetails[idx].info['plaitC'] = plaitC
									print(f'\nat row {r}, a reusable carrier ({plaitC}) was just assigned to a plaiting section on bed {posBed}.')
									plaitInfo['assigned'] += 1
									plaitInfo['carriers'].append(plaitC)
									plaitInfo['lastRows'][plaitC] = len(posPatData)-1 - next((i for i, data in enumerate(reversed(posPatData)) if idx in data.keys()), 0)

									if plaitC in takenOutCarriers:
										k.incarrier(plaitC)
										takenOutCarriers.remove(plaitC)
										takeOutAtEnd.append(plaitC)

							if plaitC is not None:
								if abs(patNs[-1]-rightMostN) < abs(patNs[0]-n1):
									posPatDetails[idx].info['plaitCside'] = 'r'
									tuckDrop = placeCarrier(k, leftN=None, rightN=patNs[-1], carrierOpts=[plaitC], gauge=gauge)[0]
								else:
									posPatDetails[idx].info['plaitCside'] = 'l'
									tuckDrop = placeCarrier(k, leftN=patNs[0], rightN=None, carrierOpts=[plaitC], gauge=gauge)[0]
							else: print(f'\nWARNING: at row {r}, we needed a carrier for plaiting but none were available. Note that the piece will have no plaiting in this section (bed {posBed}) until one does become available.')
						else: #tuck if far away
							if posPatDetails[idx].info['plaitCside'] == 'l': tuckDrop = placeCarrier(k, leftN=patNs[0], rightN=None, carrierOpts=[plaitC], gauge=gauge)[0]
							else: tuckDrop = placeCarrier(k, leftN=None, rightN=patNs[-1], carrierOpts=[plaitC], gauge=gauge)[0]

					if 'secureStartN' in posPatDetails[idx].args:
						if patNs[0] == n1 or (gauge == 2 and patNs[0] == n1+1): posPatDetails[idx].args['secureStartN'] = True
						else: posPatDetails[idx].args['secureStartN'] = False

						if patNs[-1] == rightMostN or (gauge == 2 and patNs[-1] == rightMostN-1): posPatDetails[idx].args['secureEndN'] = True
						else: posPatDetails[idx].args['secureEndN'] = False

					patPasses = 1
					if 'passes' in posPatDetails[idx].info and posPatDetails[idx].info['passes'] > 1: #if multiple passes per pass of jersey
						passCt = posPatDetails[idx].info['passes']
						patNeedles = []
						if passCt % 2 == 1: #whole odd number (great!)
							patPasses = passCt
							for p in range(0, passCt):
								patNeedles.append(patNs)
						elif passCt % 2 == 0: #whole even number; will alternate between two odd numbers
							passCt1 = passCt + 1
							passCt2 = passCt - 1

							if posPatDetails[idx].info['count'] % 2 == 0: currPassCt = passCt1
							else: currPassCt = passCt2
							patPasses = currPassCt
							for p in range(0, currPassCt):
								patNeedles.append(patNs)
					else: patNeedles = patNs

					if placementLeft and patNs[0] < prevLeftN: #here things change
						if type(patNeedles[0]) == list: patNeedles[0][0] = prevLeftN
						else: patNeedles[0] = prevLeftN #have first (or only) pass start at prevLeftN

					plaitCsInTheWay = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNs[0] and loc <= patNs[-1]]
					if len(plaitCsInTheWay):
						k.rollerAdvance(0)
						for pC in plaitCsInTheWay:
							k.comment(f'miss plaitC ({pC[0]}) out of way of stitch pattern')
							if abs((patNs[-1])-pC[1]) < abs((patNs[0])-pC[1]):
								k.miss('+', f'f{patNs[-1]+3}', pC[0]) #closer to right side, pos miss
								plaitInfo['carrierPark'][pC[0]] = patNs[-1]+3
							else:
								k.miss('-', f'f{patNs[0]-3}', pC[0])
								plaitInfo['carrierPark'][pC[0]] = patNs[0]-3
						k.rollerAdvance(rollerAdvance)

					k.comment(f'insert stitch pattern for bed {posBed} ({patPasses} pass count)')

					if 'stitchNumber' in posPatDetails[idx].info: k.stitchNumber(posPatDetails[idx].info['stitchNumber'])

					if incMid and placementLeft and prevLeftN > patRightN:
						incDoubleBed(k, count=(prevLeftN-patRightN), edgeNeedle=prevLeftN-1, c=bedCarriers[posBed], side='l', gauge=gauge, emptyNeedles=emptyNeedles, incMethod='zig-zag')
					else: insertStitchPattern(k, stitchPat=posPatDetails[idx], needles=patNeedles, passEdgeNs=[n1, rightMostN], bed='f', side='l', c=bedCarriers[posBed])
					
					placementLeft = False
					
					if 'stitchNumber' in posPatDetails[idx].info: k.stitchNumber(stitchNumber) #reset it

					if len(twistedStitches):
						for n in range(patNs[0], patNs[-1]): #TODO: have this be possible for if stitch pattern length > 1
							twist = None
							if f'b{n}' in twistedStitches: twist = f'b{n}'
							elif f'f{n}' in twistedStitches: twist = f'f{n}'
							if twist is not None:
								k.twist(twist, -rollerAdvance) #do twisted stitch now so can add another knit on that needle without additional knit being interpreted as twisted stitch
								twistedStitches.remove(twist) #get rid of it since we already twisted it
					
					if len(tuckDrop):
						k.rollerAdvance(0)
						for bn in tuckDrop:
							k.drop(bn)
						k.rollerAdvance(rollerAdvance)

					if plaitC is not None and sectionCountChangeNext and (sectionCount < len(pieceMap[r+1])): # sectionCount < len(pieceMap[r+1]) means a *new* section is coming, rather than a section ending
						k.comment(f'miss plaitC out of way of upcoming new section')
						k.rollerAdvance(0)
						if stitchPatDetailsF[idx].info['plaitCside'] == 'l':
							k.miss('-', f'f{rowsEdgeNeedles[r][0]}', plaitC)
							plaitInfo['carrierPark'][plaitC] = rowsEdgeNeedles[r][0]
						else:
							k.miss('+', f'f{rowsEdgeNeedles[r][-1]}', plaitC)
							plaitInfo['carrierPark'][plaitC] = rowsEdgeNeedles[r][-1]
						k.rollerAdvance(rollerAdvance)

					passLeftN = patRightN+1
				
				if passRightN >= passLeftN:
					if not fairisleKnitPos(passLeftN, passRightN): plainKnitPos(passLeftN, passRightN) #new
			else:
				if not fairisleKnitPos(leftMostN, rightMostN): plainKnitPos(leftMostN, rightMostN) #new


			if knitStacked:
				for bn in knitStacked:
					k.knit('+', bn, bedCarriers[posBed])

			if dir1 == '+' and (xferR < -2): #so no ladder (carrier is in correct spot to dec or inc with yarn) #TODO: have this be the correct stitch pattern if applicable
				for n in range(n2+1, prevRightN+1):
					if f'{posBed}{n}' not in emptyNeedles:
						k.knit('+', f'{posBed}{n}', bedCarriers[posBed])
					elif n == prevRightN: k.miss('+', f'{posBed}{n}', bedCarriers[posBed]) #get carrier out of way

				if bothOpenXtraC is not None and openShaping and gauge == 2: k.miss('+', f'{posBed}{prevRightN+1}', bedCarriers[posBed]) #using different carrier for bindoff that's coming up and will tuck prevRightN+1, so miss past that too

			if shaping and openSide[carrier] == 'both' and dir1 == '-' and xferL < 0 and xferL >= -2: #if skipped this before, do it now that carriers are on opposite sides
				if addBorder and xferL > 0: borderToDrop.extend(leftShaping(bedCarriers[negBed]))
				else: knitStacked = leftShaping(bedCarriers[negBed]) #TODO: deal with toDrop and knitStacked somewhere else now, I guess #^ (or maybe not #? since might not have those returns due to open dec)
		#--- end posBedPass func ---#^

		if dir1 == '-': # placeXtraC and bothOpenXtraC['bed'] == negBed #new location (since posBedPass needs to be defined first) #v
			if placeXtraC and bothOpenXtraC['bed'] == negBed:
				k.comment('place carrier with extra pass')
				# resetBedCarriers = bedCarriers.copy()
				posBed = negBed
				posBedPass(False)
				if negBed == 'f': posBed = 'b'
				else: posBed = 'f' #reset it #^
			negBedPass() #'f' instead of 'b' if switchDir == True, otherwise, 'b' if switchDir == None or False (meaning we are switching direction, but just not this time)
			
			if xferL < -2: #so no ladder (carrier is in correct spot to dec by bindoff) #TODO: have this be the correct stitch pattern if applicable
				if bothOpenXtraC is not None and openShaping and gauge == 2: k.miss('-', f'{negBed}{prevLeftN-1}', bedCarriers[negBed]) #using different carrier for bindoff that's coming up and will tuck prevLeftN-1, so miss past that too #TODO: #remove #?

		if placeXtraC and bothOpenXtraC['bed'] == posBed:
			k.comment('place carrier with extra pass')
			negBed = posBed
			negBedPass(False)
			if posBed == 'f': negBed = 'b'
			else: negBed = 'f' #reset it

		posBedPass()
		if dir1 == '+':
			if placeXtraC and bothOpenXtraC['bed'] == negBed:
				k.comment('place carrier with extra pass')
				posBed = negBed
				posBedPass(False)
				if negBed == 'f': posBed = 'b'
				else: posBed = 'f' #reset it #^

			negBedPass()
			if doublePass1:
				k.comment('extra pass to prepare for open decreasing')
				posBedPass(False) #new#*#*
		else: #right shaping happened first
			if openDecSectR and gauge == 2 and xferR < -2: #* #right shaping happened first & need to complete open tube bindoff shaping on right for other bed
				if negBedCondition(prevRightN): #force it to bindoff on the pos bed
					rightBindCt = abs(xferR)-1
					rightBindN = prevRightN-1	
				else:
					rightBindCt = abs(xferR)
					rightBindN = prevRightN

				halfGaugeOpenBindoff(k, rightBindCt, rightBindN, bedCarriers[posBed], 'r', asDecMethod=True, xtraSecure=True) #TODO: test / check this (and add tucks) #prevRightN-1 so it does other bed #use carrier for bed than corresponds with parity of needle one in from prevRightN #check
			
			if doublePass1:
				k.comment('extra pass to prepare for open decreasing')
				negBedPass(False) #new#*#*

		if len(placementPass) and placementPass[0] < placementPass[1]: #if applicable, place middle section carrier by new left-most needle to get it out of the way for new left-most shortrow section in next row #TODO: check this with posBed and negBed
			for n in range(placementPass[0], placementPass[1]+1):
				if f'b{n}' not in emptyNeedles: k.knit('+', f'b{n}', bedCarriers['b']) #TODO: see if this interferes with openShaping
			k.miss('+', f'b{placementPass[1]+1}', bedCarriers['b'])

		for bn in twistedStitches:
			k.twist(bn, -rollerAdvance)

		
		if len(borderToDrop) and sectionIdx == (sectionCount-1): #if last section
			# if dropBorderKnits: lastDropR = r #new #*
			
			borderToDrop = sortBedNeedles(list(filter(lambda bn: bn not in rowsTakenNeedles[r], borderToDrop)))

			if dropBorderKnits:
				lastDropR = r #new #*

				k.comment('last drop') #remove #?
				sanityDrop = borderToDrop.copy()
			else: k.comment('drop waste border tucks') #remove #?

			for p in range(0, 2): #do it twice
				for n in borderToDrop:
					k.drop(n)
			
			borderToDrop = [] #new #* #TODO: test #*#*#*

		for n in range(n1, n2 + 1):
			visualization[r].append(int(carrier))

		if sectionIdx == (sectionCount-1) and (plaitInfo['count'] != plaitInfo['assigned'] or (leftDropWasteC is None and rightDropWasteC is None)) and r in plaitInfo['lastRows'].values():
			for lC, lR in plaitInfo['lastRows'].items():
				if lR == r:
					reusableCarriers.append(lC)
					if plaitInfo['count'] != plaitInfo['assigned']: print(f'\nat row {r}, a carrier that was being used for plaiting ({lC}) just became available, which we needed for a plaiting section!')
					else: print(f'\nat row {r}, a carrier that was being used for plaiting ({lC}) just became available, which we needed for the drop waste border!')

		if sectionFinished:
			if dir1 == '+':
				bindSide = 'l'
				bindXferN = n1
				if bedCarriers[posBed] != bedCarriers[negBed]: rightReusableCs.append(bedCarriers[posBed])
			else:
				bindSide = 'r'
				bindXferN = n2
				rightReusableCs.append(bedCarriers[posBed])
			if addBindoff and finishOff: #TODO: decide if should copy not finishOff stuff into here and move down so `if not finishOff:`
				if dir1 == '+':
					bindC = bedCarriers[negBed] #most recent
					if not closedCaston and not openBindoff and bedCarriers[posBed] != bedCarriers[negBed]:
						if bedCarriers[posBed] not in takeOutAtEnd: takeOutAtEnd.append(bedCarriers[posBed]) #TODO: miss it past edge-most needle
						reusableCarriers.append(bedCarriers[posBed]) #TODO: print that this carrier is now available!
						k.miss('+', f'f{n2+3}', bedCarriers[posBed]) #miss carrier out of the way
				else:
					bindC = bedCarriers[posBed]
					if not closedCaston and not openBindoff and bedCarriers[posBed] != bedCarriers[negBed]:
						k.outcarrier(bedCarriers[negBed])
						takenOutCarriers.append(bedCarriers[negBed])
						if bedCarriers[negBed] in takeOutAtEnd: takeOutAtEnd.remove(bedCarriers[negBed])
						reusableCarriers.append(bedCarriers[negBed]) #TODO: print that this carrier is now available!

				if openBindoff:
					bindCt = (n2-n1+1)
					if bedCarriers[posBed] != bedCarriers[negBed]:
						if negBedCondition(n1): #force it to bindoff on the neg bed
							leftBindCt = bindCt-1 #TODO: check and ... #v
							leftBindN = n1
						else:
							leftBindCt = bindCt-2
							leftBindN = n1+1
						
						halfGaugeOpenBindoff(k, leftBindCt, leftBindN, bedCarriers[negBed], 'l', asDecMethod=True, xtraSecure=True)
						k.miss('+', f'f{n2+3}', bedCarriers[negBed]) #miss carrier out of the way
						if bedCarriers[negBed] not in takeOutAtEnd: takeOutAtEnd.append(bedCarriers[negBed])

						if posBedCondition(n2): #force it to bindoff on the pos bed (which will have ended on right)
							rightBindCt = bindCt-1 #TODO: check and maybe change back to bindCt (and bindCt-1 below for else)
							rightBindN = n2
						else:
							rightBindCt = bindCt-2
							rightBindN = n2-1	

						halfGaugeOpenBindoff(k, rightBindCt, rightBindN, bedCarriers[posBed], 'r', asDecMethod=True, xtraSecure=True)
						k.outcarrier(bedCarriers[posBed])
						if bedCarriers[posBed] in takeOutAtEnd: takeOutAtEnd.remove(bedCarriers[posBed])
					else:
						halfGaugeOpenBindoff(k, (n2-n1+1), bindXferN, bindC, bindSide)
						if bindC in takeOutAtEnd: takeOutAtEnd.remove(bindC)
				else:
					bindoff(k, (n2-n1+1), bindXferN, bindC, bindSide, emptyNeedles=emptyNeedles)
					if bindC in takeOutAtEnd: takeOutAtEnd.remove(bindC)

				if r == len(pieceMap)-1 and sectionIdx == sectionCount-1 and len(takeOutAtEnd):
					for outC in takeOutAtEnd:
						if outC != bindC: k.outcarrier(outC)
			else: #drop finish (or not finishOff)
				outCarriers = []

				if addBorder: widthAdd = borderWidthAdd
				else: widthAdd = 0

				if r == len(pieceMap)-1 and sectionIdx == sectionCount-1:
					rollOut = True
					outCarriers.append(bedCarriers[posBed])
					outCarriers.append(bedCarriers[negBed]) #if same set() will ensure no duplicates
					outCarriers.extend(takeOutAtEnd)
					outCarriers = list(set(outCarriers)) #ensure no duplicates
				else:
					if (plaitInfo['count'] == plaitInfo['assigned']) and (leftDropWasteC is not None or rightDropWasteC is not None) and (not openShaping or not rightDec or not leftDec): #check #TODO: change this to work with openDecSect #*#*#*
						if not finishOff:
							if bedCarriers[negBed] not in takeOutAtEnd: takeOutAtEnd.append(bedCarriers[negBed]) #TODO: miss it past edge-most needle
							if bedCarriers[posBed] not in takeOutAtEnd: takeOutAtEnd.append(bedCarriers[posBed]) #TODO: miss it past edge-most needle
						else:
							outCarriers.append(bedCarriers[negBed])
							if bedCarriers[negBed] in takeOutAtEnd: takeOutAtEnd.remove(bedCarriers[negBed])
							if bedCarriers[posBed] != bedCarriers[negBed]: 
								outCarriers.append(bedCarriers[posBed])
								if bedCarriers[posBed] in takeOutAtEnd: takeOutAtEnd.remove(bedCarriers[posBed])
					else: #might need the carrier for plaiting or openShaping for both beds
						if plaitInfo['count'] != plaitInfo['assigned']: print(f'\nat row {r}, a carrier that was being used in the main piece ({carrier}) just became available, which we needed for a plaiting section!')
						else: print(f'\nat row {r}, a carrier that was being used in the main piece ({carrier}) just became available, which we needed for the drop waste border!')

						reusableCarriers.append(bedCarriers[negBed])
						if bedCarriers[posBed] != bedCarriers[negBed]: reusableCarriers.append(bedCarriers[posBed])
					 
					if abs(bindXferN-(leftMostBorderN-widthAdd)) < abs(bindXferN-(rightMostBorderN+widthAdd)):
						dropMissDir = '-'
						k.miss('-', f'f{leftMostBorderN-widthAdd}', bedCarriers[negBed]) #TODO: check with negBed etc.
					else:
						dropMissDir = '+'
						k.miss('+', f'f{rightMostBorderN+widthAdd}', bedCarriers[posBed]) #TODO: check
					rollOut = False

				recycledCarrier = False
				if finishOff:
					if leftDropWasteC is None and len(reusableCarriers):
						leftDropWasteC = reusableCarriers[0]
						if leftDropWasteC in takenOutCarriers:
							k.incarrier(leftDropWasteC)
							takeOutAtEnd.append(leftDropWasteC)
							takenOutCarriers.remove(leftDropWasteC)
						recycledCarrier = True

					tuckDrop, dropBorderC, dropTuckDir = placeCarrier(k, leftN=n1, rightN=n2, carrierOpts=[leftDropWasteC, rightDropWasteC], gauge=gauge)
					if dropTuckDir is None: dropTuckDir = dir1

					dropFinish(k, [n1, n2], [n1, n2], outCarriers, rollOut, emptyNeedles, direction=dropTuckDir, borderC=dropBorderC, borderStPat='rib')

					if dropBorderC not in outCarriers:
						if addBorder and dropBorderC == borderC and r < lastWasteWeightRow:
							if dropMissDir == '+': borderStartLeft = False
							else: borderStartLeft = True
						
						k.rollerAdvance(0)
						if dropMissDir == '+':
							k.miss('+', f'f{rightMostBorderN+widthAdd}', dropBorderC)
						else:
							k.miss('-', f'f{leftMostBorderN-widthAdd}', dropBorderC)
						k.rollerAdvance(rollerAdvance)

					if len(tuckDrop):
						k.rollerAdvance(0)
						for t in tuckDrop:
							k.drop(t)
						k.rollerAdvance(rollerAdvance)
				else:
					for oC in outCarriers:
						k.outcarrier(oC)
						if oC in takeOutAtEnd: takeOutAtEnd.remove(oC)

				takenOutCarriers.extend(outCarriers)
				
				if recycledCarrier: leftDropWasteC = None #so it is available for other stuff

		#-------------------------
		n0 = n2 + 1

		if sectionIdx == sectionCount-1:
			for n in range(n0, width):
				row.append(0)
				visualization[r].append(0)
		else: endPoints.append(n0)

		shortrowCount += 1

		r += 1

		if sectionIdx < sectionCount-1:
			if sectionCountChangeNext:
				if sectionIdx == 0: cycleEnd = r-1
				sectionIdx += 1
				r -= shortrowCount
				shortrowCount = 0
			elif (shortrowCount == maxShortrowCount) or r == len(pieceMap):
				if sectionIdx == 0: cycleEnd = r-1
				if r == len(pieceMap):
					r -= shortrowCount
					shortrowCount = 0
					sectionIdx += 1
				else:
					shortrowCount = 0
					sectionIdx += 1
					r -= maxShortrowCount
		else:
			if sectionCountChangeNext or shortrowCount == maxShortrowCount:
				shortrowCount = 0
				sectionIdx = 0
		
		#do it until: maxShortrowCount or sectionCountChangeNext

	vFile = open('./visualization.txt', 'w')
	 
	# print('\nvisualization:') #remove
	for v in visualization:
		for c in v: vFile.write(''.join(str(c)))
		vFile.write('\n')
		# print(v) #remove

	vFile.close()

	print('\nDone.')
