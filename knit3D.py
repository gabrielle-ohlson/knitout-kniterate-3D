import numpy as np
import math
import warnings

from PIL import Image, ImageColor

#NOTE: for gauge > 1: decided baseBed should consistently be front so as to make things less complicated (because doesn't really matter) --- so translation would be fn -> f(gauge*n) bn -> b((gauge*n)+1)

#TODO: maybe fix things so if -> f then b and if <- 
#---------------------------------------------
#--- CUSTOMIZABLE VARIABLES FOR EXTENSIONS ---
#---------------------------------------------
#for waste section
wasteSpeedNumber = 400

#for main section
speedNumber = 300
# stitchNumber = 5
stitchNumber = 4
rollerAdvance = 300

#for xfers
xferSpeedNumber = 300 #100
xferStitchNumber = math.ceil(stitchNumber//2)
xferRollerAdvance = 0 #100 #?

#for splits
splitSpeedNumber = 100
splitStitchNumber = 4 #math.ceil(stitchNumber//2)
splitRollerAdvance = 0 #NOTE: was 300 before...

#for wasteWeights
wasteWeightsRowCount = 20

#----------------------
#--- MISC FUNCTIONS ---
#----------------------
def setSettings(speed=None, stitch=None, roller=None, xferSpeed=None, xferStitch=None, xferRoller=None, splitSpeed=None, splitStitch=None, splitRoller=None, wasteSpeed=None):
	if speed is not None: globals()['speedNumber'] = speed
	if stitch is not None: globals()['stitchNumber'] = stitch
	if roller is not None: globals()['rollerAdvance'] = roller

	if xferSpeed is not None: globals()['xferSpeedNumber'] = xferSpeed
	if xferStitch is not None: globals()['xferStitchNumber'] = xferStitch
	if xferRoller is not None: globals()['xferRollerAdvance'] = xferRoller

	if splitSpeed is not None: globals()['splitSpeedNumber'] = splitSpeed
	if splitStitch is not None: globals()['splitStitchNumber'] = splitStitch
	if splitRoller is not None: globals()['splitRollerAdvance'] = splitRoller

	if wasteSpeed is not None: globals()['wasteSpeedNumber'] = wasteSpeed


def xferSettings(k, alterations={}):
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
	k.speedNumber(speedNumber)
	k.stitchNumber(stitchNumber)
	k.rollerAdvance(rollerAdvance)


def availableCarrierCheck(usedCarriers, reusableCarriers=[]): #?
	if len(usedCarriers) == 6: raise ValueError('Not enough available carriers.')
	elif len(usedCarriers) + len(reusableCarriers) == 6:
		warnings.warn('Reusing carrier.')
		return usedCarriers[0]
	else: return None


# def convertGauge(gauge=2, leftN=None, rightN=None): #maybe move outside of this? #remove #? #v
# 	newLeftN = leftN
# 	newRightN = rightN
# 	if gauge > 1:
# 		if leftN is not None: newLeftN *= gauge
# 		if rightN is not None: newRightN = (rightN*gauge)+1

# 	if leftN is None: return newRightN
# 	elif rightN is None: return newLeftN
# 	else: return newLeftN, newRightN #remove #? #^


def convertGauge(gauge=2, leftN=None, rightN=None): #new
	newLeftN = leftN
	newRightN = rightN
	if gauge > 1:
		if leftN is not None: newLeftN = int(leftN*gauge)
		if rightN is not None: newRightN = int(rightN*gauge)
		# if rightN is not None: newRightN = (rightN*gauge)+1

	if leftN is None: return newRightN
	elif rightN is None: return newLeftN
	else: return newLeftN, newRightN


def tempMissOut(k, width, direction, c=None, buffer=None):
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
	sortedBnList = list(set(bnList.copy()))
	if direction == '-': sortedBnList.sort(key=lambda bn: int(bn[1:]), reverse=True)
	else: sortedBnList.sort(key=lambda bn: int(bn[1:]))

	return sortedBnList


def placeCarrier(k, leftN=None, rightN=None, carrierOpts=[], gauge=2, opDetails={}):
	placedCarrier = None #for now
	tuckDir = None
	tuckDrop = []

	lastOps = []

	carrierOpts = list(filter(None, carrierOpts))

	for c in carrierOpts:
		lastLineC = k.returnLastOp(carrier=c, asDict=True, **opDetails) #new #check
		# lastLineC = k.returnLastOp(carrier=c, asDict=True)
		if lastLineC is not None: lastOps.append(lastLineC)

	distances = {}
	needleNums = {}

	for ln in lastOps:
		# lastOp = {'op': op, 'direction': direction, 'bn1': {'bed': b1, 'needle': n1}, 'bn2': {'bed': b2, 'needle': n2}, 'carrier': carrier, 'rack': None}
		c = ln['carrier']

		if type(c) == list:
			for carr in c:
				if carr in carrierOpts:
					c = carr
					break

		if ln['op'] == 'in' or ln['op'] == 'out': needleNum = 0 #new #just assume 0 is the min needle (#TODO: have option for detecting min needle)
		else: needleNum = ln['bn1']['needle']
		
		needleNums[c] = needleNum

		# if leftN is not None: distances[abs(needleNum-leftN)] = {'carrier': c, 'direction': '+'}
		# if rightN is not None: distances[abs(needleNum-rightN)] = {'carrier': c, 'direction': '-'}
		if leftN is not None: distances[abs(needleNum-leftN)] = {'carrier': c, 'sideN': leftN}
		if rightN is not None: distances[abs(needleNum-rightN)] = {'carrier': c, 'sideN': rightN}
	
	if len(distances): 
		minDist = min(distances.keys())
		placedCarrier = distances[minDist]['carrier']

		if (needleNum-(distances[minDist]['sideN'])) > 0: tuckDir = '-' #new
		else: tuckDir = '+'
		
		# tuckDir = distances[minDist]['direction']

		if minDist > 5: #need to tuck to get it in correct spot
			tuckB = 0 #for tucking every other
			tuckF = 0 

			k.comment(f'tuck to move carrier from {needleNum} to {distances[minDist]["sideN"]}')

			k.rollerAdvance(0)

			if tuckDir == '+':
				# for t in range(needleNums[placedCarrier]+1, leftN):
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
				# for t in range(needleNums[placedCarrier]-1, rightN, -1):
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


def includeNSecureSides(n, secureNeedles={}, knitBed=None):
	'''
	*n is the number associated with the needle we're checking
	*secureNeedles is dict with needle numbers as key and bed as value (valid values are 'f', 'b', or 'both')
	*knitBed is the bed that is currently knitting, if applicable (because this is only checking if we can't xfer it, so if it was unable to be xferred from a certain bed, it should still be knitted on that bed); value of None indicates we are just check for xfer
	'''
	# if type(secureNeedles[0] == dict): needles = list(secureNeedles.keys())
	# else: needles = secureNeedles
	if n in secureNeedles:
		if knitBed is None: return False
		else: #for knitting
			if knitBed == secureNeedles[n]: return True
			else: return False
	else: return True


#----------------------------------------------------
#--- STANDARD KNITTING FUNCTIONS /STITCH PATTERNS ---
#----------------------------------------------------

#--- KNITTING PASSES ---
def knitPass(k, startN, endN, c, bed='f', gauge=1, emptyNeedles=[]):
	if endN > startN: #pass is pos
		for n in range(startN, endN+1):
			if f'{bed}{n}' not in emptyNeedles:
				if (bed == 'f' and n % gauge == 0) or (bed == 'b' and (gauge == 1 or n % gauge != 0)): k.knit('+', f'{bed}{n}', c) #check
				elif n == endN: k.miss('+', f'{bed}{n}', c)
				# elif bed == 'b' and (gauge == 1 or n % gauge != 0): k.knit('+', f'b{n}', c) #check
			elif n == endN: k.miss('+', f'{bed}{n}', c)
	else: #pass is neg
		for n in range(startN, endN-1, -1):
			if f'{bed}{n}' not in emptyNeedles:
				if (bed == 'f' and n % gauge == 0) or (bed == 'b' and (gauge == 1 or n % gauge != 0)): k.knit('-', f'{bed}{n}', c) #check
				elif n == endN: k.miss('-', f'{bed}{n}', c)
				# if bed == 'b' and (gauge == 1 or n % gauge != 0): k.knit('-', f'b{n}', c) #check
				# elif bed == 'f' and n % gauge == 0: k.knit('-', f'f{n}', c) #check
			elif n == endN: k.miss('-', f'{bed}{n}', c)


def jersey(k, startN, endN, length, c, currentBed='f', gauge=1, emptyNeedles=[]):
	k.comment('begin jersey')
	for p in range(0, length):
		if p % 2 == 0:
			passStartN = startN
			passEndN = endN
		else:
			passStartN = endN
			passEndN = startN
		knitPass(k, startN=passStartN, endN=passEndN, c=c, bed=currentBed, gauge=gauge, emptyNeedles=emptyNeedles)
	k.comment('end jersey') #new


#--- FUNCTION FOR KNITTING ON ALT NEEDLES, PARITY SWITCHING FOR FRONT & BACK ---
# def interlock(k, startN, endN, length, c, gauge=1, startCondition=1, emptyNeedles=[], tuckNeedles=[]): #remove #?
# def interlock(k, startN, endN, length, c, gauge=1, startCondition=1, emptyNeedles=[], currentBed=None, homeBed=None, secureStartN=False, secureEndN=False, knitAtRack=False): #TODO: maybe #remove knitAtRack
def interlock(k, startN, endN, length, c, gauge=1, startCondition=1, emptyNeedles=[], currentBed=None, homeBed=None, secureStartN=False, secureEndN=False): #TODO: maybe #remove knitAtRack
	'''Knits on every needle interlock starting on side indicated by which needle value is greater.
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
		
	length *= 2
	length = int(length) #incase doing e.g. .5 length (only a pass)

	# if knitAtRack: #TODO: maybe #remove
	# 	if (((startN//gauge) % (2*gauge)) % gauge) == 0: #means it will stay on original bed
	# 		if (currentBed == 'f' and endN > startN) or (currentBed == 'b' and startN > endN): kRack = -1
	# 		else: kRack = 1
	# 	else:
	# 		if (currentBed == 'f' and endN > startN) or (currentBed == 'b' and startN > endN): kRack = 1
	# 		else: kRack = -1

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
		if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'b': return False #new #check

		if f'f{n}' not in emptyNeedles and n % gauge == 0 and (((n//gauge) % 2) == 0):
			k.knit(direction, f'f{n}', c)
			return True
		else: return False
	
	def backBed1(n, direction):
		if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'f': return False #new #check

		if f'b{n}' not in emptyNeedles and (gauge == 1 or n % gauge != 0) and ((((n-1)//gauge) % 2) == 0):
			k.knit(direction, f'b{n}', c)
			return True
		else: return False
	
	def frontBed2(n, direction):
		if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'b': return False #new #check

		if f'f{n}' not in emptyNeedles and n % gauge == 0 and (((n//gauge) % 2) != 0):
			k.knit(direction, f'f{n}', c)
			return True
		else: return False
	
	def backBed2(n, direction):
		if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'f': return False #new #check

		if f'b{n}' not in emptyNeedles and (gauge == 1 or n % gauge != 0) and ((((n-1)//gauge) % 2) != 0):
			k.knit(direction, f'b{n}', c)
			return True
		else: return False

	if currentBed is not None: #currentBed indicates that we need to start by xferring to proper spots
		xferSettings(k)
		# if currentBed == 'both': #can't be applicable if homeBed is not None
		# 	print('TODO')
		# else:
		if currentBed == 'f':
			otherBed = 'b'
			currCondition = lambda n: (n % gauge == 0)
		else:
			otherBed = 'f'
			currCondition = lambda n: ((n-1) % gauge == 0)

		for n in range(leftN, rightN+1):
			if (n == startN and secureStartN) or (n == endN and secureEndN): continue #new #check

			if currCondition(n) and f'{currentBed}{n}' not in emptyNeedles and (((n//gauge) % (2*gauge)) % gauge) != 0: k.xfer(f'{currentBed}{n}', f'{otherBed}{n}') #new #check (especially check if works for gauge 1)
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
			else: return False #new #check

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
			else: return False #new #check

		if homeCondition(n) and f'{travelBed}{n}' not in emptyNeedles and ((n//gauge) % (2*gauge) == (gauge-1)): #check for gauge 1
			k.knit(direction, f'{travelBed}{n}', c)
			return True
		else: return False
	
	# def homeFrontBed1(n, direction):
	# 	if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'b': return False #new #check

	# 	if homeCondition(n) and f'f{n}' not in emptyNeedles and ((n//gauge) % (2*gauge) == 0): #for homeBed 'f'
	# 		k.knit(direction, f'f{n}', c)
	# 		return True
	# 	else: return False
	
	# def homeBackBed1(n, direction):
	# 	if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'f': return False #new #check

	# 	if homeCondition(n) and f'b{n}' not in emptyNeedles and (((n-1)//gauge) % (2*gauge) == gauge): #for homeBed 'f' #check
	# 		k.knit(direction, f'b{n}', c)
	# 		return True
	# 	else: return False
	
	# def homeFrontBed2(n, direction):
	# 	if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'b': return False #new #check

	# 	if f'f{n}' not in emptyNeedles and n % gauge == 0 and ((n//gauge) % (2*gauge) == gauge): #for homeBed 'f' #check
	# 		k.knit(direction, f'f{n}', c)
	# 		return True
	# 	else: return False
	
	# def homeBackBed2(n, direction):
	# 	if ((n == startN and secureStartN) or (n == endN and secureEndN)) and currentBed == 'f': return False #new #check

	# 	if homeCondition(n) and f'b{n}' not in emptyNeedles and (((n-1)//gauge) % (2*gauge) == 0): #for homeBed 'f' #check
	# 		k.knit(direction, f'b{n}', c)
	# 		return True
	# 	else: return False


	#--- the knitting ---
	# if knitAtRack: k.rack(kRack) #TODO: #remove this (or keep) after testing

	for h in range(beg, length):
		if h % 2 == 0:
			for n in range(leftN, rightN+1):
				if startCondition == 1:
					if homeBed is None:
						if frontBed1(n, '+'): continue
						elif backBed1(n, '+'): continue
						elif n == rightN: k.miss('+', f'f{n}', c)
					else:
						if homeBed1(n, '+'): continue
						elif travelBed1(n, '+'): continue
						elif n == rightN: k.miss('+', f'f{n}', c)
				else:
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
	
	# if knitAtRack: k.rack(0) #TODO: #remove this (or keep) after testing

	if homeBed is not None:
		xferSettings(k)
		for n in range(leftN, rightN+1):
			if (n == startN and secureStartN) or (n == endN and secureEndN): continue #new #check

			if currCondition(n) and f'{homeBed}{n}' not in emptyNeedles and (((n//gauge) % (2*gauge)) % gauge) != 0: k.xfer(f'{travelBed}{n}', f'{homeBed}{n}') #new #check (especially check if works for gauge 1)
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

def garter(k, startN, endN, length, c, patternRows=1, startBed='f', currentBed=None, originBed=None, homeBed=None, secureStartN=True, secureEndN=True, gauge=1): 
	'''
	*k is knitout Writer
	*startN is the starting needle to knit on
	*endN is the last needle to knit on
	*length is total passes knit
	*c is carrier
	*currentBed is the bed(s) that current has knitting (valid values are: 'f' [front], 'b' [back], and 'both'); assumes you start on the front bed, unless otherwise indicated
	*startBed is the bed to start on
	*homeBed is the bed to transfer the loops back to at the end (if applicable)
	*secureStartN and *secureEndN are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
	*gauge is... gauge
	'''

	if currentBed is None: currentBed = startBed
	if originBed is None: originBed = currentBed
	# initialBed = currentBed
	# if homeBed is not None: initialBed = homeBed
	# else:  
	k.comment('begin garter')
	# k.comment(f'secureStartN: {secureStartN}, secureEndN: {secureEndN}') #remove #debug

	# extraPass = False #TODO #*#*#*
	# length = length/2
	# if length % 1 != 0: extraPass = True
	# length = math.ceil(length)
	
	# if patternRows > 1:
	# 	length = length/patternRows
	# 	if length % 1 != 0: extraPass = True
	# 	length = math.ceil(length)
	# elif length % 2 != 0: 
	# print(length, extraPass)

	# if gauge == 1: #remove #? #v
	# 	shift1 = 0
	# 	shift2 = 0 #remove #? #^

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
		# originBedStartN, otherBedStartN = startN, otherStartN
	else:
		secureNeedles[startN] = otherBed
		secureNeedles[otherStartN] = originBed
		# otherBedStartN, originBedStartN = startN, otherStartN
	
	if (endN % 2 == 0 and originBed == 'f') or ((endN+1) % 2 == 0 and originBed == 'b'):
		secureNeedles[endN] = originBed
		secureNeedles[otherEndN] = otherBed
		# originBedEndN, otherBedEndN = endN, otherEndN
	else:
		secureNeedles[endN] = otherBed
		secureNeedles[otherEndN] = originBed
		# otherBedEndN, originBedEndN = endN, otherEndN
	
	# def includeN(n, currBed=None):
	# 	# if (n == startN and secureStartN) or (n == endN and secureEndN):
	# 	if (secureStartN and (n == startN or (gauge == 2 and n == otherStartN))) or (secureEndN and (n == endN or (gauge == 2 and n == otherEndN))): #new
	# 		if currBed is None: return False
	# 		else:
	# 			if n == originBedStartN or n == originBedEndN:
	# 				if currBed == originBed: return True
	# 				else: return False
	# 			else: #otherBedStartN or otherBedEndN
	# 				if currBed != originBed: return True
	# 				else: return False
	# 			# if currBed == initialBed: return True
	# 			# if currBed == originBed: return True
	# 			# else: return False
	# 	else: return True
	# 	# if n == startN or n == endN: return False
	# 	# elif gauge > 1 and ((dir1 == '+' and (n == startN+1 or n == endN-1)) or (dir1== '-' and (n == startN-1 or n == endN+1))): return False
	# 	# else: return True

	# if homeBed == 'b' or (homeBed is None and currentBed == 'b'):
	if homeBed == 'b' or (homeBed is None and originBed == 'b'):
		condition = lambda n: (n % gauge != 0 or gauge == 1)
	else:
		condition = lambda n: n % gauge == 0
	
	if startBed == 'b':
		bed1 = 'b'
		bed2 = 'f'

		# if gauge > 1: #remove #? #v
		# 	shift1 = -1
		# 	shift2 = 1

		# condition1 = lambda n: (n % gauge != 0 or gauge == 1)
		# condition2 = lambda n: n % gauge == 0 #remove #? #^

		if currentBed != 'b':
			if currentBed == 'both' and gauge > 1:
				shift = 1
				k.rack(-1)
			else: shift = 0
			# if gauge > 1: k.rack(-1) #remove #?

			xferSettings(k)

			for n in range1:
				if condition(n) and includeNSecureSides(n, secureNeedles=secureNeedles): k.xfer(f'f{n}', f'b{n+shift}') #new #check
				# if condition(n) and includeN(n): k.xfer(f'f{n}', f'b{n+shift}')

			if currentBed == 'both' and gauge > 1: k.rack(0) #remove #?
			# if gauge > 1: k.rack(0) #remove #?

			resetSettings(k)
			currentBed = 'b'
	else: #front or both
		bed1 = 'f'
		bed2 = 'b'

		# if gauge > 1: #remove #? #v
		# 	shift1 = 1
		# 	shift2 = -1

		# condition1 = lambda n: n % gauge == 0
		# condition2 = lambda n: (n % gauge != 0 or gauge == 1) #remove #? #^

		# if startBed == 'both': #both
		if currentBed != 'f': #both
			if currentBed == 'both' and gauge > 1:
				shift = -1
				k.rack(-1)
			else: shift = 0

			# if gauge > 1: k.rack(-1) #remove #?

			xferSettings(k)
			for n in range1:
				if condition(n) and includeNSecureSides(n, secureNeedles=secureNeedles): k.xfer(f'b{n}', f'f{n+shift}') #new #check
				# if condition(n) and includeN(n): k.xfer(f'b{n}', f'f{n+shift}')

			# if gauge > 1: k.rack(0) #remove #?
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
					# if includeN(n, bed1): k.knit(direction, f'{bed1}{n}', c)
					if includeNSecureSides(n, secureNeedles=secureNeedles, knitBed=bed1): k.knit(direction, f'{bed1}{n}', c) #new #check #*#*#*
					# else: k.miss(direction, f'{bed2}{n}', c)
					else: k.knit(direction, f'{bed2}{n}', c)
				elif n == endN: k.miss(direction, f'{bed1}{n}', c) #new #option 2: elif n == list(needleRange)[-1]
				# elif n == startN: k.miss(direction, f'{bed1}{n}', c)
				# if condition1(n): k.knit(direction, f'{bed1}{n}', c) #remove #?

			if direction == dir1: direction = dir2
			else: direction = dir1 #remove #?
			if needleRange == range1: needleRange = range2 #TODO: maybe just make it needleRange = range2 since it will always be that?
			else: needleRange = range1 #remove #?

			passCt += 1
			if passCt == length: break #new

		# if passCt == length and ((not returnXfers) or (currentBed == startBed)): break #new
		if passCt == length and ((homeBed is None) or (currentBed == homeBed)): break #new

		xferSettings(k)
			
		# if gauge > 1: k.rack(-1) #remove #?

		for n in range1:
			if condition(n) and includeNSecureSides(n, secureNeedles=secureNeedles): k.xfer(f'{bed1}{n}', f'{bed2}{n}') #new #heck
			# if condition(n) and includeN(n): k.xfer(f'{bed1}{n}', f'{bed2}{n}')

		# if gauge > 1: k.rack(0) #remove #?

		currentBed = bed2 #new #*#*#*
		resetSettings(k)

		# if l == length-1 and extraPass: break #new
		if passCt == length: break #new

		for r in range(0, patternRows):
			for n in needleRange:
				if condition(n):
					if includeNSecureSides(n, secureNeedles=secureNeedles, knitBed=bed2): k.knit(direction, f'{bed2}{n}', c) #new #check
					# if includeN(n, bed2): k.knit(direction, f'{bed2}{n}', c) #new #*#*#*
					# else: k.miss(direction, f'{bed1}{n}', c) #new #*#*#*
					else: k.knit(direction, f'{bed1}{n}', c) #new #*#*#*
				elif n == startN: k.miss(direction, f'{bed2}{n}', c) #new #option 2: elif n == list(needleRange)[-1]
				# elif n == endN: k.miss(direction, f'{bed2}{n}', c)
				# if condition2(n): k.knit(direction, f'{bed2}{n}', c) #remove #?

			if direction == dir1: direction = dir2 #remove #?
			else: direction = dir1
			if needleRange == range1: needleRange = range2 #remove #? #^
			else: needleRange = range1 #TODO: maybe just make it needleRange = range1 since it will always be that?

			passCt += 1
			if passCt == length: break #new
		
		# if passCt == length and ((not returnXfers) or (currentBed == startBed)): break #new
		if passCt == length and ((homeBed is None) or (currentBed == homeBed)): break

		xferSettings(k)

		# if gauge > 1: k.rack(-1) #remove #?

		for n in range2:
			if condition(n) and includeNSecureSides(n, secureNeedles=secureNeedles): k.xfer(f'{bed2}{n}', f'{bed1}{n}') #new #check
			# if condition(n) and includeN(n): k.xfer(f'{bed2}{n}', f'{bed1}{n}')

		# if gauge > 1: k.rack(0) #remove #?

		currentBed = bed1 #new #*#*#*

		resetSettings(k)

		if passCt == length: break #new

	k.comment('end garter') #new

	nextDirection = direction
	if nextDirection == '+': nextSide = 'l'
	else: nextSide = 'r'

	return nextSide #so know where carrier is at (note: will be *next* direction)
	# return nextDirection #so know where carrier is at (note: will be *next* direction)


def lace(k, startN, endN, length, c, patBeg=0, patternRows=2, spaceBtwHoles=1, offset=1, offsetStart=0, offsetReset=None, currentBed='f', gauge='1', secureStartN=True, secureEndN=True): #TODO: ensure it works well for gauge 2
	'''
	*k is the knitout Writer
	*startN is the first needle to knit on in first pass
	*endN is the last needle to knit on in first pass
	*length is the total number of rows
	*c is the carrier
	*patBeg is the pass number to start at (useful for if using this function in cactus and need to prevent reseting xfer pattern)
	*patternRows is the number of rows between xfers to form new holes
	spaceBtwHoles is the number of needles that are skipped btw xfers to form the lace holes
	*offset is the shift in lace hole placement for alternating rows (e.g. offset=0 would stack lace holes directly ontop of one another [NOTE: requires patternRows to have minimum value of 2], offset=1 would be checkerboard pattern, etc.)
	*offsetStart is *TODO
	*offsetReset is the number of rows after which the offset is set back to the beginning (if None, will just reset once offset automatically resets)
	*currentBed is the needle bed where the main knitting will occur (other bed wil be used for xfers)
	*gauge is gauge
	'''
	# if offset == 0 and patternRows < 2:
	# 	patternRows = 2 #new
	# 	print('\nwarning: changing patternRows to 2 so lace holes can still form with offset of 0')

	if patBeg == 1 and length == 1: length += 1 #new

	if patternRows < 2:
		patternRows = 2 #new
		print('\nwarning: changing patternRows to 2 so lace holes can properly form.')

	if currentBed == 'f':
		# rack1 = gauge
		# rack2 = -gauge
		rack1 = -gauge
		rack2 = gauge
		# rack1 = 1
		# rack2 = -1
		bed2 = 'b'
	else:
		# rack1 = -gauge
		# rack2 = gauge
		rack1 = gauge
		rack2 = -gauge
		# rack1 = -1
		# rack2 = 1
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
	
	# laceStitch = math.ceil(stitchNumber/2)
	laceStitch = stitchNumber+3
	if laceStitch > 9: laceStitch = 9
	k.comment(f'begin lace')
	
	xferPasses = 0
	# mod = 0
	mod = offsetStart
	# for p in range(0, length):
	for p in range(patBeg, length):
		if (p-patBeg) % 2 == 0:
			direction = dir1
			lastN = endN
		else:
			direction = dir2
			lastN = startN

		if p % patternRows == 0:
			# if currentBed == 'f': print('\n', mod*gauge) #remove #debug
			# k.xferStitchNumber(stitchNumber)
			k.stitchNumber(stitchNumber)
			if gauge == 1:
				if xferPasses % 2 == 0: rack = rack1
				else: rack = rack2
				shift = rack
			else:
				rack = rack1 #check
				shift = -gauge

			xferPasses += 1

			for n in ranges[dir1]:
				# if currentBed == 'f' and n%gauge == 0: print(n, (n - startN) % (gauge*(spaceBtwHoles+1))) #remove #debug
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
			elif n == lastN: k.miss(direction, f'f{n}', c) #new #check
		
		k.stitchNumber(stitchNumber)
		# k.xferStitchNumber(xferStitchNumber)
	k.comment(f'end lace')

# def rib(k, startN, endN, length, c, currentBed=None, homeBed=None, secureStartN=True, secureEndN=True, sequence='fb', offset=False, gauge=2):
def rib(k, startN, endN, length, c, currentBed='f', originBed=None, homeBed=None, secureStartN=True, secureEndN=True, sequence='fb', gauge=1):
	'''
	*k is the knitout Writer
	*endN is the last needle
	*startN is the first needle
	*currentBed is the bed(s) that current has knitting (valid values are: 'f' [front], 'b' [back], and 'both'); if value is None, will assume that the loops are already in position for rib
	*homeBed is the bed to transfer the loops back to at the end (if applicable); NOTE: this should only be added if knitting if half gauge tube will stitch patterns inserted on one bed (since the function will act accordingly)
	*secureStartN and *secureEndN are booleans that indicate whether or not we should refrain from xferring the edge-most needles, for security (NOTE: this should be True if given edge needle is on the edge of the piece [rather than in the middle of it])
	*sequence is the repeating rib pattern (e.g. 'fb' of 'bf' for 1x1 [first bed indicates which bed left-most needle will be on], 'ffbb' for 2x2, 'fbffbb' for 1x1x2x2, etc.)
	*gauge is gauge
	# *offset is a boolean that indicates whether something is happening like half gauge tube so need to xfer with no rack and then knit with rack #TODO write this better #remove actually don't need this
	'''

	k.comment(f'begin rib ({sequence})')

	# secureSequence = sequence #to change / return

	if originBed is None: originBed = currentBed

	if gauge > 1: #new
		gaugedSequence = ''
		for char in sequence:
			gaugedSequence += char * gauge
		sequence = gaugedSequence
	
	# def bedConditions(bed, n):
	def bedConditions(n):
		# if originBed is not None: bed = originBed #new 
		# if homeBed is not None: bed = homeBed #new 
		# if bed == 'f':
		if originBed == 'f':
			if n % gauge == 0: return True
			else: return False
		else:
			if (n+1) % gauge == 0: return True
			else: return False
	# conditions = {'f': lambda n: n % gauge == 0, 'b': lambda n: (n+1) % gauge == 0}

	if endN > startN: #first pass is pos
		dir1 = '+'
		dir2 = '-'
		otherEndN = endN-1 #for gauge 2
		otherStartN = startN+1
		# leftN = startN
		ranges = {dir1: range(startN, endN+1), dir2: range(endN, startN-1, -1)}
	else: #first pass is neg
		dir1 = '-'
		dir2 = '+'
		otherEndN = endN+1 #for gauge 2
		otherStartN = startN-1
		# leftN = endN
		ranges = {dir1: range(startN, endN-1, -1), dir2: range(endN, startN+1)}


	secureNeedles = {}
	if originBed == 'f': otherBed = 'b'
	else: otherBed = 'f'

	# switchBeds = str.maketrans('fb', 'bf')
	if (startN % 2 == 0 and originBed == 'f') or ((startN+1) % 2 == 0 and originBed == 'b'):
		secureNeedles[startN] = originBed
		secureNeedles[otherStartN] = otherBed
		# if sequence[startN % len(sequence)] == otherBed: secureSequence = sequence.translate(switchBeds)
	else:
		secureNeedles[startN] = otherBed
		secureNeedles[otherStartN] = originBed
		# if sequence[otherStartN % len(sequence)] == otherBed: secureSequence = sequence.translate(switchBeds)
	
	if (endN % 2 == 0 and originBed == 'f') or ((endN+1) % 2 == 0 and originBed == 'b'):
		secureNeedles[endN] = originBed
		secureNeedles[otherEndN] = otherBed
	else:
		secureNeedles[endN] = otherBed
		secureNeedles[otherEndN] = originBed

	# xferEndN = True
	# xferStartN = True
	if currentBed is not None: #currentBed indicates that we need to start by xferring to proper spots
		# switchBeds = str.maketrans('fb', 'bf')
		# if secureStartN: #TODO: ensure this doesn't cause any issues with shaping rib
		# 	if dir1 == '+':
		# 		if sequence[0] == currentBed: sequence = sequence.translate(switchBeds)
		# 	else: xferStartN = False
		
		# if secureEndN:
		# 	if dir1 == '-':
		# 		if sequence[0] == currentBed: sequence = sequence.translate(switchBeds)
		# 	else: xferEndN = False

		xferSettings(k)
		if currentBed == 'both': #can't be applicable if homeBed is not None
			# xferEndN = True #change these back to true because can't have loops on both beds directly across from each other
			# xferStartN = True
			# s = startN
			for n in ranges[dir1]: #TODO: adjust for gauge
				if bedConditions(n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{currentBed}{n}', f'{otherBed}{n}')
				# if (n == startN and not xferStartN) or (n == endN and not xferEndN): continue
				# else:
				# 	if bedConditions(n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{currentBed}{n}', f'{otherBed}{n}')
					# 
					# if bedConditions('b', n) and (sequence[(n-leftN) % len(sequence)] == 'f'): k.xfer(f'b{n}', f'f{n}')
					# elif bedConditions('f', n) and (sequence[(n-leftN) % len(sequence)] == 'b'): k.xfer(f'f{n}', f'b{n}')

					# if bedConditions('b', n) and (sequence[n % len(sequence)] == 'f'): k.xfer(f'b{n}', f'f{n}')
					# elif bedConditions('f', n) and (sequence[n % len(sequence)] == 'b'): k.xfer(f'f{n}', f'b{n}')
		else:
			# if currentBed == 'f': otherBed = 'b'
			# else: otherBed = 'f'
			for n in ranges[dir1]: #TODO: adjust for gauge
				if includeNSecureSides(n, secureNeedles=secureNeedles):
					if bedConditions(n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{currentBed}{n}', f'{otherBed}{n}')
				# if (n == startN and not xferStartN) or (n == endN and not xferEndN): continue
				# else:
				# 	if bedConditions(currentBed, n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{currentBed}{n}', f'{otherBed}{n}')
				# 	# if bedConditions(currentBed, n) and (sequence[(n-leftN) % len(sequence)] == otherBed): k.xfer(f'{currentBed}{n}', f'{otherBed}{n}')
				# 	# if sequence[(n-leftN) % len(sequence)] == otherBed: k.xfer(f'{currentBed}{n}', f'{otherBed}{n}')
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
			# if sequence[(n-leftN) % len(sequence)] == 'f': #remove
			if sequence[n % len(sequence)] == 'f':
				if bedConditions(n):
					if includeNSecureSides(n, secureNeedles=secureNeedles, knitBed='f'): k.knit(direction, f'f{n}', c) #xferred it or originBed == 'f', ok to knit
					else: k.knit(direction, f'b{n}', c) #if didn't xfer this, knit on the bed it started on
				elif n == lastN: k.miss(direction, f'f{n}', c) #new #check

				# if currentBed == 'b' and ((n == startN and not xferStartN) or (n == endN and not xferEndN)):
				# 	if bedConditions('b', n):
				# 		k.knit(direction, f'b{n}', c) #if didn't xfer this, knit on the bed it started on 
				# 	elif n == lastN: k.miss(direction, f'f{n}', c) #new #check
				# elif bedConditions('f', n): k.knit(direction, f'f{n}', c)
				# elif n == lastN: k.miss(direction, f'f{n}', c) #new #check
			else: #sequence == 'b'
				if bedConditions(n):
					if includeNSecureSides(n, secureNeedles=secureNeedles, knitBed='b'): k.knit(direction, f'b{n}', c) #xferred it or originBed == 'b', ok to knit
					else: k.knit(direction, f'f{n}', c) #if didn't xfer this, knit on the bed it started on
				elif n == lastN: k.miss(direction, f'b{n}', c) #new #check

				# if currentBed == 'f' and ((n == startN and not xferStartN) or (n == endN and not xferEndN)):
				# 	if bedConditions('f', n):
				# 		k.knit(direction, f'f{n}', c)
				# 	elif n == lastN: k.miss(direction, f'f{n}', c) #new #check
				# elif bedConditions('b', n): k.knit(direction, f'b{n}', c)
				# elif n == lastN: k.miss(direction, f'f{n}', c) #new #check
	
	if homeBed is not None:
		if homeBed == 'f': otherBed = 'b'
		else: otherBed = 'f'
		xferSettings(k)
		for n in ranges[dir1]: #TODO: adjust for gauge
			if includeNSecureSides(n, secureNeedles=secureNeedles):
					if bedConditions(n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{otherBed}{n}', f'{homeBed}{n}')
			# if (n == startN and not xferStartN) or (n == endN and not xferEndN): continue
			# else:
			# 	if bedConditions(homeBed, n) and (sequence[n % len(sequence)] == otherBed): k.xfer(f'{otherBed}{n}', f'{homeBed}{n}') #check bedConditions(homeBed, n)
			# 	# if bedConditions(homeBed, n) and (sequence[(n-leftN) % len(sequence)] == otherBed): k.xfer(f'{otherBed}{n}', f'{homeBed}{n}') #check bedConditions(homeBed, n)
		resetSettings(k)
	k.comment(f'end rib')

# def stitchPatternTube(k, pattern, leftN, rightN, length, c, side='l', patFuncArgs={}):
def stitchPatternTube(k, leftN, rightN, c, wasteC='1', drawC='2', featureCs=[], side='l', patterns=[], defaultLength=None, wasteDivider=False):
	'''
	*k is knitout Writer
	*leftN is the left-most needle to knit on
	*rightN is the right-most needle to knit on
	*c is the carrier to knit with
	*wasteC is the carrier to use for the waste section; if None, won't add any waste sections
	*drawC is the carrier to use for the draw thread
	*featureCs is a list of any carriers that might be used for special features (for now, the only use case would be if plaiting were to occur)
	*side is the side the start on (valid values are 'l' [left] and 'r' [right])
	*patterns is a list of patterns to make tubes for; can be a string specifying which stitch pattern to use (should match the function name for that specific pattern [which should, in turn, simply be the pattern name]); note that 'jersey' is fine for circular (either will work)
		- can also be a sub-list with pattern name as the first element and a dict with args specific to the pattern's function/additional info as value
			- do this^ if want to knit a bunch of tubes with different stitch patterns; in this case, a waste section will be inserted in between them
			- in the case of a dict, this would pass additional specifications for the given pattern, specific to that pattern and the parameters in its function. The key should be the parameter name (as a string) and the value should be the value you're passing for it. These are the parameters that you might include for certain patterns:
				- garter: 'patternRows'
				- lace: 'patternRows'
				- rib: 'sequence'
				- **for ANY pattern, can also include the following information:
					- 'length' which is the number of passes on either bed (will override the defaultLength)
					- 'plaiting' which indicates plaiting will be used for the stitch pattern (in which case, the additional plaiting carrier should be included in featureCs, and front/back bed will knit in intervals of 3 passes each, with plaiting occurring for first two passes and normal for last [so that plaiting carrier can consistently live on the same side, since knitting circularly])
	*defaultLength is the number of passes on either bed that will automatically be used if no 'length' is specified in a pattern's dict	
	
	knits a half gauge tube in the stitch pattern
	'''
	if wasteC is None: wasteDivider = False #just in case the user made a mistake

	# if c != drawC and c != wasteC: otherCs.append(c)
	gauge = 2

	otherCs = featureCs.copy()
	if c != drawC and c != wasteC: otherCs.append(c)
	
	plaitCs = featureCs.copy()
	if len(featureCs):
		if drawC in otherCs: otherCs.remove(drawC)
		if wasteC in otherCs: otherCs.remove(wasteC)
		if len(plaitCs) > 1: endOnRight = [plaitCs[1]]
		else: endOnRight = [] #just plaiting on the front
			# else: raise ValueError(f"Not enough carriers provided for plaiting.") #TODO: add option of just plaiting on one bed
	else: endOnRight = []

	# wasteSection(k, leftN=leftN, rightN=rightN, wasteC=wasteC, drawC=drawC, otherCs=otherCs, gauge=2, endOnRight=endOnRight, initial=True, drawMiddle=wasteDivider)

	# if c != drawC:
	# 	if drawC in endOnRight: k.miss('+', f'f{rightN+3}', drawC)
	# 	else: k.miss('-', f'f{leftN-3}', drawC)
	# if c != wasteC: 
	# 	if wasteC in endOnRight: k.miss('+', f'f{rightN+3}', wasteC)
	# 	else: k.miss('-', f'f{leftN-3}', wasteC)

	for idx, pat in enumerate(patterns):
		# if wasteDivider and idx != 0:
		# 	wasteSection(k, leftN=leftN, rightN=rightN, wasteC=wasteC, drawC=drawC, otherCs=otherCs, gauge=2, endOnRight=endOnRight, initial=False, drawMiddle=wasteDivider)

		# 	if c != drawC:
		# 		if drawC in endOnRight: k.miss('+', f'f{rightN+3}', drawC)
		# 		else: k.miss('-', f'f{leftN-3}', drawC)
		# 	if c != wasteC: 
		# 		if wasteC in endOnRight: k.miss('+', f'f{rightN+3}', wasteC)
		# 		else: k.miss('-', f'f{leftN-3}', wasteC)

		passCt = 80 #if nothing specified

		if defaultLength is not None: passCt = defaultLength*2

		frontPlaitC = c
		backPlaitC = c

		missDrawC = True
		missWasteC = True
		# resetStitch = False
		if type(pat) == str:
			pattern = pat
			patFuncArgs = {}
			info = {}
		else:
			pattern = pat[0]
			info = pat[1].copy()
			patFuncArgs = pat[1]
			if 'length' in patFuncArgs:
				# length = patFuncArgs['length']
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
			if 'stitchNumber' in patFuncArgs:
				# k.stitchNumber(patFuncArgs['stitchNumber'])
				del patFuncArgs['stitchNumber'] #so don't use it in get_parameters
				# resetStitch = True
		
		if wasteDivider and idx != 0:
			wasteSection(k, leftN=leftN, rightN=rightN, wasteC=wasteC, drawC=drawC, otherCs=otherCs, gauge=2, endOnRight=endOnRight, initial=False, drawMiddle=wasteDivider)

			if c != drawC and missDrawC:
				if drawC in endOnRight: k.miss('+', f'f{rightN+3}', drawC)
				else: k.miss('-', f'f{leftN-3}', drawC)
			if c != wasteC and missWasteC: 
				if wasteC in endOnRight: k.miss('+', f'f{rightN+3}', wasteC)
				else: k.miss('-', f'f{leftN-3}', wasteC)
		elif idx == 0 and wasteC is not None:
			wasteSection(k, leftN=leftN, rightN=rightN, wasteC=wasteC, drawC=drawC, otherCs=otherCs, gauge=2, endOnRight=endOnRight, initial=True, drawMiddle=wasteDivider)

			if c != drawC and missDrawC:
				if drawC in endOnRight: k.miss('+', f'f{rightN+3}', drawC)
				else: k.miss('-', f'f{leftN-3}', drawC)
			if c != wasteC and missWasteC: 
				if wasteC in endOnRight: k.miss('+', f'f{rightN+3}', wasteC)
				else: k.miss('-', f'f{leftN-3}', wasteC)

		if 'stitchNumber' in info: k.stitchNumber(info['stitchNumber'])

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
				passCt += 3 #new #check
			
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

			args = get_parameters(stitchPatFunc)

			argsF = args.copy() #new
			argsB = args.copy() #new

			argsF['startN'], argsF['endN'] = leftN, rightN #new
			argsB['startN'], argsB['endN'] = rightN, leftN #new

			# print(pattern, args) #remove #debug

			if 'patternRows' in args: patternRows = args['patternRows']
			else: patternRows = None

			if 'startCondition' in args:
				startCondition = args['startCondition']
				startConF = startCondition
				startConB = startCondition
			else: startCondition = None

			if pattern == 'rib' and args['secureStartN'] == True:
				switchBeds = str.maketrans('fb', 'bf')
				seq = args['sequence']

				# stLeftN = leftN
				# stRightN = rightN
				# if stLeftN % 2 != 0: stLeftN += 1
				# if stRightN % 2 == 0: stRightN -= 1
				# if seq[stLeftN % len(seq)] != 'f': argsF['sequence'] = seq.translate(switchBeds) #new #check
				# if seq[stRightN % len(seq)] != 'b': argsB['sequence'] = seq.translate(switchBeds) #new #check
				if seq[leftN % len(seq)] == 'f': argsF['sequence'] = seq.translate(switchBeds) #switch beds since secureStartN means it will stay on the bed #new #check
				if seq[rightN % len(seq)] == 'b': argsB['sequence'] = seq.translate(switchBeds) #new #check

				# if side == 'l': #bed will automatically be f (for now)
				# 	stStartN = leftN
				# 	if stStartN % 2 != 0: stStartN += 1
				# 	if seq[stStartN % len(seq)] != 'f': args['sequence'] = seq.translate(switchBeds) #new #check

				# 	stEndN = rightN
				# 	if stEndN % 2 == 0: stEndN -= 1

				# 	# if (bed == 'f' and stStartN % 2 != 0) or (bed == b and stStartN % 2 == 0): stStartN += 1 #TODO: add back when have option for diff stitch patterns on either bed
				# else: #bed will automatically be b 
				# 	stStartN = rightN
				# 	if stStartN % 2 == 0: stStartN -= 1
				# 	if seq[stStartN % len(seq)] != 'b': args['sequence'] = seq.translate(switchBeds) #new #check
				# 	# if (bed == 'f' and stStartN % 2 != 0) or (bed == b and stStartN % 2 == 0): stStartN -= 1

				# # if seq[stStartN % len(seq)] != bed: args['sequence'] = seq.translate(switchBeds) #new #check

			# def setValues(args_vals={}):
			def setValues(argBed, args_vals={}):
				for key in args_vals:
					if key in argBed: argBed[key] = args_vals[key]
					# if key in args: args[key] = args_vals[key]

			# def get_parameters(func):
			# 	toSet = ['startBed', 'currentBed', 'homeBed', 'patternRows', 'patBeg']

			# 	keys = func.__code__.co_varnames[:func.__code__.co_argcount][::-1]
			# 	sorter = {j: i for i, j in enumerate(keys[::-1])}
				
			# 	params = sorted([i for i in keys if i in toSet], key=sorter.get)
			# 	return params

			# if 'currentBed' in params: patFuncArgs['currentBed'] = None #to be set
			# params = list(filter(lambda p: p == 'startBed' or p == 'currentBed' or p == 'homeBed' or p == 'patternRows' or p == 'patBeg', params)

			#sorted_args = {i: 'undefined' for i in sorted(keys, key=sorter.get) if i not in alreadyCovered}

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
					# startN = leftN
					# endN = rightN
					if patternRows is not None:
						offsetStart = patBegF #whatever the previous patBeg was #check
						patBegF = patRowsF % patternRows #new
						# patBeg = patternRows - (patRowsF % patternRows) #new
						if patRowsF % patternRows == 0:
							if startBedF == 'b': startBedF = 'f'
							else: startBedF = 'b'
						patRowsF += 1
					if startCondition is not None:
						if startConF == 1: startConF = 2
						else: startConF = 1
						args['startCondition'] = startConF

					setValues(argsF, {'startBed': startBedF, 'currentBed': currentBed, 'originBed': currentBed, 'homeBed': currentBed, 'patBeg': patBegF, 'offsetStart': offsetStart})
					# setValues({'startBed': startBedF, 'currentBed': currentBed, 'originBed': currentBed, 'homeBed': currentBed, 'patBeg': patBegF, 'offsetStart': offsetStart})

					# if 'currentBed' in args: args['currentBed'] = 'f'
				else: #neg back bed
					currentBed = 'b'
					currArgs = argsB
					# startN = rightN
					# endN = leftN
					if patternRows is not None:
						offsetStart = patBegB #whatever the previous patBeg was #check
						patBegB = patRowsB % patternRows #new
						# patBeg = patternRows - (patRowsB % patternRows) #new
						if patRowsB % patternRows == 0:
							if startBedB == 'b': startBedB = 'f'
							else: startBedB = 'b'
						patRowsB += 1
					if startCondition is not None:
						if startConB == 1: startConB = 2
						else: startConB = 1
						args['startCondition'] = startConB
					
					setValues(argsB, {'startBed': startBedB, 'currentBed': currentBed, 'originBed': currentBed, 'homeBed': currentBed, 'patBeg': patBegB, 'offsetStart': offsetStart})
					# setValues({'startBed': startBedB, 'currentBed': currentBed, 'originBed': currentBed, 'homeBed': currentBed, 'patBeg': patBegB, 'offsetStart': offsetStart})

				k.comment(f'insert stitch pattern for bed {currentBed}')
				
				stitchPatFunc(k, length=(0.5 if pattern == 'interlock' else 1), c=c, **currArgs)
				# stitchPatFunc(k, startN=startN, endN=endN, length=(0.5 if pattern == 'interlock' else 1), c=c, **args)
			
			if 'stitchNumber' in info: k.stitchNumber(stitchNumber) #reset


# def wasteBorder(k, startN, endN, rows, c, widthL=4, widthR=4, gauge=2, emptyNeedles=[], offLimits=[], firstTime=False, lastTime=False, justTuck=False, shift=0, missN=None, tuckOver=[[], []]): #TODO: move this somewhere else in file (to a section where it fits better)
def wasteBorder(k, startN, endN, rows, c, widthL=4, widthR=4, gauge=2, emptyNeedles=[], offLimits=[], firstTime=False, lastTime=False, justTuck=False, tuckNs=[], missN=None, tuckOver=[[], []]): #TODO: move this somewhere else in file (to a section where it fits better)
	'''
	*k is the knitout Writer
	*startN is the needle closest to the main swatch that is meant to be knitted as part of the waste border on the side that will start on
	*endN is the needle closest to the main swatch that is meant to be knitted as part of the waste border on the side that will end on
	*c is carrier to use for waste border
	*gauge is... gauge
	*emptyNeedles is an optional list of needles that are not currently holding loops (e.g. if using stitch pattern); these needles are eligible to be tucked on
	*offLimits is an optional list of needles that are are 'off limits' for being knitted/tucked on
	*firstTime is a boolean that indicates whether or not the waste border is being knitted for the first time and a caston needs to be included
	*lastTime is a boolean that indicates whether or not the waste border is being knitted for the last time and the loops need to be dropped
	*justTuck is *TODO
	*shift is *TODO
	*missN is *TODO
	*tuckOver is *TODO

	NOTE: should have carrier by startN before adding border
	'''	
	k.rollerAdvance(0)
	nextTuck = []

	if endN > startN: #first pass is pos, so starting on left side
		dir1 = '-'
		dir2 = '+'
		side1 = 'l'
		side2 = 'r'
		leftN = startN
		rightN = endN
		tuckRange = range(startN+1, endN)
	else: #first pass is neg, so starting on right side
		dir1 = '+'
		dir2 = '-'
		side1 = 'r'
		side2 = 'l'	
		rightN = startN
		leftN = endN
		tuckRange = range(startN-1, endN, -1)

	startBeds = {}  #remove #?
	endBeds = {}  #remove #?
	interlockStart = {}

	if leftN % 2 == 0: #have *last* stitch knitted in waste border on left side be on front bed if leftN is even (meaning 1st empty needle to be tucked on would be odd) so it makes a diagonal when tucked thru/out main knitting
		startBeds['l'] = 'f' #remove #?
		endBeds['l'] = 'f' #remove #?

		if ((leftN//gauge) % 2) == 0: interlockStart['l'] = 2 #the way the interlock func code is written, ((leftN//gauge) % 2) == 0 [which corresponds with frontBed1 func] should happen second time around, so start with frontBed2 func
		else: interlockStart['l'] = 1

	else: #last stitch on left side should be on back bed
		startBeds['l'] = 'b' #remove #?
		endBeds['l'] = 'b' #remove #?

		if (((leftN-1)//gauge) % 2) == 0: interlockStart['l'] = 2 #the way the interlock func code is written, (((leftN-1)//gauge) % 2) == 0 [which corresponds with backBed1 func] should happen second time around, so start with backBed2 func
		else: interlockStart['l'] = 1
	
	if rightN % 2 == 0: #have *first* stitch knitted in waste border on right side before tucking in middle be on front bed if rightN is even so it makes a diagonal after tucked thru/out main knitting
		startBeds['r'] = 'f' #remove #?
		endBeds['r'] = 'f' #otherwise, on back bed if endN is odd so #remove #?

		if ((rightN//gauge) % 2) == 0: interlockStart['r'] = 2 #the way the interlock func code is written, ((rightN//gauge) % 2) == 0 [which corresponds with frontBed1 func] should happen second time around, so start with frontBed2 func
		else: interlockStart['r'] = 1
	else:
		startBeds['r'] = 'b' #remove #?
		endBeds['r'] = 'b' #remove #?

		if (((rightN-1)//gauge) % 2) == 0: interlockStart['r'] = 2 #the way the interlock func code is written, (((rightN-1)//gauge) % 2) == 0 [which corresponds with backBed1 func] should happen second time around, so start with backBed2 func
		else: interlockStart['r'] = 1

	needles = {'l': [leftN, leftN-widthL], 'r': [rightN, rightN+widthR]}
	ranges1 = {'l': range(leftN, leftN-widthL-1, -1), 'r': range(rightN, rightN+widthR+1)} #remove #?
	ranges2 = {'l': range(leftN-widthL, leftN+1), 'r': range(rightN+widthR, rightN-1, -1)} #remove #?
	
	tuckOverCaston = [item for sublist in tuckOver[1] for item in sublist]

	if firstTime: #caston if first time
		if dir2 == '+':
			castonBed1 = 'f'
			castonBed2 = 'b'
			condition1 = lambda n: n % gauge == 0
			condition2 = lambda n: (n % gauge != 0 or gauge == 1)
		else:
			castonBed1 = 'b'
			castonBed2 = 'f'
			condition1 = lambda n: (n % gauge != 0 or gauge == 1)
			condition2 = lambda n: n % gauge == 0

	def castonFirstTime(castonR):
		k.comment('cast-on to start waste border')
		k.rack(0.25)
		# for n in castonRange:
		for n in castonR:
			if condition1(n):
				if f'{castonBed1}{n}' not in offLimits: k.knit(dir2, f'{castonBed1}{n}', c)
			if condition2(n):
				if f'{castonBed2}{n}' not in offLimits: k.knit(dir2, f'{castonBed2}{n}', c)
		k.rack(0)

		
	if not justTuck:
		sectionCt = 0
		k.comment(f'border side 1')
		interlockRows = rows
		interlockEndN = needles[side1][1]
		prevInterlockStartN = needles[side1][0]
		checkAgain = False #new
		if len(tuckOver[0]):
			tuckOverNs = tuckOver[0].copy()
			tuckOverNs2 = tuckOver[1].copy() #new #*#*#*
			if dir2 == '-': tuckOverNs.reverse() #if starting on right side for border
			
			for t in range(0, len(tuckOverNs)):
				tList = tuckOverNs[t].copy()
				tList2 = tuckOverNs2[t].copy() #new #check #*#*#*
				if dir2 == '-': tList.reverse()
				else: tList2.reverse() #new #*#*#*
				tuckStartN = int(tList[0][1:])
				tuckEndN = int(tList[-1][1:])

				if dir2 == '+': #if starting on left side for border
					tuckStartN -= 1
					tuckEndN += 1
				else:
					tuckStartN += 1
					tuckEndN -= 1

				# if (dir2 == '+' and tuckStartN >= needles[side2][0]) or (dir2 == '-' and tuckStartN <= needles[side2][0]): break #check #go back! #?!?#?!#? #*#*#*#*#*#* #here #*#*#*#*#*#*
				
				interlockStartN = tuckStartN

				# interlockStartN, interlockEndN #go back! #?
				lastOpBorderC = k.returnLastOp(carrier=c, asDict=True) #new #v
				lastBorderN = lastOpBorderC['bn1']['needle']
				if firstTime: distFromStart = abs(lastBorderN-interlockEndN)
				else: distFromStart = abs(lastBorderN-interlockStartN)

				if distFromStart >= abs(interlockStartN-interlockEndN):
					k.comment(f'get carrier in correct spot')
					interlock(k, lastBorderN, tuckEndN, 0.5, c, gauge, startCondition=(2 if interlockStart[side2] == 1 else 1), emptyNeedles=offLimits) #check #new
					for bn in tList2:
						if bn not in offLimits: k.tuck(dir1, bn, c)

				if (dir2 == '+' and tuckStartN >= needles[side2][0]) or (dir2 == '-' and tuckStartN <= needles[side2][0]):
					if t == 0: checkAgain = True #new check
					break #check #go back! #?!?#?!#? #*#*#*#*#*#* #here #*#*#*#*#*#*

				if firstTime:
					if dir2 == '+': castonRange = range(interlockEndN, interlockStartN) #if starting on left side
					else: castonRange = reversed(range(interlockStartN, interlockEndN)) #check

					castonFirstTime(castonRange)

				interlock(k, interlockStartN, interlockEndN, interlockRows, c, gauge, startCondition=interlockStart[side1], emptyNeedles=offLimits)

				for bn in tList:
					if bn not in offLimits: k.tuck(dir2, bn, c)
	
				interlockEndN = tuckEndN
				sectionCt += 1
				prevInterlockStartN = interlockStartN
		
		interlockStartN = needles[side1][0]

		if checkAgain: #new #v
			lastOpBorderC = k.returnLastOp(carrier=c, asDict=True)
			lastBorderN = lastOpBorderC['bn1']['needle']
			if firstTime: distFromStart = abs(lastBorderN-interlockEndN)
			else: distFromStart = abs(lastBorderN-interlockStartN)
			
			if distFromStart >= abs(interlockStartN-interlockEndN):
				k.comment(f'get carrier in correct spot !')
				interlock(k, lastBorderN, (list(tuckRange)[-1]-1 if dir1 == '+' else list(tuckRange)[-1]+1), 0.5, c, gauge, startCondition=(2 if interlockStart[side2] == 1 else 1), emptyNeedles=offLimits) #check #new
			
				tuckCt = {'f': 0, 'b': 0}
				tuckInterval = 3
				for n in reversed(tuckRange): #TODO: maybe just make sure it is secure on edges
					if f'f{n}' not in offLimits and ((gauge == 1 and f'f{n}' in emptyNeedles) or (gauge != 1 and n % gauge != 0)):
						if (tuckCt['f']) % tuckInterval == 0:
							# toDrop.append(f'f{n}')
							k.tuck(dir1, f'f{n}', c)
						tuckCt['f'] += 1
					elif f'b{n}' not in offLimits and ((gauge == 1 and f'b{n}' in emptyNeedles) or (gauge != 1 and n % gauge == 0)):
						if (tuckCt['b']) % tuckInterval == 0:
							# toDrop.append(f'b{n}')
							k.tuck(dir1, f'b{n}', c)
						tuckCt['b'] += 1  #new #^

		if firstTime:
			if dir2 == '+': castonRange = range(interlockEndN, interlockStartN) #if starting on left side
			else: castonRange = reversed(range(interlockStartN, interlockEndN)) #check

			castonFirstTime(castonRange)
			k.rack(0)
		elif sectionCt > 0: interlock(k, interlockEndN, interlockStartN, 0.5, c, gauge, startCondition=(2 if interlockStart[side2] == 1 else 1), emptyNeedles=offLimits) #check

		interlock(k, interlockStartN, interlockEndN, interlockRows, c, gauge, startCondition=interlockStart[side1], emptyNeedles=offLimits) #new #check

	toDrop = []
	tuckCt = {'f': 0, 'b': 0}

	tuckInterval = 3
	# tuckInterval = 2
	tuckRangeList = list(tuckRange)

	tuckStartN = tuckRangeList[0]
	tuckEndN = tuckRangeList[len(tuckRangeList)-1]

	if len(tuckNs): #new #v
		for bn in reversed(tuckNs):
			if bn not in offLimits:
				k.tuck(dir2, bn, c)
				toDrop.append(bn)
	else: #new #^
		for n in tuckRange:
			if n == tuckStartN: #ensure tuck makes a diagonal
				if (endBeds[side1] == 'f' and tuckStartN % gauge != 0) or (endBeds[side1] == 'b' and tuckStartN % gauge == 0):
					continue

			# if shift == 0 and n == tuckRangeList[len(tuckRangeList)-2]: #second to last needle
			if not len(tuckNs) and n == tuckRangeList[len(tuckRangeList)-2]: #second to last needle
				if startBeds[side2] == 'b':
					if n % gauge != 0: lastTuckN = f'f{n}'
					else: lastTuckN = f'f{tuckEndN}'
				else:
					if n % gauge == 0: lastTuckN = f'b{n}'
					else: lastTuckN = f'b{tuckEndN}'
				
				toDrop.append(lastTuckN)
				k.tuck(dir2, lastTuckN, c)
				break

			if f'f{n}' not in offLimits and ((gauge == 1 and f'f{n}' in emptyNeedles) or (gauge != 1 and n % gauge != 0)):
				if (tuckCt['f']) % tuckInterval == 0:
					toDrop.append(f'f{n}')
					if not len(tuckNs): #new #v
						if dir2 == '+': nextTuck.append(f'f{n+gauge}')
						else: nextTuck.append(f'f{n-gauge}') #new #^
					k.tuck(dir2, f'f{n}', c)
				# if f'f{n}' not in offLimits: tuckCt['f'] += 1
				tuckCt['f'] += 1
			elif f'b{n}' not in offLimits and ((gauge == 1 and f'b{n}' in emptyNeedles) or (gauge != 1 and n % gauge == 0)):
				if (tuckCt['b']) % tuckInterval == 0:
					toDrop.append(f'b{n}')
					k.tuck(dir2, f'b{n}', c)
					if not len(tuckNs): #new #v
						if dir2 == '+': nextTuck.append(f'b{n+gauge}')
						else: nextTuck.append(f'b{n-gauge}') #new #^
				# if f'b{n}' not in offLimits: tuckCt['b'] += 1
				tuckCt['b'] += 1

	# if justTuck: return toDrop
	if justTuck: return sortBedNeedles(toDrop) #new

	if firstTime:
		if dir2 == '+':
			castonBed1 = 'f'
			castonBed2 = 'b'
			condition1 = lambda n: n % gauge == 0
			condition2 = lambda n: (n % gauge != 0 or gauge == 1)
		else:
			castonBed1 = 'b'
			castonBed2 = 'f'
			condition1 = lambda n: (n % gauge != 0 or gauge == 1)
			condition2 = lambda n: n % gauge == 0
	
	interlockRows = rows
	interlockStartN = needles[side2][0]

	borderSections = []

	if len(tuckOver[0]):
		k.comment(f'border side 2') #remove #debug
		tuckOverNs = tuckOver[0].copy()
		tuckOverNs2 = tuckOver[1].copy() #new #*#*#*
		if dir2 == '-': tuckOverNs.reverse() #if starting on right side for border
		else: tuckOverNs2.reverse() #new

		for t in range(0, len(tuckOverNs)):
			tList = tuckOverNs[t].copy()
			tList2 = tuckOverNs2[t].copy()

			if dir2 == '-': tList.reverse()
			else: tList2.reverse() #new #*#*#*
			tuckStartN = int(tList[0][1:])
			tuckEndN = int(tList[-1][1:])

			if dir2 == '+': #if starting on left side for border
				tuckStartN -= 1 #-1
				tuckEndN += 1 #+1
			else:
				tuckStartN += 1 #+1
				tuckEndN -= 1 #-1

			if (dir2 == '+' and tuckStartN <= needles[side1][0]) or (dir2 == '-' and tuckStartN >= needles[side1][0]): continue
			
			interlockEndN = tuckStartN

			borderSections.append({'startN': interlockEndN, 'endN': interlockStartN, 'tList': tList2}) #switched bc will have already done one pass

			if firstTime:
				if dir2 == '+': castonRange = range(interlockStartN, interlockEndN) #if starting on left side
				else: castonRange = reversed(range(interlockEndN, interlockStartN))
				# if dir2 == '+': castonRange = range(interlockEndN, interlockStartN) #if starting on left side
				# else: castonRange = reversed(range(interlockStartN, interlockEndN))
				castonFirstTime(castonRange)
			else: interlock(k, interlockStartN, interlockEndN, length=0.5, c=c, gauge=gauge, startCondition=interlockStart[side2], emptyNeedles=offLimits)

			#tuck to get to next interlock section
			for bn in tList:
				if bn not in offLimits: k.tuck(dir2, bn, c)

			interlockStartN = tuckEndN

	interlockEndN = needles[side2][1]
	if firstTime:
		if dir2 == '+': castonRange = range(interlockStartN, interlockEndN) #if starting on left side
		else: castonRange = reversed(range(interlockEndN, interlockStartN))

		castonFirstTime(castonRange)

		interlock(k, interlockEndN, interlockStartN, 0.5, c, gauge, startCondition=(2 if interlockStart[side2] == 1 else 1), emptyNeedles=offLimits) #interlock, just to get it on correct side

	interlock(k, interlockStartN, interlockEndN, rows, c, gauge, startCondition=interlockStart[side2], emptyNeedles=offLimits) #new #check

	for bSec in borderSections:
		for bn in bSec['tList']:
			if bn not in offLimits: k.tuck(dir1, bn, c)
			
		interlock(k, bSec['startN'], bSec['endN'], length=rows-0.5, c=c, gauge=gauge, startCondition=(2 if interlockStart[side2] == 1 else 1), emptyNeedles=offLimits)


	if dir2 == '+':
		if missN is None: missN = endN+2
		k.miss(dir2, f'f{missN}', c) #get carrier out of way from main knitting
	else:
		if missN is None: missN = endN-2
		k.miss(dir2, f'f{missN}', c)

	if lastTime: #TODO: make sure not to drop if about to increase on
		for n in ranges1[side1]:
			if n % gauge == 0 and f'f{n}' not in offLimits: toDrop.append(f'f{n}')
		for n in ranges2[side1]:
			if (n % gauge != 0 or gauge == 1) and f'b{n}' not in offLimits: toDrop.append(f'b{n}')
		for n in ranges1[side2]:
			if n % gauge == 0  and f'f{n}' not in offLimits: toDrop.append(f'f{n}')
		for n in ranges2[side2]:
			if (n % gauge != 0 or gauge == 1) and f'b{n}' not in offLimits: toDrop.append(f'b{n}')

	k.rollerAdvance(rollerAdvance)

	return sortBedNeedles(toDrop), nextTuck #so know to drop those tucks after
	# return toDrop, nextTuck #so know to drop those tucks after
	# return toDrop #so know to drop those tucks after


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
def wasteSection(k, leftN, rightN, closedCaston=True, wasteC='1', drawC='2', otherCs = [], gauge=1, endOnRight=[], firstNeedles={}, catchMaxNeedles=False, initial=True, drawMiddle=False, interlockLength=36):
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
				carrierLocations[wasteC] = firstNeedles[wasteC][1] #*
			else:
				missWaste = firstNeedles[wasteC][0]
				carrierLocations[wasteC] = firstNeedles[wasteC][0] #*
		
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

	if len(carriers) != len(carrierLocations):
		for c in carriers:
			if c not in carrierLocations:
				if c in endOnRight: carrierLocations[c] = rightN
				else: carrierLocations[c] = leftN


	if initial:
		catchEndOnRight = endOnRight.copy()

		# if closedCaston:
		if closedCaston and not drawMiddle: #new
			if drawC in endOnRight:
				catchEndOnRight.remove(drawC)
				if drawC in missOtherCs: missOtherCs[drawC] = firstNeedles[drawC][0] 
			else:
				catchEndOnRight.append(drawC)
				if drawC in missOtherCs: missOtherCs[drawC] = firstNeedles[drawC][1] 

		catchYarns(k, leftN, rightN, carriers, gauge, catchEndOnRight, missOtherCs, catchMaxNeedles)

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
	
	def drawThread():
		k.comment('draw thread')

		if drawC in endOnRight:
			if (not closedCaston) or drawMiddle: negDraw('b', False)
			posDraw()
		else:
			if (not closedCaston) or drawMiddle: posDraw('b', False)
			negDraw()

	k.comment('waste section')
	k.speedNumber(wasteSpeedNumber)

	if drawMiddle: interlockLength //= 2 #check

	if wasteC in endOnRight: #TODO: add extra pass if wasteC == drawC and closedCaston == True
		interlock(k, rightN, leftN, interlockLength, wasteC, gauge)
		if drawMiddle:
			drawThread()
			interlock(k, rightN, leftN, interlockLength, wasteC, gauge)
		else: circular(k, rightN, leftN, 8, wasteC, gauge)
		if missWaste is not None: k.miss('+', f'f{missWaste}', wasteC)
	else:
		interlock(k, leftN, rightN, interlockLength, wasteC, gauge)
		if drawMiddle:
			drawThread()
			interlock(k, leftN, rightN, interlockLength, wasteC, gauge)
		else: circular(k, leftN, rightN, 8, wasteC, gauge)
		if missWaste is not None: k.miss('-', f'f{missWaste}', wasteC)

	if closedCaston and not drawMiddle: #new
		for n in range(leftN, rightN+1):
			if (n + 1) % gauge == 0: k.drop(f'b{n}')

	if not drawMiddle: drawThread()

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

	k.comment(';tail')
	if shortrowing: k.rollerAdvance(100)
	else: k.rollerAdvance(200)

	k.miss(dir, f'{bed}{miss1}', c)

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
	if not asDecMethod: k.comment('bindoff')

	def posLoop(op=None, bed=None):
		for x in range(xferNeedle, xferNeedle+count):
			if op == 'knit' and f'{bed}{x}' not in emptyNeedles: k.knit('+', f'{bed}{x}', c)
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

	def negLoop(op=None, bed=None):
		for x in range(xferNeedle+count-1, xferNeedle-1, -1):
			if op == 'knit' and f'{bed}{x}' not in emptyNeedles: k.knit('-', f'{bed}{x}', c)
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

	#-------------
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


def halfGaugeOpenBindoff(k, count, xferNeedle, c, side='l'):
	'''
	*k is knitout Writer
	*count is the number of #TODO
	*xferNeedle is the first (edge-most) needle involved in the bindoff
	*c is the carrier being used for the binding off
	*side is the side on which the bind off starts; valid values are 'l' (left) and 'r' (right)
	'''
	k.comment('open-tube bindoff')

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
		bindRange1 = range(xferNeedle, xferNeedle+count, 2)
		if (bed2 == 'b' and otherEdgeN % 2 != 0) or (bed2 == 'f' and otherEdgeN % 2 == 0):
			smallRack = 1
			bindRange2 = range(otherEdgeN, xferNeedle, -2)
		else:
			smallRack -1
			bindRange2 = range(otherEdgeN-1, xferNeedle, -2)
	else:
		adjust = -2
		if bed1 == 'f': rack = -2
		else: rack = 2
		dir1 = '-'
		dir2 = '+'
		otherEdgeN = xferNeedle-count+1
		bindRange1 = range(xferNeedle, xferNeedle-count, -2)
		if (bed2 == 'b' and otherEdgeN % 2 != 0) or (bed2 == 'f' and otherEdgeN % 2 == 0):
			bindRange2 = range(otherEdgeN, xferNeedle, 2)
		else:
			bindRange2 = range(otherEdgeN+1, xferNeedle, 2)

	for n in bindRange1:
		k.xfer(f'{bed1}{n}', f'{bed2}{n}')
		if abs(n-otherEdgeN) != 1: #skip if 1 in from otherEdgeN (note: only applicable if count % 2 == 0, since xferNeedle & otherEdgeN would have different parity)
			k.rack(rack)
			k.xfer(f'{bed2}{n}', f'{bed1}{n+adjust}')
			k.rack(0)
			k.knit(dir1, f'{bed1}{n+adjust}', c)

	k.rack(rack//2)
	if count % 2 != 0: #note: if count % 2 != 0, xferNeedle & otherEdgeN have same parity
		k.xfer(f'{bed1}{otherEdgeN}', f'{bed2}{otherEdgeN-(adjust//2)}')
		k.rack(0)
		k.knit(dir2, f'{bed2}{otherEdgeN-(adjust//2)}', c)
	else:
		k.xfer(f'{bed2}{otherEdgeN-(adjust//2)}', f'{bed1}{otherEdgeN}')
		k.rack(0)
		k.xfer(f'{bed1}{otherEdgeN}', f'{bed2}{otherEdgeN}')
		k.knit(dir2, f'{bed2}{otherEdgeN}', c)

	for n in bindRange2:
		k.xfer(f'{bed2}{n}', f'{bed1}{n}')
		k.rack(rack)
		k.xfer(f'{bed1}{n}', f'{bed2}{n-adjust}') #+rack
		k.rack(0)
		k.knit(dir2, f'{bed2}{n-adjust}', c)

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
	'''

	k.comment('drop finish')

	outCarriers = carriers.copy()

	if len(carriers):
		if borderC is not None and borderC in carriers: outCarriers.remove(borderC) # remove so can take it out at end instead 
		for c in outCarriers: k.outcarrier(c)

	def knitBorder(posNeedleRange, posBed, negNeedleRange, negBed):
		beg = 0
		length = 16 #16 rows of waste #TODO: maybe make this a parameter?
		# length = 8 #8 rows of waste #TODO: maybe make this a parameter?

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
		
		if borderStPat is not None and len(frontNeedleRanges) and len(backNeedleRanges): #TODO: have option for single bed stitch pattern #new #check
			stitchPatternTube(k, leftN=posNeedleRange[0], rightN=posNeedleRange[1], c=borderC, wasteC=None, side=side, patterns=[borderStPat], defaultLength=16, wasteDivider=False)
			# def stitchPatternTube(k, leftN, rightN, c, wasteC='1', drawC='2', featureCs=[], side='l', patterns=[], defaultLength=None, wasteDivider=False)
			# stitchPatFunc = globals()[patName]
		else:
			for r in range(beg, length):
				if r % 2 == 0: knitBorderPos(posNeedleRange, posBed)
				else: knitBorderNeg(negNeedleRange, negBed)

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

	def dropOnBed(needleRanges, bed):
		if type(needleRanges[0]) == int: #just one range (one section)
			if rollOut and (needleRanges is backNeedleRanges or not len(backNeedleRanges)): k.addRollerAdvance(2000) #TODO: determine what max roller advance is
			for n in range(needleRanges[0], needleRanges[1]+1):
				if f'{bed}{n}' not in emptyNeedles: k.drop(f'{bed}{n}')
		else: #multiple ranges (multiple sections, likely shortrowing)
			for nr in needleRanges:
				if rollOut and needleRanges.index(nr) == len(needleRanges)-1 and (needleRanges is backNeedleRanges or not len(backNeedleRanges)): k.addRollerAdvance(2000) #TODO: determine what max roller advance is
				for n in range(nr[0], nr[1]+1):
					if f'{bed}{n}' not in emptyNeedles: k.drop(f'{bed}{n}')

	if len(frontNeedleRanges): dropOnBed(frontNeedleRanges, 'f')
	if len(backNeedleRanges): dropOnBed(backNeedleRanges, 'b')

	# if len(carriers):
	# 	for c in carriers: k.outcarrier(c)
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


def shapeXferDoubleBedHalfGauge(k, xferType, count, edgeNeedle, side='l'): #NOTE: changed 'type' to 'xferType'
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
	else: print('TODO')
	

def decDoubleBed(k, count, decNeedle, c=None, side='l', gauge=1, emptyNeedles=[]):
	'''
	*k in knitout Writer
	*count is number of needles to dec
	*decNeedle is edge-most needle being decreased (so reference point for increasing)
	*c is carrier (optional, but necessary if dec > 2, so worth including anyway)
	*side is side to dec on
	*emptyNeedles is an optional list of needles that are not currently holding loops (e.g. if using stitch pattern), so don't waste time xferring them

	returns new edge-needle on given side based on decrease count, so should be called as so (e.g.):
	leftneedle = decDoubleBed(...)
	'''
	stackedLoopNeedles = []
	twistedStitches = []

	decMethod = 'xfer'
	# if count > 2: decMethod = 'bindoff' #remove #?
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
		# count *= gauge #remove #?
		newEdgeNeedle += count
		k.comment(f'dec {count} on left ({decNeedle} -> {newEdgeNeedle})')
	else:
		# count *= gauge #remove #?
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
				# stackedLoopNeedles, twistedStitches = shapeXferDoubleBedHalfGauge(k, 'dec', (count//gauge), decNeedle, side) #remove #?
				stackedLoopNeedles, twistedStitches = shapeXferDoubleBedHalfGauge(k, 'dec', count, decNeedle, side)
			else: print('\n#TODO') #add for other gauges
	else: #dec by more than 2 (or more than 4 if half gauge), bindoff method
		bindNeedle = decNeedle

		bindoff(k, count, bindNeedle, c, side, True, True, emptyNeedles)

	resetSettings(k)
	return newEdgeNeedle, stackedLoopNeedles, twistedStitches #new


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

	returns 1) new edge-needle on given side based on inc count and 2) list of now-empty needles to perform twisted stitches on, so should be called as so (e.g.):
	leftneedle, twistedStitches = incDoubleBed(...)
	'''
	# if count > 2 and count < 5 and gauge == 2 and incMethod == 'split': incMethod = 'xfer' #new #TODO: test doesnt work :(
	# elif count > 2: incMethod = 'zig-zag'
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
		# count *= gauge #remove #?
		# newEdgeNeedle -= count
		if incMethod == 'split' and splitType == 'gradual':
			newEdgeNeedle -= 1
			k.comment(f'inc 1 on left ({edgeNeedle} -> {newEdgeNeedle}) by gradual split')
		else:
			newEdgeNeedle -= count
			k.comment(f'inc {count} on left ({edgeNeedle} -> {newEdgeNeedle}) by {incMethod}')
	else: #right side
		# count *= gauge #remove #?
		# newEdgeNeedle += count
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
			# if gauge == 2: shapeXferDoubleBedHalfGauge(k, 'inc', (count//gauge), edgeNeedle, side) #remove #?
			if gauge == 2:
				twistedStitches = shapeXferDoubleBedHalfGauge(k, 'inc', count, edgeNeedle, side)
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
					# if splitType == 'gradual': newEdgeNeedle += 1 #change, since only splitting one right now
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
					# if splitType == 'gradual': #gradual split
					# if splitType == 'gradual': newEdgeNeedle -= 1 #change, since only splitting one right now
					if edgeNeedleB > edgeNeedleF: #meaning edgeNeedle % 2 != 0 (aka it's on back bed)
						k.deleteLastOp(kwd_s=f'knit + b{edgeNeedleB}', breakCondition=lambda op: 'knit - ' in op)
						k.rack(1)
						k.split('+', f'b{edgeNeedleB}', f'f{edgeNeedleF+2}', c)
					else: #meaning edgeNeedle % 2 == 0 (aka it's on front bed)
						k.deleteLastOp(kwd_s=f'knit + f{edgeNeedleF}', breakCondition=lambda op: 'knit - ' in op)
						k.rack(-1)
						k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleB+2}', c)
					k.rack(0)
			# if (count//gauge) == 1: #remove #?
			elif count == 2:
				if side == 'l': #left side #remove #? #v
					# if splitType == 'gradual': #gradual split (one at a time): #gradual
					# 	newEdgeNeedle += 1 #change, since only splitting one right now
					# 	if edgeNeedleF < edgeNeedleB: #leftN == edgeN
					# 		k.deleteLastOp(kwd_s=f'knit - f{edgeNeedleF}', breakCondition=lambda op: 'knit + ' in op)
					# 		k.rack(1)
					# 		k.split('-', f'f{edgeNeedleF}', f'b{edgeNeedleB-2}', c)
					# 	else:
					# 		k.deleteLastOp(kwd_s=f'knit - b{edgeNeedleB}', breakCondition=lambda op: 'knit + ' in op)
					# 		k.rack(-1)
					# 		k.split('-', f'b{edgeNeedleB}', f'f{edgeNeedleF-2}', c)
					# 	k.rack(0)
					# elif splitType == 'xfer': #original split style (includes xfers) #remove #? #^
					if splitType == 'xfer': #original split style (includes xfers)
						k.deleteLastOp(kwd_s=f'knit - f{edgeNeedleF}', breakCondition=lambda op: 'knit + ' in op)
						k.deleteLastOp(kwd_s=f'knit - b{edgeNeedleB}', breakCondition=lambda op: 'knit + ' in op)
						if edgeNeedleF > edgeNeedleB: k.split('-', f'f{edgeNeedleF}', f'b{edgeNeedleF}', c)
						k.split('-', f'b{edgeNeedleB}', f'f{edgeNeedleB}', c)
						if edgeNeedleF < edgeNeedleB: k.split('-', f'f{edgeNeedleF}', f'b{edgeNeedleF}', c)

						k.rack(-gauge)
						if edgeNeedleF > edgeNeedleB: #?
							k.tuck('-', f'f{edgeNeedleF-1}', c)
							k.tuck('-', f'b{edgeNeedleF-2-gauge}', c)

						k.xfer(f'b{edgeNeedleF}', f'f{edgeNeedleF-gauge}')
						if edgeNeedleF > edgeNeedleB: #?
							k.drop(f'b{edgeNeedleF-2-gauge}')
							k.drop(f'f{edgeNeedleF-1}')

						k.rack(gauge)
						if edgeNeedleF < edgeNeedleB: #?
							k.tuck('-', f'b{edgeNeedleB-1}', c)
							k.tuck('-', f'f{edgeNeedleB-2-gauge}', c)

						k.xfer(f'f{edgeNeedleB}', f'b{edgeNeedleB-gauge}')

						if edgeNeedleF < edgeNeedleB: #?
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
					# if splitType == 'gradual': #gradual split #remove #? #v
					# 	newEdgeNeedle -= 1 #change, since only splitting one right now
					# 	if edgeNeedleB > edgeNeedleF: #meaning edgeNeedle % 2 != 0 (aka it's on back bed)
					# 		k.deleteLastOp(kwd_s=f'knit + b{edgeNeedleB}', breakCondition=lambda op: 'knit - ' in op)
					# 		k.rack(1)
					# 		k.split('+', f'b{edgeNeedleB}', f'f{edgeNeedleF+2}', c)
					# 	else: #meaning edgeNeedle % 2 == 0 (aka it's on front bed)
					# 		k.deleteLastOp(kwd_s=f'knit + f{edgeNeedleF}', breakCondition=lambda op: 'knit - ' in op)
					# 		k.rack(-1)
					# 		k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleB+2}', c)
					# 	k.rack(0)
					# elif splitType == 'xfer': #remove #? #^
					if splitType == 'xfer':
						k.deleteLastOp(kwd_s=f'knit + f{edgeNeedleF}', breakCondition=lambda op: 'knit - ' in op)
						k.deleteLastOp(kwd_s=f'knit + b{edgeNeedleB}', breakCondition=lambda op: 'knit - ' in op)
						if edgeNeedleF < edgeNeedleB: k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleF}', c)
						k.split('+', f'b{edgeNeedleB}', f'f{edgeNeedleB}', c)
						if edgeNeedleF > edgeNeedleB: k.split('+', f'f{edgeNeedleF}', f'b{edgeNeedleF}', c)

						k.rack(-gauge)
						if edgeNeedleF < edgeNeedleB: #?
							k.tuck('+', f'f{edgeNeedleB+1}', c)
							k.tuck('+', f'b{edgeNeedleB+2+gauge}', c)
						
						k.xfer(f'f{edgeNeedleB}', f'b{edgeNeedleB+gauge}')

						if edgeNeedleF < edgeNeedleB:
							k.drop(f'b{edgeNeedleB+2+gauge}')
							k.drop(f'f{edgeNeedleB+1}')
						
						k.rack(gauge)
						if edgeNeedleF > edgeNeedleB:
							k.tuck('+', f'b{edgeNeedleF+1}', c) #?
							k.tuck('+', f'f{edgeNeedleF+2+gauge}', c) #?

						k.xfer(f'b{edgeNeedleF}', f'f{edgeNeedleF+gauge}')

						if edgeNeedleF > edgeNeedleB:
							k.drop(f'f{edgeNeedleF+2+gauge}') #?
							k.drop(f'b{edgeNeedleF+1}') #?
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
			# elif (count//gauge == 2):
			elif (count > 2):
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

	# if gauge == 1 or bed == 'f': condition = lambda n: n % gauge == 0
	# else: condition = lambda n: n % gauge != 0
	
	lastN = endN

	if endN > startN: #first pass is pos
		dir1 = '+'
		dir2 = '-'
		# leftN = startN
		# rightN = endN
		par = -1
		# shift = -sectionWidth
		# width = (endN-startN)+1

		# lastN = endN - sectionWidth

		needleRange1 = range(startN, endN+1)
		needleRange2 = range(endN, startN-1, -1)
		# beg = 0
	else: #first pass is neg
		dir1 = '-'
		dir2 = '+'
		# leftN = endN
		# rightN = startN
		par = 1
		# shift = sectionWidth
		# width = (startN-endN)+1

		# lastN = endN + sectionWidth 

		needleRange1 = range(startN, endN-1, -1)
		needleRange2 = range(endN, startN+1)
		# beg = 1
		# length += 1

	def enoughNeedles(p, lastN): #neg: 1 or 9 #pos: 10 or 2
		# if p % 2 != 0 and lastN == startN-(par*((width-1)%sectionWidth)): return True #meaning knitting the last leftover needles before starting a new cycle #go back! #?



		# if lastN == (startN-(startN-endN)%sectionWidth): return True #meaning knitting the last leftover needles before starting a new cycle
		
		if dir1 == '+':
			if lastN >= startN and (lastN-startN)+1 >= sectionWidth: return True
			# if lastN >= endN and startN-lastN > sectionWidth: return True #for odd
			else: return False
		else:
			if lastN >= endN and (startN-lastN)+1 >= sectionWidth: return True #for odd
			else: return False

		
		# if lastN >= leftN and (lastN-leftN)+1 >= sectionWidth
		# 	# if lastN >= endN and startN-lastN > sectionWidth: return True #for odd
		# else: return False

		# if dir1 == '+':

		# else:
		# 	if lastN >= endN and (startN-lastN)+1 >= sectionWidth: return True #for odd
		# 	# if lastN >= endN and startN-lastN > sectionWidth: return True #for odd
		# 	else: return False

		# if (p % 2 == 0 and dir1 == '+') or (p % 2 != 0 and dir1 == '-'):
		# 	# if lastN-startN > sectionWidth: return True
		# 	if lastN-endN > sectionWidth: return True
		# 	else: return False
		# else:
		# 	if startN-lastN > sectionWidth: return True
		# 	else: return False

	for p in range(0, length):
		# lastN = endN
		k.comment(f'new spiral cycle')
		# while(abs(startN-lastN) > sectionWidth):
		# if p % 2 == 0: lastN += (par*sectionWidth)
		# else: lastN -= (par*sectionWidth)
		# if p % 2 == 0: lastN += (par*sectionWidth)
		# else: lastN = endN
		lastN = endN
		while(enoughNeedles(p, lastN)):
			# if p % 2 == 0: lastN += shift
			# else: lastN -= shift
			# if p % 2 == 0: lastN += (par*sectionWidth)
			# else: lastN -= (par*sectionWidth)
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
			# if p % 2 == 0: lastN += (par*sectionWidth)
			# else: lastN -= (par*sectionWidth)


#------------------------------------------------------------------------
#--- IMAGE PROCESSING / KNITTING WITH KNITOUT FOR CACTUS-ESQUE THINGS ---
#------------------------------------------------------------------------

plaitInfo = {'count': 0, 'assigned': 0, 'f': [], 'b': [], 'lastRows': {}, 'carriers': [], 'carrierPark': {}} #new #global

# def insertStitchPattern(k, stitchPat, needles, bed, side='l', c='1', info={}, **additionalArgs): #TODO: implement the thing where we add multiple needles when calling this function to indicate multiple passes
# def insertStitchPattern(k, stitchPat, needles, passEdgeNs, bed, side='l', c='1', **additionalArgs): #TODO: implement the thing where we add multiple needles when calling this function to indicate multiple passes
def insertStitchPattern(k, stitchPat, needles, passEdgeNs, bed, side='l', c='1'): #TODO: implement the thing where we add multiple needles when calling this function to indicate multiple passes
	patName = stitchPat.pattern
	if patName == 'interlock': patLength = 0.5
	else: patLength = 1

	# patFuncReturns = {'garter': ['side'], 'rib': [None]}
	patFuncReturns = {'garter': ['side']}

	stitchPatFunc = globals()[patName]

	def get_parameters(func):
		keys = func.__code__.co_varnames[:func.__code__.co_argcount][::-1]
		sorter = {j: i for i, j in enumerate(keys[::-1])} 
		
		params = sorted([i for i in keys], key=sorter.get)
		return params
		# values = func.__defaults__[::-1]
		# kwargs = {i: j for i, j in zip(keys, values)}
		
		# sorted_args = tuple(sorted([i for i in keys if i not in kwargs], key=sorter.get))
		# sorted_kwargs = {i: kwargs[i] for i in sorted(kwargs.keys(), key=sorter.get)}   
		# return sorted_args, sorted_kwargs
	
	# if patName == 'rib': print('\nrib', stitchPat.info['count'], stitchPat.args['secureStartN']) #remove #debug
	if stitchPat.info['count'] == 0 and patName == 'rib' and stitchPat.args['secureStartN'] == True:
		seq = stitchPat.args['sequence']
		# print('\n!', seq) #remove #debug
		if type(needles[0]) == list: stNeedles = needles[0].copy()
		else: stNeedles = needles.copy()

		if side == 'l':
			stStartN = stNeedles[0]
			# if (bed == 'f' and stStartN % 2 != 0) or (bed == b and stStartN % 2 == 0): stStartN += 1 #removed this since gauging the sequence will make f => ff
		else:
			stStartN = stNeedles[-1]
			# if (bed == 'f' and stStartN % 2 != 0) or (bed == b and stStartN % 2 == 0): stStartN -= 1

		switchBeds = str.maketrans('fb', 'bf')
		if seq[stStartN % len(seq)] == bed: stitchPat.args['sequence'] = seq.translate(switchBeds) #new #check
		# if seq[stStartN % len(seq)] != bed: stitchPat.args['sequence'] = seq.translate(switchBeds) #new #check
		# print(stitchPat.args['sequence']) #remove #debug
		# if (startN % 2 == 0 and originBed == 'f') or ((startN+1) % 2 == 0 and originBed == 'b'):
		# 	secureNeedles[startN] = originBed
		# 	secureNeedles[otherStartN] = otherBed
		# 	if sequence[startN % len(sequence)] == otherBed: secureSequence = sequence.translate(switchBeds)

	# print(get_parameters(stitchPatFunc)) #remove #debug

	# stitchPatFunc = globals()[f'{stitchPat}Pattern']
	def postFuncUpdate(returns, updates):
		if returns == None and not len(updates): stitchPat.update(returns)
		# if returns == None: stitchPat.update(returns)
		else:
			if returns is None:stitchPat.update(updates) #new #check
			elif type(returns) == tuple: #multiple return values
				results = {}
				for val in returns:
					results[patFuncReturns[patName][returns.index(val)]] = val
				if len(updates): results.update(updates)
				# return results
				stitchPat.update(results)
				# stitchPat.completed(results)
			# else: stitchPat.completed({patFuncReturns[patName][0]: returns}) #one return value
			else:
				results = {patFuncReturns[patName][0]: returns}
				if len(updates): results.update(updates)
				stitchPat.update(results) #one return value
				# stitchPat.update({patFuncReturns[patName][0]: returns}) #one return value

	plaiting = False
	carrierCondition = 1
	if 'plaitC' in stitchPat.info and stitchPat.info['plaitC'] is not None: #new
		plaiting = True
		patC = [c, stitchPat.info['plaitC']]
		if (bed == 'f' and stitchPat.info['plaitCside'] == 'r') or (bed == 'b' and stitchPat.info['plaitCside'] == 'l'): carrierCondition = 2
		# if (bed == 'f' and stitchPat.info['plaitCside'] == 'l') or (bed == 'b' and stitchPat.info['plaitCside'] == 'r'): modC = 2
		# else: 
		# stitchPatDetailsB[idx].info['plaitCside']
	else: patC = c
		
	if type(needles[0]) == list: #meaning multiple rows
		length = len(needles)
		# startN = needles[0]
		# endN = needles[-1]

		def startAndEndNs(p): #TODO: check to make sure this actually works
			if p > 0:
				if 'secureStartN' in stitchPat.args:
					stitchPat.args['secureStartN'], stitchPat.args['secureEndN'] = stitchPat.args['secureEndN'], stitchPat.args['secureStartN']
					# stitchPat.update({'secureStartN': stitchPat.args['secureEndN'], 'secureEndN': stitchPat.args['secureStartN']}) #switch these around
			if (side == 'l' and p % 2 == 0) or (side == 'r' and p % 2 != 0): return needles[p][0], needles[p][-1]
			else: return needles[p][-1], needles[p][0]
		
		for p in range(0, length):
			if carrierCondition == 1:
				if p < length-1 or (length % 2 == 0): carrier = patC
				else: carrier = c
			else:
				if p > 0: carrier = patC
				else: carrier = c
				# if p > 0 and (p < length-1 or (length % 2 != 0)): carrier = patC
				# else: carrier = c
			postFuncInfo = {}
			startN, endN = startAndEndNs(p)

			if p == (length-1): #new#new #v
				if endN > startN: finalDirection = '+'
				else: finalDirection = '-' #^

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
						# if p > 0: stitchPat.args['currentBed'] = None
				elif stitchPat.args['homeBed'] is None:
					stitchPat.args['homeBed'] = bed #reset it back to the actual homeBed
					postFuncInfo = {'currentBed': bed}

			# if 'patternRows' in stitchPat.args and 'homeBed' in stitchPat.args:
			# 	if p < (length-1):
			# 		# if stitchPat.info['count'] % stitchPat.args['patternRows'] != 0: #if not going to reset
			# 		if stitchPat.info['count'] % stitchPat.args['patternRows'] != (stitchPat.args['patternRows']-1): #if not going to reset
			# 			stitchPat.args['homeBed'] = None #so won't xfer back
			# 		#come back! #here
			# 		elif stitchPat.args['homeBed'] == None:
			# 			stitchPat.args['homeBed'] = bed #reset it
			# 			postFuncInfo = {'currentBed': bed}
			# 	elif stitchPat.args['homeBed'] == None:
			# 		stitchPat.args['homeBed'] = bed #reset it back to the actual homeBed
			# 		postFuncInfo = {'currentBed': bed}


			# result = stitchPatFunc(k, startN=startN, endN=endN, length=patLength, c=c, **additionalArgs) #keep redefining until end #TODO: remove this comment if it works fine
			# result = stitchPatFunc(k, startN=startN, endN=endN, length=patLength, c=c, **stitchPat.args) #keep redefining until end
			result = stitchPatFunc(k, startN=startN, endN=endN, length=patLength, c=carrier, **stitchPat.args) #keep redefining until end #TODO: remove this comment if it works fine
			postFuncUpdate(result, postFuncInfo)
			# stitchPat.update() #new
			if p < length-1:
				k.rollerAdvance(0) #new
				if endN > startN:
					if endN != passEdgeNs[1]: #rightN, pos pass #here#*
						if (bed == 'f' and (endN+1) % 2 == 0) or (bed == 'b' and (endN+1) % 2 != 0): k.tuck('+', f'{bed}{endN+1}', c)
						elif endN+1 != passEdgeNs[1]: k.tuck('+', f'{bed}{endN+2}', c) #new
					else: #new #v
						if bed == 'f':
							otherBed = 'b'
							otherBedEndN = (endN-1 if (endN % 2 == 0) else endN)
						else:
							otherBed = 'f'
							otherBedEndN = (endN if (endN % 2 == 0) else endN-1)
						k.tuck('-', f'{otherBed}{otherBedEndN}', c)
						k.miss('+', f'{bed}{endN}', c) #new #^ #check
				elif endN < startN:
					if endN != passEdgeNs[0]: #leftN, posPas #here#*
						if (bed == 'f' and (endN-1) % 2 == 0) or (bed == 'b' and (endN-1) % 2 != 0): k.tuck('-', f'{bed}{endN-1}', c)
						elif endN-1 != passEdgeNs[0]: k.tuck('-', f'{bed}{endN-2}', c) #new
					else: #new #v
						if bed == 'f':
							otherBed = 'b'
							otherBedEndN = (endN+1 if (endN % 2 == 0) else endN)
						else:
							otherBed = 'f'
							otherBedEndN = (endN if (endN % 2 == 0) else endN+1)
						k.tuck('+', f'{otherBed}{otherBedEndN}', c) #new #^ #check
						k.miss('-', f'{bed}{endN}', c) #new #^ #check
				k.rollerAdvance(rollerAdvance) #new #check
			else:
			# 	if carrierCondition == 1:
			# 	if p < length-1 or (length % 2 == 0): carrier = patC
			# 	else: carrier = c
			# else:
			# 	if p > 0: carrier = patC
			# 	else: carrier = c
				if plaiting: #get it out of way in case of any future tucks that are meant to prevent holes
					# lastMissOp = k.deleteLastOp(kwd_s=['miss', f'{c} {stitchPat.info["plaitC"]}'], breakCondition=lambda op: ';begin ' in op, returnOp=True) #remove
					# if stitchPat.info['plaitCside'] == 'r' and (needles[p][-1] != passEdgeNs[1]): #TODO: maybe only miss if there's another pass coming directly up?
					if stitchPat.info['plaitCside'] == 'r' and (needles[p][-1] != passEdgeNs[1]) and finalDirection == '+': #TODO: maybe only miss if there's another pass coming directly up?
						k.comment(f'miss plaitC ({stitchPat.info["plaitC"]}) out of way before finishing row')
						k.rollerAdvance(0) #new
						k.miss('-', f'f{needles[p][-1]-3}', stitchPat.info['plaitC']) #new #-3 (used to be -1) #*#here#*
						plaitInfo['carrierPark'][stitchPat.info['plaitC']] = needles[p][-1]-3 #new #check #*#here#*
						lastMissOp = k.deleteLastOp(kwd_s=['miss', f'{c} {stitchPat.info["plaitC"]}'], breakCondition=lambda op: ';begin ' in op, returnOp=True)
						if lastMissOp:
							lastMissInfo = lastMissOp.split(' ')
							k.miss(lastMissInfo[1], lastMissInfo[2], c)
							# newMissOp = lastMissOp.replace(f'{c} {stitchPat.info["plaitC"]}', f'{c}')
						k.rollerAdvance(rollerAdvance) #new
					# elif stitchPat.info['plaitCside'] == 'l' and (needles[p][0] != passEdgeNs[0]):
					elif stitchPat.info['plaitCside'] == 'l' and (needles[p][0] != passEdgeNs[0]) and finalDirection == '-':
						k.comment(f'miss plaitC ({stitchPat.info["plaitC"]}) out of way before finishing row')
						k.rollerAdvance(0) #new
						k.miss('+', f'f{needles[p][0]+3}', stitchPat.info['plaitC']) #new #+3 (used to be +1) #*#here#*
						plaitInfo['carrierPark'][stitchPat.info['plaitC']] = needles[p][0]+3 #new #check #*#here#*
						lastMissOp = k.deleteLastOp(kwd_s=['miss', f'{c} {stitchPat.info["plaitC"]}'], breakCondition=lambda op: ';begin ' in op, returnOp=True)
						if lastMissOp:
							lastMissInfo = lastMissOp.split(' ')
							k.miss(lastMissInfo[1], lastMissInfo[2], c)
						k.rollerAdvance(rollerAdvance) #new
	else:
		if side == 'l':
			startN = needles[0]
			endN = needles[-1]
		else:
			startN = needles[-1]
			endN = needles[0]

		# if carrierCondition == 1: carrier = c
		# else: carrier = patC
		# if bed == 'b': k.comment(f'{"plaitC" in stitchPat.info}, {carrierCondition}, {stitchPat.info["plaitCside"]}') #remove #debug
		# result = stitchPatFunc(k, startN=startN, endN=endN, length=patLength, c=carrier, **stitchPat.args)
		result = stitchPatFunc(k, startN=startN, endN=endN, length=patLength, c=c, **stitchPat.args)
		# result = stitchPatFunc(k, startN=startN, endN=endN, length=patLength, c=c, **stitchPat.args) #go back! #?
		# if updateInfo: postFuncUpdate(result)
		postFuncUpdate(result, {})
		# stitchPat.update() #new
		# if type(result) == tuple: #multiple return values
		# 	results = {}
		# 	for val in result:
		# 		results[patFuncReturns[stitchPat][result.index(val)]] = val
		# 	# return results
		# 	stitchPat.update(results)
		# else: stitchPat.update({patFuncReturns[stitchPat][0]: result}) #one return value
		# # else: return {patFuncReturns[stitchPat][0]: result} #one return value

	# postFuncUpdate(result)

class StitchPatDetails:
	def __init__(self, pattern, args, info):
		self.pattern = pattern
		self.args = args
		self.info = info

	# def completed(self, returns):
	# 	for (key, val) in returns.items():
	# 		if key in self.info: self.info[key] = val
	# 		elif key in self.args: self.args[key] = val
	# 	self.info['count'] += 1 

def genericUpdate(self, returns):
	if returns is not None: #new
		for (key, val) in returns.items():
			if key in self.info: self.info[key] = val
			elif key in self.args: self.args[key] = val
	self.info['count'] += 1 #new location

def garterUpdate(self, returns): #TODO: add option of updating currentBed if self.args['homeBed'] == None #def garter(k, startN, endN, length, c, patternRows=1, startBed='f', borderC=None, gauge=1)
# def garterUpdate(self): #TODO: add option of updating currentBed if self.args['homeBed'] == None #def garter(k, startN, endN, length, c, patternRows=1, startBed='f', borderC=None, gauge=1)
	genericUpdate(self, returns)

	# self.info['count'] += 1
	if self.args['homeBed'] is None: self.args['currentBed'] = self.args['startBed'] #check and maybe #move #?

	if self.info['count'] % self.args['patternRows'] == 0:
		if self.args['startBed'] == 'f': self.args['startBed'] = 'b'
		else: self.args['startBed'] = 'f'
	
def interlockUpdate(self, returns): # def interlock(k, startN, endN, length, c, gauge=1, startCondition=1, emptyNeedles=[])
	genericUpdate(self, returns)

	if self.args['startCondition'] == 1: self.args['startCondition'] = 2 #new
	else: self.args['startCondition'] = 1

def ribUpdate(self, returns): #def rib(k, startN, endN, length, c, currentBed=None, originBed=None, homeBed=None, secureStartN=True, secureEndN=True, sequence='fb', gauge=1)
	genericUpdate(self, returns)

	if self.args['homeBed'] is None: self.args['currentBed'] = None #check
	# else: self.args['currentBed'] = self.args['homeBed']

	#TODO: see if anything else needs to be updated

def laceUpdate(self, returns): #def lace(k, startN, endN, length, c, patBeg=0, patternRows=2, spaceBtwHoles=1, offset=1, offsetReset=None, bed='f', gauge='1'): #TODO: ensure it works well for gauge 2
	genericUpdate(self, returns)

	self.args['offsetStart'] = self.args['patBeg'] #whatever the previous patBeg was #check
	self.args['patBeg'] = self.info['count'] % self.args['patternRows'] #new #TODO: #check

	# self.args['patBeg'] = self.args['patternRows'] - (self.info['count'] % self.args['patternRows']) #new #TODO: #check

def jerseyUpdate(self, returns): #def lace(k, startN, endN, length, c, patBeg=0, patternRows=2, spaceBtwHoles=1, offset=1, offsetReset=None, bed='f', gauge='1'): #TODO: ensure it works well for gauge 2
	genericUpdate(self, returns)

def getStitchData(k, bed, shapeData, imagePath='graphics/stitch-pat-map.png', stitchPatterns={}, colorArgs={}, gauge=2):
	patDetails = []
	stitchPatColors = []
	
	def get_parameters(func):
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

	# print(stitchPatterns) #remove #debug
	for (pattern, color) in stitchPatterns.items():
		params = get_parameters(globals()[pattern])
		# print(params) #remove #debug

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
								info['plaitC'] = None #new #would be updated if carrier available  #TODO: add plaiting open for jersey (default)
								if bed == 'b': info['plaitCside'] = 'r' #might be reassigned later
								else: info['plaitCside'] = 'l'
			
								# if 'passes' in info and info['passes'] < 2:
								# 	print(f'\nWARNING: changing pass count for {pattern} (color: {color}) from {info["passes"]} to {info["passes"]+1} so plaiting carrier can be consistently parked and retrieved on the same side.')
								# 	print(info['passes'])
								# 	info['passes'] += 1
								# 	print(info['passes'])
						elif arg == 'extensions':
							if 'stitchNumber' in patArgs[arg]: info['stitchNumber'] = patArgs[arg]['stitchNumber']
							if 'rollerAdvance' in patArgs[arg]: info['rollerAdvance'] = patArgs[arg]['rollerAdvance']
							if 'speedNumber' in patArgs[arg]: info['speedNumber'] = patArgs[arg]['speedNumber']

				pat = StitchPatDetails(pattern, args, info)

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
								info['plaitC'] = None #new #would be updated if carrier available
								if bed == 'b': info['plaitCside'] = 'r'
								else: info['plaitCside'] = 'l'

			pat = StitchPatDetails(pattern, args, info)

			if pat.pattern == 'garter': pat.update = garterUpdate.__get__(pat)
			elif pat.pattern == 'rib': pat.update = ribUpdate.__get__(pat)
			elif pat.pattern == 'interlock': pat.update = interlockUpdate.__get__(pat) #TODO: get this working
			elif pat.pattern == 'lace': pat.update = laceUpdate.__get__(pat) #TODO: get this working
			elif pat.pattern == 'jersey': pat.update = jerseyUpdate.__get__(pat)
			else: print(f'TODO: add support for {pat.pattern}')

			patDetails.append(pat)
			stitchPatColors.append(color)

	# check to see if there are any non-integer values for 'passes' or < 1 values
	jerseyPasses = 1 #new undent
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

	patKeys = list(stitchPatterns.keys())
	
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
	
	if jerseyPasses > 1: #new #check #v
		horizScale *= jerseyPasses
		rescale = True #new #^
	
	if rescale:
		imgData = imgData.resize((round(imgData.width*horizScale), round(imgData.height*vertScale)), Image.NEAREST) #scale image to size of shape img 
		imgHeight = imgData.height
		imgWidth = imgData.width

	imgData = imgData.transpose(Image.FLIP_TOP_BOTTOM) #so going from bottom to top
	
	return imgData, patDetails, stitchPatColors, jerseyPasses


#--- FUNCTION TO PROCESS/ANALYZE IMAGE THAT INDICATES STITCH PATTERN LOCATIONS ON CACTUS ---
# def imgToStitchPatternMap(k, bed, shapeData, imagePath='graphics/stitch-pat-map.png', stitchPatterns={}, colorArgs={}, gauge=2):
def imgToStitchPatternMap(k, imgData, stitchPatColors, stitchPatCount):
	'''
	*k is knitout Writer
	*bed specifies the needle bed that will knit the stitch pattern — valid values are 'f' (front bed) and 'b' (back bed)
	*shapeData is the data processed by PIL library from the shape img at the beginning of func shapeImgtoKnitout
	*imagePath is the path to the image that contains the stitch pattern data
	*stitchPatterns is a dictionary containing 
	*colorArgs is 
	*gauge is... the gauge

 	- Reads an image (white background, flat blobs of color to indicate a stitch pattern)
	- default stitch pattern is jersey (so if no blob, will treat as jersey)
	'''

	#------------
	imgHeight = imgData.height
	imgWidth = imgData.width

	palData = []

	for color in stitchPatColors:
		if type(color) == str: palData.append(ImageColor.getcolor(color, 'P'))
		elif type(color) == tuple and len(color) == 3: palData.append(color)
		else: raise ValueError(f"color values in stitchPatterns must be either a color name in string form e.g. 'red', or rgb tuple e.g. (255, 0, 0). Value: {color} is not valid.")

	# palData.append((255, 255, 255)) #white
	# palData = palData * (256//(len(palData)))
	palData.extend([(255, 255, 255)]*(256-len(palData)))
	palData = sum([list(x) for x in palData], [])

	pal = Image.new('P', (1, 1))
	pal.putpalette(palData)
	
	# print(stitchPatCount, stitchPatColors, pal.getcolors()) #remove #debug 
	imgData = imgData.convert('RGB')
	# imgData.show()
	# imgData = imgData.quantize(stitchPatCount+3, palette=pal)
	imgData = imgData.quantize(stitchPatCount+1, palette=pal, dither=0)

	palette = imgData.getcolors()

	# imgData.show() #remove
	
	print('palette:', palette) #remove #debug
	# if len(palette) == 1: bg = None #no bg
	if len(palette) == stitchPatCount: bg = None #no bg
	else: bg = len(palette)-1 #key for background color (white)

	# cols=[] #remove #debug
	rows = []
	for r in range(0, imgHeight):
		pat = None
		patNs = []
		row = {}
		for x in range(0, imgWidth):
			px = imgData.getpixel((x, r))
			# if px not in cols: cols.append(px) #remove #debug
			if px != bg:
				if pat is None or px == pat:
					patNs.append(x)
					if x == imgWidth-1:
						row[pat] = patNs #dict with pattern idx and needles #*#*#*
						rows.append(row)
				else:
					row[pat] = patNs #dict with pattern idx and needles #*#*#*
					patNs = []
					patNs.append(x) #new #check
					if x == imgWidth-1: rows.append(row)
				
				pat = px
			else: #background, not stitch pattern
				if not len(patNs) and x < imgWidth-1: continue
				elif len(patNs):
					row[pat] = patNs #dict with pattern idx and needles #*#*#*
					patNs = []
					pat = None

				if x == imgWidth-1:
					rows.append(row)

	# print('cols:', cols, len(cols)) #remove #debug
	return rows


# #--- FUNCTION TO PROCESS/ANALYZE IMAGE THAT INDICATES STITCH PATTERN LOCATIONS ON CACTUS ---
# def imgToStitchPatternMap(k, bed, shapeData, imagePath='graphics/stitch-pat-map.png', stitchPatterns={}, colorArgs={}, gauge=2):
# 	'''
# 	*k is knitout Writer
# 	*bed specifies the needle bed that will knit the stitch pattern — valid values are 'f' (front bed) and 'b' (back bed)
# 	*shapeData is the data processed by PIL library from the shape img at the beginning of func shapeImgtoKnitout
# 	*imagePath is the path to the image that contains the stitch pattern data
# 	*stitchPatterns is a dictionary containing 
# 	*colorArgs is 
# 	*gauge is... the gauge

#  	- Reads an image (white background, flat blobs of color to indicate a stitch pattern)
# 	- default stitch pattern is jersey (so if no blob, will treat as jersey)
# 	'''
# 	# stitchPatterns = {
# 	# 	'rib': 'blue',
# 	# 	'garter': ['red', 'green'] #(255, 0, 0),
# 	# }

# 	'''
# 	obj0 = stitchPatDetails(pattern, args)

# 	def mult(self, val):
# 		self.x = self.x*val

# 	obj0.mult = mult.__get__(obj0)

# 	obj0.mult(2)	
# 	'''
# 	# def updateGarter(self):
# 	# 	self.info['count'] += 1
# 	# 	if self.info['count'] % self.args['patternRows'] == 0:
# 	# 		if self.args['startBed'] == 'f': self.args['startBed'] = 'b'
# 	# 		else: self.args['startBed'] = 'f'

# 	# def updateRib(self):
# 	# 	print('TODO')

# 	# class StitchPatDetails:
# 	# 	def __init__(self, pattern, args, info):
# 	# 		self.pattern = pattern
# 	# 		self.args = args
# 	# 		self.info = info

# 	patDetails = []
# 	stitchPatColors = []
	
# 	def get_parameters(func):
# 		alreadyCovered = ['k', 'startN', 'endN', 'length', 'c']
# 		keys = func.__code__.co_varnames[:func.__code__.co_argcount][::-1]
# 		sorter = {j: i for i, j in enumerate(keys[::-1])}

# 		if func.__defaults__ is not None:
# 			values = func.__defaults__[::-1]
# 			kwargs = {i: j for i, j in zip(keys, values)}
# 			# if 'returnXfers' in kwargs: kwargs['returnXfers'] = True #change default to True
# 			if 'homeBed' in kwargs: kwargs['homeBed'] = bed #change default to bed arg passed in main func
# 			if 'startBed' in kwargs: kwargs['startBed'] = bed #change default to bed arg passed in main func
# 			if 'currentBed' in kwargs: kwargs['currentBed'] = bed #change default to bed arg passed in main func
# 			if 'gauge' in kwargs: kwargs['gauge'] = gauge #change the default to gauge arg passed in main func
# 		else: kwargs = None
		
# 		sorted_args = {i: 'undefined' for i in sorted(keys, key=sorter.get) if i not in alreadyCovered}

# 		if kwargs is not None:
# 			for i in sorted_args:
# 				if i in kwargs: sorted_args[i] = kwargs[i]
		
# 		# print(sorted_args) #remove #debug
# 		return sorted_args

# 	print(stitchPatterns) #remove #debug
# 	for (pattern, color) in stitchPatterns.items():
# 		params = get_parameters(globals()[pattern])

# 		if type(color) == list:
# 			for col in color:
# 				# patObj = {'pattern': pattern}
# 				args = params.copy()
# 				info = {'count': 0, 'passes': 1}
# 				if col in colorArgs:
# 					patArgs = colorArgs[col]
# 					for arg in patArgs:
# 						if arg in args: args[arg] = patArgs[arg]
# 						elif arg == 'length' or arg == 'passes': info['passes'] = patArgs[arg] #TODO: refine this
# 						elif arg == 'features':
# 							if 'plaiting' in patArgs[arg]:
# 								info['plaitC'] = None #new #would be updated if carrier available  #TODO: add plaiting open for jersey (default)
# 								if 'passes' in info and info['passes'] < 2:
# 									print(f'\nWARNING: changing pass count for {pattern} (color: {color}) from {info["passes"]} to {info["passes"]+1} so plaiting carrier can be consistently parked and retrieved on the same side.')
# 									info['passes'] += 1
# 							# info['features'] = patArgs[arg] #new for things like using multiple carriers (would say 'plaiting')
# 						elif arg == 'extensions':
# 							if 'stitchNumber' in patArgs[arg]: info['stitchNumber'] = patArgs[arg]['stitchNumber']
# 							if 'rollerAdvance' in patArgs[arg]: info['rollerAdvance'] = patArgs[arg]['rollerAdvance']
# 							if 'speedNumber' in patArgs[arg]: info['speedNumber'] = patArgs[arg]['speedNumber']
# 						# elif arg == 'c': patObj['carrier'] = patArgs['c'] #if meant to use a different carrier (#removed this for now, since complicates things bc carrier placement)

# 				# patObj['args'] = args
# 				pat = StitchPatDetails(pattern, args, info)

# 				if pat.pattern == 'garter': pat.update = garterUpdate.__get__(pat)
# 				elif pat.pattern == 'rib': pat.update = ribUpdate.__get__(pat)
# 				elif pat.pattern == 'interlock': pat.update = interlockUpdate.__get__(pat) #TODO: get this working
# 				elif pat.pattern == 'lace': pat.update = laceUpdate.__get__(pat) #TODO: get this working
# 				elif pat.pattern == 'jersey': pat.update = jerseyUpdate.__get__(pat)
# 				else: print(f'TODO: add support for {pat.pattern}')

# 				# if 'length' in pat.args and pat.args['length'] > 1:
# 				# if 'passes' in pat.info and pat.info['passes'] != 1: #TODO: maybe remove this #?
# 				# 	if bed == 'f': pat.info['side'] = 'l'
# 				# 	else: pat.info['side'] = 'r'

# 				patDetails.append(pat)
# 				# stitchPatDetails.append({'pattern': pattern, 'args': args})
# 				stitchPatColors.append(col)
# 		else:
# 			args = params.copy()
# 			info = {'count': 0, 'passes': 1}
# 			if color in colorArgs:
# 				patArgs = colorArgs[color]
# 				for arg in patArgs:
# 					if arg in args: args[arg] = patArgs[arg]
# 					elif arg == 'length' or arg == 'passes': info['passes'] = patArgs[arg] #TODO: refine this
# 					elif arg == 'features':
# 							if 'plaiting' in patArgs[arg]: info['plaitC'] = None #new #would be updated if carrier available
# 					# elif arg == 'features': info['features'] = patArgs[arg] #new for things like using multiple carriers

# 			pat = StitchPatDetails(pattern, args, info)

# 			if pat.pattern == 'garter': pat.update = garterUpdate.__get__(pat)
# 			elif pat.pattern == 'rib': pat.update = ribUpdate.__get__(pat)
# 			elif pat.pattern == 'interlock': pat.update = interlockUpdate.__get__(pat) #TODO: get this working
# 			elif pat.pattern == 'lace': pat.update = laceUpdate.__get__(pat) #TODO: get this working
# 			elif pat.pattern == 'jersey': pat.update = jerseyUpdate.__get__(pat)
# 			else: print(f'TODO: add support for {pat.pattern}')

# 			# if 'length' in pat.args and pat.args['length'] > 1:
# 			# if 'passes' in pat.info and pat.info['passes'] != 1: #remove #?
# 			# 	if bed == 'f': pat.info['side'] = 'l'
# 			# 	else: pat.info['side'] = 'r'

# 			patDetails.append(pat)
# 			# stitchPatDetails.append({'pattern': pattern, 'args': args})
# 			stitchPatColors.append(color)

# 		# check to see if there are any non-integer values for 'passes' or < 1 values
# 		jerseyPasses = 1
# 		if any(pat.info['passes'] < 1 or pat.info['passes'] % 1 != 0 for pat in patDetails):
# 			print('\nWARNING: scaling up by 2.')
# 			jerseyPasses = 2 #TODO: make it possible to scale up by more than two
# 			for pat in patDetails:
# 				pat.info['passes'] = int(pat.info['passes']*2)
# 				# pat.info['passes'] *= 2

# 	patKeys = list(stitchPatterns.keys())
	
# 	imgData = Image.open(imagePath)

# 	# check to ensure length and width of stitchPatImg is same as shapeImg
# 	imgHeight = imgData.height
# 	imgWidth = imgData.width
# 	rescale = False
# 	vertScale = 1
# 	horizScale = 1

# 	if imgHeight != shapeData.height:
# 		vertScale = shapeData.height/imgHeight
# 		rescale = True
# 	if imgWidth != shapeData.width:
# 		horizScale = shapeData.width/imgWidth
# 		rescale = True
	
# 	if jerseyPasses > 1: #scale up width because jerseyPasses being > 1 will automatically scale up height #new #check #v
# 		horizScale *= jerseyPasses
# 		rescale = True #new #^
	
# 	if rescale:
# 		imgData = imgData.resize((round(imgData.width*horizScale), round(imgData.height*vertScale)), Image.NEAREST) #scale image to size of shape img 
# 		imgHeight = imgData.height
# 		imgWidth = imgData.width

# 	imgData = imgData.transpose(Image.FLIP_TOP_BOTTOM) #so going from bottom to top

# 	#------------

# 	palData = []
# 	# palette = []

# 	# for color in stitchPatterns.values():
# 	for color in stitchPatColors:
# 		if type(color) == str: palData.append(ImageColor.getcolor(color, 'P'))
# 		elif type(color) == tuple and len(color) == 3: palData.append(color)
# 		# if type(color) == str: palette.append(ImageColor.getcolor(color, 'P'))
# 		# elif type(color) == tuple and len(color) == 3: palette.append(color)
# 		else: raise ValueError(f"color values in stitchPatterns must be either a color name in string form e.g. 'red', or rgb tuple e.g. (255, 0, 0). Value: {color} is not valid.")

# 	# palData = [(255, 255, 255)]*(256-len(palette))
# 	# palData.extend(palette)

# 	palData.extend([(255, 255, 255)]*(256-len(palData)))
# 	palData = sum([list(x) for x in palData], [])

# 	pal = Image.new('P', (1, 1))
# 	pal.putpalette(palData)
	
# 	imgData = imgData.convert('RGB')
# 	imgData = imgData.quantize(len(stitchPatterns)+3, palette=pal)

# 	palette = imgData.getcolors()
	
# 	if len(palette) == 1: bg = None #no bg
# 	else: bg = len(palette)-1 #key for background color (white)

# 	rows = []
# 	for r in range(0, imgHeight):
# 		pat = None
# 		patNs = []
# 		# row = {}
# 		# list3.extend([(k, v) for k, v in dict1.items()])
# 		# list(dict1.items())
# 		# row = []
# 		row = {}
# 		# n = 0.0
# 		for x in range(0, imgWidth):
# 			px = imgData.getpixel((x, r))
# 			if px != bg:
# 				if pat is None or px == pat:
# 					# patNs.append(n)
# 					patNs.append(x)
# 					if x == imgWidth-1:
# 						row[pat] = patNs #dict with pattern idx and needles #*#*#*
# 						# row.append({'idx': pat, 'needles': patNs}) #dict with pattern idx and needles #*#*#*
# 						# row.append((patKeys[pat], patNs)) #tuple
# 						rows.append(row)
# 				else:
# 					row[pat] = patNs #dict with pattern idx and needles #*#*#*
# 					# row.append({'idx': pat, 'needles': patNs}) #dict with pattern idx and needles #*#*#*
# 					# row.append((patKeys[pat], patNs)) #tuple
# 					patNs = []
# 					if x == imgWidth-1: rows.append(row)
				
# 				pat = px
# 			else: #background, not stitch pattern
# 				if not len(patNs) and x < imgWidth-1: continue
# 				elif len(patNs):
# 					row[pat] = patNs #dict with pattern idx and needles #*#*#*
# 					# row.append({'idx': pat, 'needles': patNs}) #dict with pattern idx and needles #*#*#*
# 					# row.append((patKeys[pat], patNs)) #tuple
# 					patNs = []
# 					pat = None

# 				if x == imgWidth-1:
# 					rows.append(row)
# 					# if pat is None: rows.append((None, []))
# 					# else: row.append

# 				#TODO: add new section stuff?

# 	# print(imgData.mode) #remove #debug
# 	# print(imgData.getcolors()) #remove #debug
# 	# imgData.show() #remove #debug

# 	# print(rows) #remove #debug
# 	# print(patDetails[0].args) #remove #debug

# 	# return patDetails, rows
# 	# for pat in patDetails:
# 	# 	print(pat.pattern)

# 	return patDetails, rows, jerseyPasses


#--- FUNCTION TO PROCESS/ANALYZE CACTUS-ESQUE IMAGE AND OUTPUT KNITOUT ---
def shapeImgToKnitout(k, imagePath='graphics/knitMap.png', gauge=2, scale=1, maxShortrowCount=1, addBindoff=True, excludeCarriers=[], addBorder=True, stitchPatternsFront={'imgPath': None, 'patterns': {}, 'colorArgs': {}}, stitchPatternsBack={'imgPath': None, 'patterns': {}, 'colorArgs': {}}, incMethod='split', closedCaston=True, openBindoff=False):
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
	*incMethod is a string indicating the increasing method that should be used in the piece — valid values are 'split', 'xfer', and 'zig-zag' (NOTE: this might be overridden if a large amount of needles are involved in a particular increase [e.g. automatically zig-zag if > 4 needles in inc])

	- Reads a shape image (black and white) and generates an array of rows containing pixel sub-arrays that either have the value 0 (black - shape) or 255 (white - background)
	- Optionally, also reads/processes a stitch pattern image (well, calls the function 'imgToStitchPattern' to read it)
	- Goes through each row and separates each chunk of black pixels into sections (based on whether there is white space separating sections of black pixels)
	- Goes through rows again and assigns a carrier to each section, allowing for shortrowing; information is stored in 'pieceMap', with lists containing tuples for each section -- e.g. pieceMap[0] = [(1, [1, 2, 3]), (2, [10, 11, 12])] means row 0 uses carrier 1 on needles 1,2,3 and carrier 2 on needles 10,11,12
	- Finally, outputs a 'visualization' (just for, ya know, visualization purposes) with 0 being white space, and knitted mass indicated by carrier number
	'''

	''' TODO:
	[] add option to add carriers back in for availability if they are no longer being used
	[] add option for plaiting via knitting with two carriers to make half-gauge jersey less stretchy
	'''
	#1. Read image data from input path; resize based on gauge
	imgData = Image.open(imagePath).convert('L')

	if scale != 1: imgData = imgData.resize((imgData.width*scale, imgData.height*scale), Image.NEAREST) #scale image according to passed 'scale' value, if scale != 1

	# if scale != 1 or gauge > 1: imgData = imgData.resize((imgData.width*scale, imgData.height*scale*gauge), Image.NEAREST) #scale image according to passed 'scale' value #scale gauge vertically to elongate image, if gauge > 1 #remove #?
	
	imgData = imgData.transpose(Image.FLIP_TOP_BOTTOM) #so going from bottom to top

	# imgData = imgData.point(lambda x: 0 if x < 128 else 255, '1')
	# imgData.show()

	width = imgData.width

	# plaitInfo = {'count': 0, 'assigned': 0, 'lastRows': {}, 'carriers': []} #go back! #?
	plaitStPatsRows = []
	# plaitStPats = {} #go back! #?
	rawStDataF = None #new
	stitchPatDataF = None
	stitchPatDetailsF = []
	jerseyPassesF = 1

	rawStDataB = None #new
	stitchPatDataB = None
	stitchPatDetailsB = []
	jerseyPassesB = 1
	
	#new #check #v
	if stitchPatternsFront['imgPath'] is not None:
		rawStDataF, stitchPatDetailsF, stitchPatColorsF, jerseyPassesF = getStitchData(k, bed='f', shapeData=imgData, imagePath=stitchPatternsFront['imgPath'], stitchPatterns=stitchPatternsFront['patterns'], colorArgs=stitchPatternsFront['colorArgs'])
		# stitchPatDetailsF, stitchPatDataF, jerseyPassesF = imgToStitchPatternMap(k, bed='f', shapeData=imgData, imagePath=stitchPatternsFront['imgPath'], stitchPatterns=stitchPatternsFront['patterns'], colorArgs=stitchPatternsFront['colorArgs'])
	
	# for i, st in enumerate(stitchPatDetailsF): #remove #debug
	# 	print(i, st)
	if stitchPatternsBack['imgPath'] is not None:
		rawStDataB, stitchPatDetailsB, stitchPatColorsB, jerseyPassesB = getStitchData(k, bed='b', shapeData=imgData, imagePath=stitchPatternsBack['imgPath'], stitchPatterns=stitchPatternsBack['patterns'], colorArgs=stitchPatternsBack['colorArgs'])
		# stitchPatDetailsB, stitchPatDataB, jerseyPassesB = imgToStitchPatternMap(k, bed='b', shapeData=imgData, imagePath=stitchPatternsBack['imgPath'], stitchPatterns=stitchPatternsBack['patterns'], colorArgs=stitchPatternsBack['colorArgs'])

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

		for idx, stDeets in enumerate(stitchPatDetailsF): #new #check
			if 'plaitC' in stDeets.info:
				# if not 'f' in plaitStPats: plaitStPats['f'] = [] #go back! #?
				# plaitStPats['f'].append(idx) #go back! #?
				stIdxRow1 = next((r for r, data in enumerate(stitchPatDataF) if idx in data.keys()), None)
				# plaitStPats['f'].append([idx, stIdxRow1])
				plaitStPatsRows.append([stIdxRow1, idx, 'f'])
				plaitInfo['f'].append(idx) #new #*
				# stIdxRow1 = next(([r, data] for r, data in enumerate(stitchPatDataF) if idx in data.keys()), None)
				plaitInfo['count'] += 1
				# carriersForPlait += 1 #new #check
		
		# stitchPatDataF = imgToStitchPatternMap(k, imgData=rawStDataF, stitchPatColors=stitchPatColorsF, stitchPatCount=len(stitchPatDetailsF))
	if rawStDataB is not None:
		stitchPatDataB = imgToStitchPatternMap(k, imgData=rawStDataB, stitchPatColors=stitchPatColorsB, stitchPatCount=len(stitchPatDetailsB))

		for idx, stDeets in enumerate(stitchPatDetailsB): #new #check
			if 'plaitC' in stDeets.info:
				# if not 'b' in plaitStPats: plaitStPats['b'] = [] #go back! #?
				# plaitStPats['b'].append(idx) #go back! #?
				stIdxRow1 = next((r for r, data in enumerate(stitchPatDataB) if idx in data.keys()), None)
				stIdxRowLast = next((r for r, data in enumerate(stitchPatDataB) if idx in data.keys()), None)
				# stitchPatDataF[stR][stIdx]
				# plaitStPats['b'].append([idx, stIdxRow1])
				plaitStPatsRows.append([stIdxRow1, idx, 'b'])
				plaitInfo['b'].append(idx) #new #*
				plaitInfo['count'] += 1
			# if 'plaitC' in stDeets.info: carriersForPlait += 1 #new #check
		
		# stitchPatDataB = imgToStitchPatternMap(k, imgData=rawStDataB, stitchPatColors=stitchPatColorsB, stitchPatCount=len(stitchPatDetailsB))
	#new #check #^

	if len(plaitStPatsRows): plaitStPatsRows.sort(key=lambda info: info[0]) #sort by row

	'''
	imageData = io.imread(imagePath)
	if scale != 1: imageData = resize(imageData, (imageData.shape[0]*scale, imageData.shape[1]*scale), anti_aliasing=True) #scale image according to passed 'scale' value

	if gauge > 1: imageData = resize(imageData, (imageData.shape[0]*gauge, imageData.shape[1]), anti_aliasing=True) #scale gauge vertically to elongate image, if gauge > 1
	imageData = np.flipud(imageData) #so going from bottom to top

	# imgToStitchPatternMap(k, shapeMap=imageData)
	
	width = len(imageData[0])

	# io.imshow(imageData)
	# io.show()
	'''

	carrierCount = 1
	emptyNeedles = []
	takeOutAtEnd = [] #for carriers to take out at end, might be modified as carriers are taken out #new#new #check #*#*#*#*#*#* #come back!!
	# takeOutAtEnd = ['1'] #for carriers to take out at end, might be modified as carriers are taken out #new #remove #?
	gradualSplit = 1*gauge #split count for when gradual split should be implemented
	maxSplit = 1*gauge #current max split count supported by doubleBedInc func

	if gauge > 1:
		# width = (width*gauge)+1 #remove #?
		for n in range(0, width):
			if n % gauge == 0: emptyNeedles.append(f'b{n}')
			elif (n-1) % gauge == 0: emptyNeedles.append(f'f{n}')
			else:
				emptyNeedles.append(f'f{n}')
				emptyNeedles.append(f'b{n}')

	# print('\nimageData:') #remove
	# print(imageData) #remove

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
	rowsEdgeNeedles2 = []

	maxNeedle = 0 #starts at zero, will be increased
	increasing = False #for now (value will be changed if increasing detected)

	castonLeftN = None
	castonRightN = None

	imgHeight = imgData.height
	imgWidth = imgData.width

	for r in range(0, imgHeight): #new #*#*#*
		# carrierCount = 0 #reset each time
		leftmostN = None

		row = []
		section = []
		rowTakenNeedles = []

		# for n in range(0, len(imageData[r])): #remove #?
		n = -0.5 #start here
		for x in range(0, imgWidth): #new #*#*#*
			n += 0.5
			px = imgData.getpixel((x, r)) #TODO: have option for pixel than is grey (inc / dec of one needle for gauge 2 [so just front or back; keeping track])

			# if (px == 0 and imageData[r][n] != 0) or (px != 0 and imageData[r][n] == 0): print('!!!') #remove #debug #*#*#*
			# if (px == 0 and imageData[r][n] != 0): print(px, math.floor(imageData[r][n])) #remove #debug #*#*#*

			# if imageData[r][n] == 0: #remove #?
			# if math.floor(imageData[r][n]) == 0: #remove #?
			if px == 0: #black #new #*#*#*
				if leftmostN is None: leftmostN = n

				section.append(n)
				takenNeedle = int(n*gauge)
				if gauge == 1 or (takenNeedle % gauge == 0):
					rowTakenNeedles.append(f'f{takenNeedle}') #new #check
				if gauge == 1 or ((takenNeedle+1) % gauge == 0):
					rowTakenNeedles.append(f'b{takenNeedle}') #new #check

				# if n == len(imageData[r]) - 1: #remove #?
				if x == imgWidth - 1: #new #*#*#*
					row.append(section)

					if r == 0 and castonLeftN is None: castonLeftN, castonRightN = convertGauge(gauge, row[0][0], row[0][len(row[0])-1])

					if len(row) > carrierCount: carrierCount = len(row)

					# if r > 0 and r < (len(imageData)-1) and len(rows[len(rows)-1]) < len(rows[len(rows)-2]) and carrierCount >= len(rows[len(rows)-2]): #if necessary, split prev row [-1] into multiple sections (based on number of sections in prev row to that [-2]) if current carrierCount >= # of sections in [-2]
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
			else: #white
				if len(section) == 0: continue
				else:
					if section[len(section)-1] > maxNeedle: maxNeedle = section[len(section)-1]

					row.append(section)
					section = []
					newSection = False
					for i in range(x, imgWidth): #new #*#*#*
						if imgData.getpixel((i, r)) == 0: #black #new #*#*#*
							x = i
							newSection = True
							break

					if not newSection: #very last section
						if r == 0: castonLeftN, castonRightN = convertGauge(gauge, row[0][0], row[0][len(row[0])-1])

						if len(row) > carrierCount: carrierCount = len(row)

						# if r > 0 and r < (len(imageData)-1) and len(rows[len(rows)-1]) < len(rows[len(rows)-2]) and carrierCount >= len(rows[len(rows)-2]): #if necessary, split prev row [-1] into multiple sections (based on number of sections in prev row to that [-2]) if current carrierCount >= # of sections in [-2]
						# if r > 0 and r < (imgHeight-1) and len(rows[r-1]) < len(rows[r-2]) and len(row) >= len(rows[r-2]): #if necessary, split prev row [-1] into multiple sections (based on number of sections in prev row to that [-2]) if current carrierCount >= # of sections in [-2]
						if r > 0 and r < (imgHeight-1) and len(rows[r-1]) < len(rows[r-2]) and len(row) >= len(rows[r-2]):
							startPt = 1
							minus1Needles = rows[r-1]
							minus2Needles = rows[r-2]
							# minus1Needles = rows[len(rows)-1]
							# minus2Needles = rows[len(rows)-2]
							for n2 in range(startPt, len(minus2Needles)):
								for n1 in range(0, len(minus1Needles)):
									for i in range(1, len(minus1Needles[n1])):
										if minus2Needles[n2][0] == minus1Needles[n1][i]:
											minus1Needles[n1:n1+1] = minus1Needles[n1][:i], minus1Needles[n1][i:]
											startPt += 1
											break
													
						# rowsEdgeNeedles.append(list(convertGauge(gauge=gauge, leftN=leftmostN, rightN=maxNeedle))) #TODO: determine if still need this
						rowsEdgeNeedles.append(list(convertGauge(gauge=gauge, leftN=leftmostN, rightN=row[-1][-1]))) #TODO: determine if still need this

						rows.append(row)
						rowsTakenNeedles.append(rowTakenNeedles) #new check
						break #go to next row
	# -----------------------------

	# maxNeedle *= gauge #convert maxNeedle to gauge
	maxNeedle = convertGauge(gauge, maxNeedle) #convert maxNeedle to gauge

	# for i, r in enumerate(rows): #remove #debug #*#*#*#*#*#*
	# 	print(f'\n{i}: {r}') #remove
	# 	print(rowsTakenNeedles[i])
	
	#3. Go through rows data and assign carriers to each section
	sections = [] #list for storing SectionInfo

	carrierOrder = [] #list for storing carrier order, helpful when want a certain carrier to be used e.g. always on left (will change if > 2 sections in piece)

	lowNumCs = 0

	if len(plaitInfo['f']):
		frontPlaitCs = len(plaitInfo['f'])
		backPlaitCs = len(plaitInfo['b'])
		availableCs = 6-carrierCount
		# lowNumCs = min(frontPlaitCs, availableCs)

		aCs = availableCs
		# while count < C and f > 0:
		while lowNumCs < availableCs and aCs > 0:
			if lowNumCs % 2 == 0 or backPlaitCs == 0:
				frontPlaitCs -= 1
				lowNumCs += 1
			else: backPlaitCs -= 1
			aCs -= 1

		# else: 
		# if len(plaitInfo['b']):
			

		# 	lowNumCs = len(plaitInfo['carriers'])//2
		# 	if lowNumCs > len(plaitInfo['f']): lowNumCs = len(plaitInfo['f'])
		# 	else: 

		# else: lowNumCs = len(plaitInfo['carriers'])
		# lowNumCs = len(plaitInfo['carriers'])

	for cs in range(1, 7): #initialize sections (but won't add leftN & rightN until later)
		if len(carrierOrder) == carrierCount: break
		cStr = str(cs)
		if cStr in excludeCarriers or cs <= lowNumCs: continue
		else:
			sections.append(SectionInfo(cs))
			carrierOrder.append(cStr) #carrierOrder starts out as just [1, 2, 3]

	mainC = carrierOrder[0] #new #check

	# for cs in range(0, carrierCount): #initialize sections (but won't add leftN & rightN until later)
	# 	if str(cs) in excludeCarriers:
	# 		ec = cs + 1
	# 		while ec < 6:
	# 			if str(ec) in excludeCarriers:
	# 				ec += 1
	# 			else:
	# 				cs = ec
	# 				break
		
	# 	sections.append(SectionInfo(cs + 1))
	# 	carrierOrder.append(str(cs+1)) #carrierOrder starts out as just [1, 2, 3]

	# if any(eNs[0] < rowsEdgeNeedles[rowsEdgeNeedles.index(eNs)-1][0] for eNs in rowsEdgeNeedles) or any(eNs[1] > rowsEdgeNeedles[rowsEdgeNeedles.index(eNs)-1][1] for eNs in rowsEdgeNeedles): increasing = True #go back! #?
	# else: increasing = False

	# foundIt = next((i for i, eNs in enumerate(rowsEdgeNeedles) if eNs[0] < rowsEdgeNeedles[rowsEdgeNeedles.index(eNs)-1][0]), None)
	# print(rowsEdgeNeedles[foundIt], rowsEdgeNeedles[foundIt-1])

	# if addBorder and not increasing: #TODO: change this to if no inc (detect in any inc in )
	# 	addBorder = False
	# 	print('\ntoggling addBorder to False, since no increasing in piece')

	availableCarriers = []
	for cs in range(6, 0, -1): #new #v
		cStr = str(cs)
		if cStr not in carrierOrder and cStr not in excludeCarriers: availableCarriers.append(cStr) #new #^

	# for cs in range(6, carrierCount, -1): #remove #v
	# 	if str(cs) not in excludeCarriers: availableCarriers.append(str(cs)) #remove #^
	wasteC = mainC #new#new

	if '5' in availableCarriers: #prioritize 5 as borderC since it seems to work well
		drawC = availableCarriers.pop(availableCarriers.index('5'))
		borderC = drawC
		takeOutAtEnd.append(drawC)
	elif len(availableCarriers):
		borderC = availableCarriers.pop() #it will be 6, since that's what would be left over in this case
		drawC = borderC
		takeOutAtEnd.append(drawC)
	else:
		borderC = None #new
		drawC = carrierOrder[-1] #whichever carrier comes in last #new#new
		# drawC = carrierOrder[0] #whichever carrier comes in last (since carrier order should be backwards in terms of time) #remove #?
	
	otherCs = [] #new#new #v
	for cs in carrierOrder:
		takeOutAtEnd.append(cs)
		if cs != drawC and cs != wasteC: otherCs.append(cs) #^
	
	# if '2' in availableCarriers:
	# 	drawC = availableCarriers.pop(availableCarriers.index('2'))
	# 	borderC = drawC
	# elif len(availableCarriers):
	# 	borderC = availableCarriers.pop()
	# 	drawC = borderC
	# else:
	# 	borderC = None #new
	# 	drawC = carrierOrder[0] #whichever carrier comes in last (since carrier order should be backwards in terms of time)
	
	# # if len(availableCarriers): borderC = availableCarriers.pop()
	# # else: borderC = None

	print('\nmaxNeedle:', maxNeedle) #remove #debug

	''' #remove #v
	shortrowLeftPrep = [idx for idx, element in enumerate(rows) if len(element) > 1] #here we check if the piece contains > 2 sections in any given row and then, if so, assigns index of that row #TODO: make sure this is possible/effective for multiple left sections

	if len(shortrowLeftPrep) > 0:
		if len(shortrowLeftPrep) > 1 and len(rows[shortrowLeftPrep[0]]) < 3:
			manySections = []
			manyIdx = None
			for sr in shortrowLeftPrep:
				if len(rows[sr]) > 2:
					manyIdx = sr
					manySections = rows[sr]
					break
			if manyIdx is not None:
				firstSectionLeftN = manySections[0][0]
				twoSections = rows[shortrowLeftPrep[0]]
				if twoSections[0][0] - firstSectionLeftN < 0: shortrowLeftPrep = manyIdx #this is really not always true but my brain hurts so it will have to do for now
				else: shortrowLeftPrep = shortrowLeftPrep[0]
		else: shortrowLeftPrep = shortrowLeftPrep[0]

	else: shortrowLeftPrep = False #if the piece doesn't contain > 2 sections in any row

	shortrowLeftPrep = False #remove #debug #*#*#*#*#*#* #TODO: remove all shortrowLeftPrep stuff
	''' #remove #^

	pieceMap = [] #list for storing overarching carrier/needles data for rows/sections

	#now finally going through rows

	mainCSection = 0 #might be redefined
	rightCarriers = [] #carriers to the right of main carrier

	# firstNeedles = {}

	# firstNeedles = {'1': [castonLeftN, castonRightN]} #remove #?
	firstNeedles = {mainC: [castonLeftN, castonRightN]} #new#new

	#for storing first and last rows each carrier appears in
	workingRows = {mainC: [0]} #new#new
	# workingRows = {'1': [0]} #remove #?
	# lastRows = {}

	wasteWeights = {}
	wasteBoundaryExpansions = {}

	for r in range (0, len(rows)):
		rowMap = {}

		taken = [] #not sure if this is really needed, but it's just an extra step to absolutely ensure two sections in one row don't used same carrier

		#loop through sections in row
		for i in reversed(range(0, len(rows[r]))): #go backwards so new carriers are added on left #new
			leftN = rows[r][i][0] #detect the left and right-most needle in each section for that row
			rightN = rows[r][i][len(rows[r][i]) - 1]

			match = False #bool that is toggled to True if the prev leftN & rightN for a carrier aligns with section (otherwise, use 'unusedC')
			unusedC = None #if above^ stays False, stores index (in reference to 'sections' list) of carrier that hasn't been used in piece yet

			for s in range(0, carrierCount):
				if s in taken: continue

				if sections[s].leftN is None: #leftN & rightN will still be 'None' (see class SectionInfo) if not used in piece yet
					if unusedC is None: unusedC = s #index of unused carrier, if needed
					continue
				
				# if r != shortrowLeftPrep and (leftN < sections[s].leftN and rightN < sections[s].leftN) or (leftN > sections[s].rightN and rightN > sections[s].rightN): continue #prev leftN & rightN for this carrier doesn't align with leftN & rightN of current section, so continue searching #remove #*
				if (leftN < sections[s].leftN and rightN < sections[s].leftN) or (leftN > sections[s].rightN and rightN > sections[s].rightN): continue #prev leftN & rightN for this carrier doesn't align with leftN & rightN of current section, so continue searching
				else: #it's a match! (or time for shortrowLeftPrep)
					'''#remove #v
					if i == 0 and r == shortrowLeftPrep: #if it's the row before the 1st actual shortrow for shortrowLeft, update carrierOrder so this for loop checks that carrier first & it remains on the left
						prevSectionStart = sections[s].leftN
						if addBorder and prevSectionStart - leftN > 0: #increase
							increasing = True #new #check #*#*#*#*#*#*
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
								if expandBoundaryRow in wasteBoundaryExpansions: wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, rightN=prevSectionStart-1)
								else:
									wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, rightN=prevSectionStart-1)

							wasteWeights[r]['left'] = list(convertGauge(gauge, leftN, wasteRightBoundary))
							if borderC not in firstNeedles: firstNeedles[borderC] = list(convertGauge(gauge, wasteRightBoundary+1, rightN))

						carrierOrder.insert(0, carrierOrder.pop(carrierCount-1)) #move shortrowLeft carrier to front of carrierOrder list
						sections.insert(0, sections.pop(carrierCount-1)) #move section to correct location too so can be referenced by index (s) correctly
						workingRows[carrierOrder[0]] = [r] #new
						# firstRows[carrierOrder[0]] = r #new
						firstNeedles[carrierOrder[0]] = rowsEdgeNeedles[r]
						for o in range(0, len(carrierOrder)):
							if carrierOrder[o] == '1':
								mainCSection = o
								break
					else: #not shortrowleftprep
					'''#remove #^
					if addBorder and sections[s].leftN - leftN > 0:

						increasing = True #new #check #*#*#*#*#*#*

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
							# if expandBoundaryRow in wasteBoundaryExpansions: wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, rightN=prevSectionStart-1) #remove #?
							else:
								wasteBoundaryExpansions[expandBoundaryRow] = convertGauge(gauge, rightN=sections[s].leftN-1)

						wasteWeights[r]['left'] = list(convertGauge(gauge, leftN, wasteRightBoundary))
						if borderC not in firstNeedles: firstNeedles[borderC] = list(convertGauge(gauge, wasteRightBoundary+1, rightN))

					if addBorder and rightN - sections[s].rightN > 0: #increase
						increasing = True #new #check #*#*#*#*#*#*

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

						wasteWeights[r]['right'] = list(convertGauge(gauge, wasteLeftBoundary, rightN))
						if borderC not in firstNeedles: firstNeedles[borderC] = list(convertGauge(gauge, leftN, wasteLeftBoundary-1))

					sections[s].leftN = leftN
					sections[s].rightN = rightN
					sections[s].row = r #update row so know which is last #new
					newRowSection = {carrierOrder[s]: rows[r][i]}
					rowMap = {**newRowSection, **rowMap} #add new section to beginning of rowMap since looping in reverse
					taken.append(s)
					match = True
					break

			if not match: #need to use unusedC and add new carrier for shortrowing
				# for sect in sections:  #remove #debug #v
				# 	print(sect.c, sect.leftN, sect.rightN) #remove #debug #^
				# if carrierOrder[unusedC] != '1': #remove #?
				if carrierOrder[unusedC] != mainC: #new#new
					workingRows[carrierOrder[unusedC]] = [r]
					firstNeedles[carrierOrder[unusedC]] = rowsEdgeNeedles[r]
					if leftN > sections[mainCSection].rightN: rightCarriers.append(carrierOrder[unusedC])
					
					lastRowMapKeys = list(pieceMap[r-1].keys())
					prevSectionEnd = pieceMap[r-1][lastRowMapKeys[len(lastRowMapKeys)-1]] #last needle of last section
					prevSectionEnd = prevSectionEnd[len(prevSectionEnd)-1]

					if addBorder and rightN -  prevSectionEnd > 0: #increase
						if len(wasteWeights) == 0: rightCarriers.append(borderC)

						if not r in wasteWeights: wasteWeights[r] = dict()
						
						if r - wasteWeightsRowCount > 0: pStart = r - wasteWeightsRowCount
						else: pStart = 0
						wasteLeftBoundary = None
						expandBoundaryRow = None
						for p in range(pStart, r): #to make sure wasteWeights aren't knitted on taken needles
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

						wasteWeights[r]['right'] = list(convertGauge(gauge, wasteLeftBoundary, rightN))
						if borderC not in firstNeedles: firstNeedles[borderC] = list(convertGauge(gauge, leftN, wasteLeftBoundary-1))

				taken.append(unusedC)
				sections[unusedC].leftN = leftN
				sections[unusedC].rightN = rightN
				newRowSection = {carrierOrder[unusedC]: rows[r][i]}
				rowMap = {**newRowSection, **rowMap} #add new section to beginning of rowMap since looping in reverse

		pieceMap.append(rowMap)
	# -----------------------
	# print('\npieceMap:') #remove #*#*#*#*#*#*
	# for r in range(0, len(pieceMap)):
	# 	print(r,pieceMap[r]) #remove
	print(f'\nincreasing is {increasing}') #remove #debug

	if addBorder and not increasing:
		addBorder = False
		print('\ntoggling addBorder to False, since no increasing in piece')

	for sect in sections:
		workingRows[f'{sect.c}'].append(sect.row)
		# lastRows[f'{sect.c}'] = sect.row

	if addBorder:
		wasteWeightsKeys = list(wasteWeights.keys()) #rows

		firstWasteWeightRow = wasteWeightsKeys[0]
		# global lastWasteWeightRow #remove #?
		lastWasteWeightRow = wasteWeightsKeys[len(wasteWeightsKeys)-1]
		if borderC is None:
		# couldBeBorderC = None
			for c, cRows in workingRows.items():
				if cRows[0] > lastWasteWeightRow or cRows[1] < firstWasteWeightRow:
					borderC = c
					if cRows[0] > lastWasteWeightRow: cRows[0] = firstWasteWeightRow
					else: cRows[1] = lastWasteWeightRow #new
					break
		else: workingRows[borderC] = [firstWasteWeightRow, lastWasteWeightRow] #new
		if borderC is None:
			print("\nWARNING: no carrier available for waste border, so can't do it. 'addBorder' is now False. :(")
			addBorder = False #if still no carrier available, don't add border

	global borderStartLeft
	borderStartLeft = True

	# leftMostBorderN = None #TODO: maybe make this 0?
	# rightMostBorderN = None
	leftMostBorderN = 0 #temp #new #check
	rightMostBorderN = maxNeedle #new #check

	# if carrierCount >= 2: #remove #? #v
	# 	if drawC != '2':
	# 		otherCs.append('2') #new
	# 		takeOutAtEnd.append('2') #new #check
	# 	for c in range(3, carrierCount+1):
	# 		otherCs.append(f'{c}')
	# 		takeOutAtEnd.append(f'{c}') #new #check #*#*#* #remove #? #^

	plaitBeforeBorder = None #for now
	prevBorderInfo = {}
	# if len(plaitStPats) > len(availableCarriers) and borderC is not None:
	if len(plaitStPatsRows) > len(availableCarriers) and borderC is not None:
		if not addBorder:
			availableCarriers.append(borderC)
			borderC = None
			if borderC in rightCarriers: rightCarriers.remove(borderC)
		else:
			plaitsBeforeBorder = list(filter(lambda st: st[0] < workingRows[borderC][0], plaitStPatsRows)) #new#new #v
			if len(plaitsBeforeBorder):
				if borderC > mainC: beforeBorderBed = 'b'
				else: beforeBorderBed = 'f'
				plaitBeforeBorder = next((st for st in plaitsBeforeBorder if st[-1] == beforeBorderBed), plaitsBeforeBorder[0])
				print('plaitBeforeBorder:', plaitBeforeBorder) #remove #debug
				# if any(st[-1] == 'f' for st in palitsBeforeBorder): plaitBeforeBorder = next((st for st in enumerate(plaitStPatsRows) if st[0] < workingRows[borderC][0]), None)
				# else: plaitBeforeBorder #^
				
			# plaitBeforeBorder = next((st for st in enumerate(plaitStPatsRows) if st[0] < workingRows[borderC][0]), None) #TODO: assign this to front or back, depending on if borderC is high or low number #remove #?
			if plaitBeforeBorder is not None:
				print(f'\nadding borderC ({borderC}) back into availableCarriers so it can be used in some plaiting that happens before the border.')
				# availableCarriers.insert(0, borderC) #insert at beginning so it won't be accessed with pop #remove #? #new#new
				prevBorderInfo['firstNeedles'] = firstNeedles[borderC].copy()
				prevBorderInfo['workingRows'] = workingRows[borderC].copy()
				if borderC in rightCarriers:
					prevBorderInfo['side'] = 'r'
					rightCarriers.remove(borderC)
				else: prevBorderInfo['side'] = 'l'

	if len(plaitStPatsRows): #new #check #v
		plaitCsF = []
		plaitCsB = []
		# if len(availableCarriers): #remove #?
		if len(availableCarriers) or plaitBeforeBorder is not None: #new#new
			# check to make sure the plaiting isn't happening elsewhere
			for st in plaitStPatsRows:
				stRow1, stIdx, stBed = st
				# if len(availableCarriers): #remove #? #v
				#	if st == plaitBeforeBorder: plaitC = availableCarriers.pop(0)
				#	else: plaitC = availableCarriers.pop() #remove #^
				if len(availableCarriers) or plaitBeforeBorder is not None: #new#new #v
					if st == plaitBeforeBorder:
						plaitC = borderC
						plaitBeforeBorder = None
					else:
						if stBed == 'f': plaitC = availableCarriers.pop()
						else: plaitC = availableCarriers.pop(0) #^
					plaitInfo['assigned'] += 1
					plaitInfo['carriers'].append(plaitC) #new
					if plaitC not in otherCs and plaitC != drawC: otherCs.append(plaitC) #new#new
					if plaitC not in takeOutAtEnd: takeOutAtEnd.append(plaitC)

					if stBed == 'f':
						plaitCsF.append(plaitC) #new
						stitchPatDetailsF[stIdx].info['plaitC'] = plaitC
						plaitInfo['lastRows'][plaitC] = len(stitchPatDataF)-1 - next((i for i, data in enumerate(reversed(stitchPatDataF)) if stIdx in data.keys()), 0) #new #check

						# plaitInfo['lastRows'][len(stitchPatDataF)-1 - next((i for i, data in enumerate(reversed(stitchPatDataF)) if stIdx in data.keys()), 0)] = plaitC #new #check
						if stRow1 is not None:
							stIdxRow1 = stitchPatDataF[stRow1]
							stIdxLeftN = stIdxRow1[stIdx][0]
							stIdxRightN = stIdxRow1[stIdx][-1]

							''' #TODO: add this #v and make it work to separate plaiting for stitch patterns into multiple sections when shortrowing
							sectCt = 1
							for stR in range(stRow1, plaitInfo['lastRows'][plaitC]+1):
								if len(pieceMap[stR]) > 1:
									overlapSections = list(filter((lambda sect: (stIdxLeftN <= convertGauge(rightN=sect[-1]) and stIdxRightN >= convertGauge(leftN=sect[0]))), pieceMap[stR].values()))
									if len(overlapSections) > sectCt:
										stitchPatDetailsF[stIdx].info['plaitC'] = plaitC
										if len(availableCarriers):

										sectCt = len(overlapSections)

									print(overlapSections, len(overlapSections)) #remove #debug
							'''

							firstNeedles[plaitC] = [stIdxLeftN, stIdxRightN] #new #check #here#*

							stPieceMapRow = pieceMap[stRow1]
							for sect in stPieceMapRow: #here#*
								sectLeftN, sectRightN = convertGauge(leftN=stPieceMapRow[sect][0], rightN=stPieceMapRow[sect][-1])
								if stIdxLeftN <= sectRightN and stIdxRightN >= sectLeftN: break #pattern overlaps
							
							foundIt = False
							for stRow in range(plaitInfo['lastRows'][plaitC], 0, -1):
								if foundIt: break
								for sect in pieceMap[stRow]:
									sectRowLeftN, sectRowRightN = convertGauge(leftN=pieceMap[stRow][sect][0], rightN=pieceMap[stRow][sect][-1])
									# sectRowLeftN, sectRowRightN = convertGauge(leftN=stPieceMapRow[sect][0], rightN=stPieceMapRow[sect][-1])
									if stIdxLeftN <= sectRowRightN and stIdxRightN >= sectRowLeftN:
										plaitInfo['lastRows'][plaitC] = stRow #new
										foundIt = True #pattern overlaps
										break
							
							workingRows[plaitC] = [stRow1, plaitInfo['lastRows'][plaitC]] #new #check

							# if abs(stIdxRightN-castonRightN) < abs(stIdxLeftN-castonLeftN): #go back! #?
							# if ((plaitC == '6' or plaitC == '3') and abs(stIdxRightN-castonRightN) < abs(stIdxLeftN-castonLeftN)) or abs(stIdxRightN-sectRightN) < abs(stIdxLeftN-sectLeftN): #remove #debug
							if abs(stIdxRightN-sectRightN) < abs(stIdxLeftN-sectLeftN): #new #check
								stitchPatDetailsF[stIdx].info['plaitCside'] = 'r'
								rightCarriers.append(plaitC)
							else: stitchPatDetailsF[stIdx].info['plaitCside'] = 'l'
						else: stitchPatDetailsF[stIdx].info['plaitCside'] = 'l'
					else:
						plaitCsB.append(plaitC) #new
						stitchPatDetailsB[stIdx].info['plaitC'] = plaitC
						plaitInfo['lastRows'][plaitC] = len(stitchPatDataB)-1 - next((i for i, data in enumerate(reversed(stitchPatDataB)) if stIdx in data.keys()), 0) #new #check
						# plaitInfo['lastRows'][len(stitchPatDataB)-1 - next((i for i, data in enumerate(reversed(stitchPatDataB)) if stIdx in data.keys()), 0)] = plaitC #new #check
						if stRow1 is not None:
							stIdxRow1 = stitchPatDataB[stRow1]
							stIdxLeftN = stIdxRow1[stIdx][0]
							stIdxRightN = stIdxRow1[stIdx][-1]
							firstNeedles[plaitC] = [stIdxLeftN, stIdxRightN] #new #check

							stPieceMapRow = pieceMap[stRow1] #TODO: make is stRow1 is not None
							for sect in stPieceMapRow: #here#*
								sectLeftN, sectRightN = convertGauge(leftN=stPieceMapRow[sect][0], rightN=stPieceMapRow[sect][-1])
								if stIdxLeftN <= sectRightN and stIdxRightN >= sectLeftN: break #pattern overlaps
							
							foundIt = False
							for stRow in range(plaitInfo['lastRows'][plaitC], 0, -1):
								if foundIt: break
								for sect in pieceMap[stRow]:
									sectRowLeftN, sectRowRightN = convertGauge(leftN=pieceMap[stRow][sect][0], rightN=pieceMap[stRow][sect][-1])
									# sectRowLeftN, sectRowRightN = convertGauge(leftN=stPieceMapRow[sect][0], rightN=stPieceMapRow[sect][-1])
									if stIdxLeftN <= sectRowRightN and stIdxRightN >= sectRowLeftN:
										plaitInfo['lastRows'][plaitC] = stRow #new
										foundIt = True #pattern overlaps
										break

							workingRows[plaitC] = [stRow1, plaitInfo['lastRows'][plaitC]] #new #check

							# if abs(stIdxLeftN-castonLeftN) < abs(stIdxRightN-castonRightN): #go back! #?
							# if ((plaitC == '6' or plaitC == '3') and abs(stIdxLeftN-castonLeftN) < abs(stIdxRightN-castonRightN)) or abs(stIdxLeftN-sectLeftN) < abs(stIdxRightN-sectRightN): #remove #debug
							if abs(stIdxLeftN-sectLeftN) < abs(stIdxRightN-sectRightN): #new #check
								stitchPatDetailsB[stIdx].info['plaitCside'] = 'l'
							else:
								stitchPatDetailsB[stIdx].info['plaitCside'] = 'r'
								rightCarriers.append(plaitC)
						else:
							stitchPatDetailsF[stIdx].info['plaitCside'] = 'r'
							rightCarriers.append(plaitC)
				else:
					print('need another carrier!') #remove #debug
					# overlapC = None
					# overlapSide = None
					# if stBed == 'b':
					# 	lastRow = len(stitchPatDataB)-1 - next((i for i, data in enumerate(reversed(stitchPatDataB)) if stIdx in data.keys()), 0) #new #check
					# 	plaitList = plaitCsF
					# 	otherPatDet = stitchPatDetailsF
					# 	otherPatData = stitchPatDataF
					# 	patDet = stitchPatDetailsB
					# 	patData = stitchPatDataB
					# else:
					# 	lastRow = len(stitchPatDataF)-1 - next((i for i, data in enumerate(reversed(stitchPatDataF)) if stIdx in data.keys()), 0) #new #check
					# 	plaitList = plaitCsB
					# 	otherPatDet = stitchPatDetailsB
					# 	otherPatData = stitchPatDataB
					# 	patDet = stitchPatDetailsF
					# 	patData = stitchPatDataF
					
					# for carr, cR in workingRows.items():
					# 	if overlapC is not None: break
					# 	if carr in plaitList and cR[0] <= lastRow and cR[1] >= stRow1: #overlaps
					# 		sI = next((sK for sK, sD in enumerate(otherPatDet) if sD.info['plaitC'] == carr), None) #TODO: do something if None

					# 		print(lastRow, cR[1]) #remove #debug
					# 		overlapSect = None
					# 		for sR in range(stRow1, lastRow+1):
					# 			if stIdx in patData[sR]:
					# 				stIdxLeftN = patData[sR][stIdx][0] #sI # stitchPatDataB[stRow1]
					# 				stIdxRightN = patData[sR][stIdx][-1]
					# 				otherStIdxLeftN = otherPatData[sR][sI][0]
					# 				otherStIdxRightN = otherPatData[sR][sI][-1]
					# 				if stIdxLeftN == otherStIdxLeftN and stIdxRightN == otherStIdxRightN:
					# 					sRkeys = list(pieceMap[sR].keys())

					# 					if otherPatDet[sI].info['plaitCside'] == 'l': #concerned about the left edge needle in the piece
					# 						overlapSide = 'l'
					# 						# if any(convertGauge(leftN=sect[0]) == stIdxLeftN for sect in pieceMap[sR].values()): overlapC = carr
					# 						# else:
					# 						# 	overlapC = None
					# 						# 	break
					# 						firstSect = sRkeys[0]
					# 						for pC in sRkeys:
					# 							if stIdxLeftN <= convertGauge(leftN=pieceMap[sR][pC][0]) and (pC == firstSect or stIdxLeftN > convertGauge(rightN=pieceMap[sR][sRkeys[sRkeys.index(pC)-1]][-1])): #pattern goes up to the left edge of the section (or goes past it, meaning the excess would just be cut off), and either it's the first section (so no sections to the left of it), or the pattern doesn't overflow into the previous section
					# 								overlapSect = pC
					# 							elif pC == overlapSect:
					# 								overlapSect = None
					# 								break
					# 					else: #concerned about the right edge needle in the piece
					# 						overlapSide = 'r'
					# 						lastSect = sRkeys[-1]

					# 						for pC in sRkeys:
					# 							if stIdxRightN >= convertGauge(rightN=pieceMap[sR][pC][-1]) and (pC == lastSect or stIdxRightN < convertGauge(leftN=pieceMap[sR][sRkeys[sRkeys.index(pC)+1]][0])): #pattern goes up to the right edge of the section (or goes past it, meaning the excess would just be cut off), and either it's the last section (so no sections to the right of it), or the pattern doesn't overflow into the following section
					# 								overlapSect = pC
					# 							elif pC == overlapSect:
					# 								overlapSect = None
					# 								break

					# 					if overlapSect is None: break
					# 					else: overlapC = carr


					# 						# print(sR, convertGauge(rightN=pieceMap[sR]['2'][-1])) #remove #debug
					# 						# if any(convertGauge(rightN=sect[-1]) == stIdxRightN for sect in pieceMap[sR].values()):
					# 						# 	#TODO: 
					# 						# 	overlapC = carr
					# 						# else:
					# 						# 	overlapC = None
					# 						# 	break
					# 				else: continue
										
					# 				# for sect in pieceMap[sR]: #here#*
					# 				# # if stIdxLeftN <= sectRightN and stIdxRightN >= sectLeftN: break #pattern overlaps
					# 				# 	sRleftN, sRrightN = convertGauge(leftN=pieceMap[sR][sect][0], rightN=pieceMap[sR][sect][-1])
					# 				# 	print('\n', carr, overlapC)
					# 				# 	print(sRleftN, sRrightN)
					# 				# 	print(stIdxLeftN, stIdxRightN)
					# 				# 	print(otherStIdxLeftN, otherStIdxRightN)
					# 				# 	if stIdxLeftN <= sRrightN and otherStIdxLeftN <= sRrightN and stIdxRightN >= sRleftN and otherStIdxRightN >= sRleftN: overlapC = carr
					# 				# 	elif overlapC == carr:
					# 				# 		overlapC = None
					# 				# 		break
					# 		# if overlapC is not None: break
					# print("overlapC", overlapC) #remove #debug
					# if overlapC is not None:
					# 	print(f'\nfound a carrier ({overlapC}) that can be used for two plaiting sections on either bed by knitting circularly.')
					# 	patDet[stIdx].info['plaitC'] = overlapC
					# 	patDet[stIdx].info['plaitCside'] = overlapSide
					# 	plaitInfo['assigned'] += 1
					# # if overlapC == None: #remove #v
					# # 	stitchPatDetailsB[stIdx].info['plaitCside'] = 'r'
					# # 	stitchPatDetailsB[stIdx].info['plaitC'] = '6' #remove #^

					# # break #new #^
		if not len(availableCarriers) and plaitInfo['count'] != plaitInfo['assigned']: #new #change
			for st in plaitStPatsRows:
				stRow1, stIdx, stBed = st

				overlapC = None
				overlapSide = None
				if stBed == 'b':
					# lastRow = len(stitchPatDataB)-1 - next((i for i, data in enumerate(reversed(stitchPatDataB)) if stIdx in data.keys()), 0) #new #check
					plaitList = plaitCsF
					otherPatDet = stitchPatDetailsF
					otherPatData = stitchPatDataF
					patDet = stitchPatDetailsB
					patData = stitchPatDataB
				else:
					# lastRow = len(stitchPatDataF)-1 - next((i for i, data in enumerate(reversed(stitchPatDataF)) if stIdx in data.keys()), 0) #new #check
					plaitList = plaitCsB
					otherPatDet = stitchPatDetailsB
					otherPatData = stitchPatDataB
					patDet = stitchPatDetailsF
					patData = stitchPatDataF
				
				lastRow = len(patData)-1 - next((i for i, data in enumerate(reversed(patData)) if stIdx in data.keys()), 0) #new #check

				for carr, cR in workingRows.items():
					if overlapC is not None: break
					# if carr in plaitList and cR[0] <= lastRow and cR[1] >= stRow1: #overlaps
					if carr != patDet[stIdx].info['plaitC'] and carr in plaitList and cR[0] <= lastRow and cR[1] >= stRow1: #overlaps
						# for q in otherPatDet:
						# 	print(q.info)
						sI = next((sK for sK, sD in enumerate(otherPatDet) if 'plaitC' in sD.info and sD.info['plaitC'] == carr), None) #TODO: do something if None

						if sI is None: continue
						overlapSect = None
						for sR in range(stRow1, lastRow+1):
							# if stIdx in patData[sR]:
							if stIdx in patData[sR] and sI in patData[sR]:
								stIdxLeftN = patData[sR][stIdx][0] #sI # stitchPatDataB[stRow1]
								stIdxRightN = patData[sR][stIdx][-1]
								otherStIdxLeftN = otherPatData[sR][sI][0]
								otherStIdxRightN = otherPatData[sR][sI][-1]
								if stIdxLeftN == otherStIdxLeftN and stIdxRightN == otherStIdxRightN:
									sRkeys = list(pieceMap[sR].keys())

									if otherPatDet[sI].info['plaitCside'] == 'l': #concerned about the left edge needle in the piece
										overlapSide = 'l'
										# if any(convertGauge(leftN=sect[0]) == stIdxLeftN for sect in pieceMap[sR].values()): overlapC = carr
										# else:
										# 	overlapC = None
										# 	break
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
									else: overlapC = carr


										# print(sR, convertGauge(rightN=pieceMap[sR]['2'][-1])) #remove #debug
										# if any(convertGauge(rightN=sect[-1]) == stIdxRightN for sect in pieceMap[sR].values()):
										# 	#TODO: 
										# 	overlapC = carr
										# else:
										# 	overlapC = None
										# 	break
								else: continue
									
								# for sect in pieceMap[sR]: #here#*
								# # if stIdxLeftN <= sectRightN and stIdxRightN >= sectLeftN: break #pattern overlaps
								# 	sRleftN, sRrightN = convertGauge(leftN=pieceMap[sR][sect][0], rightN=pieceMap[sR][sect][-1])
								# 	print('\n', carr, overlapC)
								# 	print(sRleftN, sRrightN)
								# 	print(stIdxLeftN, stIdxRightN)
								# 	print(otherStIdxLeftN, otherStIdxRightN)
								# 	if stIdxLeftN <= sRrightN and otherStIdxLeftN <= sRrightN and stIdxRightN >= sRleftN and otherStIdxRightN >= sRleftN: overlapC = carr
								# 	elif overlapC == carr:
								# 		overlapC = None
								# 		break
						# if overlapC is not None: break
				# print("overlapC", overlapC) #remove #debug
				if overlapC is not None:
					print('\n!') #remove #debug
					# print(f"\ndidn't have enough carriers to designate to individual plaiting sections, but found a carrier ({overlapC}) that can be used for two plaiting sections on either bed by knitting circularly with it.")
					print(stIdx, patDet[stIdx].info['plaitC'])
					if patDet[stIdx].info['plaitC'] is None:
						print(f"\ndidn't have enough carriers to designate to individual plaiting sections, but found a carrier ({overlapC}) that can be used for two plaiting sections on either bed by knitting circularly with it.") #new location
						plaitInfo['assigned'] += 1
					else: # remove it from all of the lists/dicts of carrier data
						prevPlaitC = patDet[stIdx].info['plaitC']
						print(f'\nusing carrier {overlapC} for two plaiting sections on either bed instead of also using carrier {prevPlaitC} to reduce carrier count, since we can. will be knitting circularly will {overlapC} for plaiting.')
						plaitInfo['carriers'].remove(prevPlaitC) #new location
						if prevPlaitC != borderC:
							# plaitInfo['carriers'].remove(prevPlaitC)
							otherCs.remove(prevPlaitC)
							takeOutAtEnd.remove(prevPlaitC)
							if prevPlaitC in rightCarriers: rightCarriers.remove(prevPlaitC)
							del workingRows[prevPlaitC]
							del firstNeedles[prevPlaitC]
							availableCarriers.append(prevPlaitC)
						else: #switch info back to borderC-based info
							firstNeedles[prevPlaitC] = prevBorderInfo['firstNeedles']
							workingRows[prevPlaitC] = prevBorderInfo['workingRows']
							if prevBorderInfo['side'] == 'r' and prevPlaitC not in rightCarriers: rightCarriers.append(prevPlaitC) #add it back into rightCarriers since just based on behavior of borderC now 
						
					patDet[stIdx].info['plaitC'] = overlapC
					patDet[stIdx].info['plaitCside'] = overlapSide

	needAnotherCarrier = False
	print('\nplaiting carriers:', plaitInfo['carriers']) #remove #debug
	if plaitInfo['count'] != plaitInfo['assigned']:
		print(f'before starting the piece, {plaitInfo["count"]-plaitInfo["assigned"]} more carrier(s) needed for plaiting. Hopefully, some carriers will become available once they are out of use.')
		needAnotherCarrier = True

	leftDropWasteC = None
	rightDropWasteC = None

	if addBorder:
		# otherCs.append(borderC)
		if borderC != drawC:
			otherCs.append(borderC) #if not draw thread #new #*#*#*#*#*#*
			takeOutAtEnd.append(borderC)
		# if borderC != '2': otherCs.append(borderC) #new #*#*#*#*#*#*
		# takeOutAtEnd.append(borderC)
		if width + 16 <= 252: borderWidthAdd = 8 #if have enough needles available (based on max width of piece), add 8 stitches to each side of waste border
		else: borderWidthAdd = math.floor((252-width)/4)*2 #otherwise, just do max number of extra needles available, split between two sides; round to even number so doesn't change parity of borders
		
		# wasteWeightsKeys = list(wasteWeights.keys()) #rows
		# firstWasteWeightRow = wasteWeightsKeys[0]
		# lastWasteWeightRow = wasteWeightsKeys[len(wasteWeightsKeys)-1]

		# firstRows[borderC] = firstWasteWeightRow #new
		# lastRows[borderC] = lastWasteWeightRow #new

		if not addBindoff: # have carrier on either side 
			# if len(availableCarriers):
			if len(availableCarriers) and len(carrierOrder) > 1: #if available carriers and more than one section
				otherDropC = availableCarriers.pop()
				if otherDropC != drawC: otherCs.append(otherDropC) #new #check #if not draw thread
				# if otherDropC != '2': otherCs.append(otherDropC) #if not draw thread
				# otherCs.append(otherDropC)
				takeOutAtEnd.append(otherDropC)
			else: otherDropC = None

			if 'left' in wasteWeights[lastWasteWeightRow]:
				if 'right' in wasteWeights[lastWasteWeightRow]: #both
					# leftIncCarrier = next(c for c in pieceMap[lastWasteWeightRow] if pieceMap[lastWasteWeightRow][c][0] == wasteWeights[lastWasteWeightRow]['left'][0])
					leftIncCarrier = next(c for c in pieceMap[lastWasteWeightRow] if convertGauge(leftN=pieceMap[lastWasteWeightRow][c][0]) == wasteWeights[lastWasteWeightRow]['left'][0])

					rightIncCarrier = next(c for c in pieceMap[lastWasteWeightRow] if convertGauge(rightN=pieceMap[lastWasteWeightRow][c][-1]) == wasteWeights[lastWasteWeightRow]['right'][1])
					# rightIncCarrier = next(c for c in pieceMap[lastWasteWeightRow] if pieceMap[lastWasteWeightRow][c][len(pieceMap[lastWasteWeightRow][c])-1] == wasteWeights[lastWasteWeightRow]['right'][1])

					lastWastePieceMapKeys = list(pieceMap[lastWasteWeightRow].keys())
					if lastWastePieceMapKeys.index(rightIncCarrier) > lastWastePieceMapKeys.index(leftIncCarrier): #right happens last
						if borderC not in plaitInfo['carriers']: rightDropWasteC = borderC #new #check #*#*#*
						# rightDropWasteC = borderC #remove #*#*#*
						leftDropWasteC = otherDropC #might be None
					elif lastWastePieceMapKeys.index(leftIncCarrier) > lastWastePieceMapKeys.index(rightIncCarrier): #left inc happens last (so waste weight ends on left side) 
						if borderC not in plaitInfo['carriers']: leftDropWasteC = borderC #new #check #*#*#*
						# leftDropWasteC = borderC #remove #*#*#*
						rightDropWasteC = otherDropC #might be None
					else: #they are equal, so need to find out which one happens last based on dir1 of the carrier
						if leftIncCarrier in rightCarriers: #ends on right, so right happens last
							if borderC not in plaitInfo['carriers']: rightDropWasteC = borderC #new #check #*#*#*
							# rightDropWasteC = borderC
							leftDropWasteC = otherDropC #might be None
						else: #ends on left, so left happens last
							if borderC not in plaitInfo['carriers']: leftDropWasteC = borderC #new #check #*#*#*
							# leftDropWasteC = borderC
							rightDropWasteC = otherDropC #might be None
				else: #just left (meaning last inc is on left side)
					if borderC not in plaitInfo['carriers']: leftDropWasteC = borderC #new #check #*#*#*
					# leftDropWasteC = borderC
					rightDropWasteC = otherDropC #might be None
			else: #just right (meaning last inc is on right side)
				if borderC not in plaitInfo['carriers']: rightDropWasteC = borderC #new #check #*#*#*
				# rightDropWasteC = borderC
				leftDropWasteC = otherDropC #might be None

			if rightDropWasteC is not None and rightDropWasteC not in rightCarriers: rightCarriers.append(rightDropWasteC)
		else:
			otherDropC = None
		# -------------------------------------

		leftBorderNs = list(filter(lambda w: 'left' in w, wasteWeights.values()))
		rightBorderNs = list(filter(lambda w: 'right' in w, wasteWeights.values()))
		

		# global prevBorderLeftN #new #check #go back! #? #v
		# global prevBorderRightN
		# if len(leftBorderNs):
		# 	prevBorderLeftN = leftBorderNs[0]['left'][0] #new #check
		# 	leftMostBorderN = min(leftBorderNs, key=lambda ns: ns['left'][0])['left'][0]
		# else: leftMostBorderN = 0 #new #check
		# if len(rightBorderNs):
		# 	prevBorderRightN = rightBorderNs[0]['right'][1] #new #check
		# 	rightMostBorderN = max(rightBorderNs, key=lambda ns: ns['right'][1])['right'][1]
		# else: rightMostBorderN = maxNeedle #new #check #go back! #? #^

		firstNeedles[borderC] = [leftMostBorderN-borderWidthAdd, rightMostBorderN+borderWidthAdd] #add this so know to miss other carriers out of way here
		if otherDropC is not None: firstNeedles[otherDropC] = firstNeedles[borderC].copy() #to be altered

		if borderC in rightCarriers: borderStartLeft = False
	elif not addBorder and not addBindoff:
		if borderC is not None: #meaning there were leftover carriers
			# if borderC == '2': leftDropWasteC = borderC #draw thread
			if borderC == drawC:
				if borderC not in plaitInfo['carriers']: leftDropWasteC = borderC #new #check #*#*#*
				# leftDropWasteC = borderC #draw thread
			elif len(availableCarriers):
				leftDropWasteC = availableCarriers.pop()
			
			if len(carrierOrder) > 1:
				if borderC != drawC:
					if borderC not in plaitInfo['carriers']: rightDropWasteC = borderC #new #check #*#*#*
					# rightDropWasteC = borderC
				elif len(availableCarriers): rightDropWasteC = availableCarriers.pop()

			if leftDropWasteC is not None:
				# if leftDropWasteC != '2': otherCs.append(leftDropWasteC)
				if leftDropWasteC != drawC: otherCs.append(leftDropWasteC)
				takeOutAtEnd.append(leftDropWasteC)
			if rightDropWasteC is not None:
				if rightDropWasteC not in rightCarriers: rightCarriers.append(rightDropWasteC)
				if rightDropWasteC != drawC: otherCs.append(rightDropWasteC)
				# otherCs.append(rightDropWasteC)
				takeOutAtEnd.append(rightDropWasteC)

	print('\nCarriers used in main piece:', carrierOrder)
	print('\nborderC:', borderC, 'addBorder:', addBorder)
	print('\nleftDropWasteC:', leftDropWasteC, 'rightDropWasteC:', rightDropWasteC) #remove #debug
	if addBorder:
		print('\nfirstWasteWeightRow:', firstWasteWeightRow) #remove #debug
		print('\nwasteBoundaryExpansions:', wasteBoundaryExpansions) #remove #debug #TODO: adjust since no longer includes carrier as key
		print('\nwasteWeights:', wasteWeights) #remove #debug #TODO: adjust since no longer includes carrier as key

	print('\navailableCarriers leftover:', availableCarriers) #remove #debug 

	takenOutCarriers = [] #new
	reusableCarriers = availableCarriers.copy() #new #TODO: if reuse a carrier, check to send which needle it last ended by, and tuck over (and then drop) to get it on correct side if too far away

	#5. Add waste section and cast-on

	
	# # alter first needles if they are within another carrier's knitting

	
	firstNeedlesBefore = firstNeedles.copy()

	for c in reversed(list(firstNeedles.keys())):
		if len(firstNeedlesBefore) == 1: break

		firstNeedlesBefore.popitem()
		leftMostBeforeN = min(firstNeedlesBefore.values(), key=lambda firstNs: firstNs[0])[0]
		rightMostBeforeN = max(firstNeedlesBefore.values(), key=lambda firstNs: firstNs[1])[1]

		if firstNeedles[c][0] > leftMostBeforeN: firstNeedles[c][0] = leftMostBeforeN
		if firstNeedles[c][1] < rightMostBeforeN: firstNeedles[c][1] = rightMostBeforeN

	if ((castonRightN/gauge)-(castonLeftN/gauge) < 16): catchMaxNeedles = True #TODO: have it be is it is < 4 when divided by carriers length (but >= 16 otherwise), have it treat it as len(carriers)/2 #TODO: try changing this #come back! #*#*#*#*#*#* #here
	else: catchMaxNeedles = False

	wasteRightCarriers = rightCarriers.copy()

	# if closedCaston: wasteRightCarriers.append('1') #have wasteSection func put main carrier (aka caston carrier) on right, side doing closedTubeCaston, so it will actually end on left (since closedTubeCaston is only one pass) #remove #? #v

	# if '1' not in excludeCarriers: wasteC = '1'
	# else: wasteC = carrierOrder[-1] #whichever carrier is used first (carrierOrder should be backwards in terms of time) #remove #? #^
	if closedCaston: wasteRightCarriers.append(mainC) #have wasteSection func put main carrier (aka caston carrier) on right, side doing closedTubeCaston, so it will actually end on left (since closedTubeCaston is only one pass)

	# if gauge == 1: closedCaston = False
	# else:
	# 	wasteRightCarriers.append('1') #have wasteSection func put main carrier (aka caston carrier) on right, side doing closedTubeCaston, so it will actually end on left (since closedTubeCaston is only one pass)
	# 	closedCaston = True

	if drawC not in firstNeedles: firstNeedles[drawC] = [0, maxNeedle]
	if (width+4) < 252:
		firstNeedles[drawC][0] -= 2 #get it a bit more out of the way
		firstNeedles[drawC][1] += 2
	
	# print('\nrightCarriers:', rightCarriers, wasteRightCarriers) #remove #debug

	print('\ndrawC:', drawC, 'wasteC:', wasteC, 'otherCs:', otherCs) #remove #debug

	print('\nfirstNeedles:', firstNeedles) #remove #debug

	wasteSection(k=k, leftN=castonLeftN, rightN=castonRightN, closedCaston=closedCaston, wasteC=wasteC, drawC=drawC, otherCs=otherCs, gauge=gauge, endOnRight=wasteRightCarriers, firstNeedles=firstNeedles, catchMaxNeedles=catchMaxNeedles)

	# if closedCaston: closedTubeCaston(k, castonRightN, castonLeftN, '1', gauge) #remove #? #v
	# else: openTubeCaston(k, castonLeftN, castonRightN, '1', gauge) #remove #? #^
	if closedCaston: closedTubeCaston(k, castonRightN, castonLeftN, mainC, gauge) #new#new #v
	else: openTubeCaston(k, castonLeftN, castonRightN, mainC, gauge) #^

	#5. Convert generated data to knitout; also generate visualization of pieceMap data so can see what it would actually look like (0 == whitespace, other numbers == stitch knit with respective carrier number)
	visualization = [] #list for storing visualization

	#TODO: check what max short row count is that the kniterate can handle

	# extraCarriersIn = [] #remove

	sectionIdx = 0
	shortrowCount = 0
	cycleEnd = maxShortrowCount #new #*#*#*
	endPoints = []

	global toDrop #?
	toDrop = []

	global sanityDrop
	sanityDrop = []

	global lastDropR
	lastDropR = len(pieceMap)-1

	#--- MAIN PART OF FUNCTION ---
	r = 0
	while r < len(pieceMap):
		sectionCount = len(pieceMap[r]) #number of sections in this row
		mapKeys = list(pieceMap[r].keys()) #carriers used in this row

		if (r+1) < len(pieceMap)-1 and (sectionCount < len(pieceMap[r+1]) or sectionCount > len(pieceMap[r+1])): sectionCountChangeNext = True #if new section coming up next, or section is ending & no longer exists next
		else: sectionCountChangeNext = False

		if sectionIdx == 0:
			visualization.append([])
			n0 = 0 #for whitespace (just for visualization, not knitout)
			# finishedCarriers = list(filter(lambda carr: workingRows[carr][1] == r+1, list(workingRows.keys()))) #new
			# reusableCarriers.extend(finishedCarriers) #new
		else: n0 = endPoints.pop(0)

		carrier = mapKeys[sectionIdx]
		needles = pieceMap[r][mapKeys[sectionIdx]]

		k.comment(f'row: {r} (section {sectionIdx+1}/{sectionCount})')

		dir1 = '+' #left side
		if carrier in rightCarriers: dir1 = '-' #right side

		prevLeftN = None
		prevRightN = None
		xferL = 0
		xferR = 0

		placementLeft = False

		twistedStitches = [] #might use later on if increasing

		n1, n2 = convertGauge(gauge, needles[0], needles[len(needles) - 1])

		#analyze stitchPatData (if applicable)
		def findPatterns(data):
			patterns = {}
			if data is not None and len(data[r]):
				for pat, patNs in data[r].items():
					patLeftN, patRightN = patNs[0], patNs[-1] #new 
					# if patLeftN <= n2 and patRightN >= n1:
					# if (patLeftN >= n1 and patLeftN <= n2) or (patRightN <= n2 and patRightN >= n1): #pattern overlaps
					if patLeftN <= n2 and patRightN >= n1: #pattern overlaps
						overlap = []
						if patLeftN >= n1: overlap.append(patLeftN)
						else: overlap.append(n1)

						if patRightN <= n2: overlap.append(patRightN)
						else: overlap.append(n2)
						patterns[pat] = overlap
			return patterns
		
		patternsF = findPatterns(stitchPatDataF)
		patternsB = findPatterns(stitchPatDataB)

		placementPass = []

		sectionFinished = False
		if r == len(pieceMap)-1 or (r < len(pieceMap)-1 and carrier not in pieceMap[r+1]): sectionFinished = True #TODO: alter this if 

		finishOff = True
		if sectionFinished and r < len(pieceMap)-1:
			# if (n1 >= rowsEdgeNeedles[r][0] or n2 <= rowsEdgeNeedles[r][1]):
			nextRowNeedles = list(pieceMap[r+1].values())[0]
			if (n1/gauge) in nextRowNeedles or (n2/gauge) in nextRowNeedles:
				finishOff = False #new #*#*#*
				print(f'\nNOTE: not finishing off carrier {carrier}, even though its section is finished, because some (or all) of the loops will be taken over by another carrier.')

		if r > 0 and carrier not in pieceMap[r-1]: #means this is a new section #might need to cast some needles on
			if sectionIdx != 0 and sectionIdx != len(mapKeys)-1: #means that it is a new shortrow section that is not on the edge, so need to place carrier in correct spot
				if dir1 == '+': k.miss('+', f'f{n1-1}', carrier)
				else: k.miss('-', f'f{n2+1}', carrier)
				k.pause(f'cut C{carrier}')


			#TODO: maybe remove this, it might never be needed (doesn't look like there is need for caston) #actually, go for if need to increase
			prevRowMapKeys = list(pieceMap[r-1].keys())
			prevRowNeedles = range(convertGauge(gauge=gauge, leftN=pieceMap[r-1][prevRowMapKeys[0]][0]), convertGauge(gauge=gauge, rightN=pieceMap[r-1][prevRowMapKeys[len(prevRowMapKeys)-1]][len(pieceMap[r-1][prevRowMapKeys[len(prevRowMapKeys)-1]])-1])) #new
			# prevRowNeedles = range(pieceMap[r-1][prevRowMapKeys[0]][0]*gauge, (pieceMap[r-1][prevRowMapKeys[len(prevRowMapKeys)-1]][len(pieceMap[r-1][prevRowMapKeys[len(prevRowMapKeys)-1]])-1]*gauge)+1)

			newNeedles = []
			needleRange = range(n1, n2+1)
			if dir1 == '-': needleRange = range(n2, n1-1, -1)
			for n in needleRange:
				if n not in prevRowNeedles: newNeedles.append(n)
			if len(newNeedles):
				k.rack(0.25)
				for n in range(0, len(newNeedles)):
					if f'f{newNeedles[n]}' not in emptyNeedles: k.knit(dir1, f'f{n}', carrier)
					if f'b{newNeedles[n]}' not in emptyNeedles: k.knit(dir1, f'b{n}', carrier)
				k.rack(0)

				dir2 = '-'
				needleRange = range(n2, n1-1, -1)
				if dir1 == '-':
					dir2 = '+'
					needleRange = range(n1, n2+1)

				k.comment('back pass to get carrier on correct side')
				for n in range(len(newNeedles)-1, -1, -1): #back pass to get carrier on correct side #check
					if f'b{newNeedles[n]}' not in emptyNeedles: k.knit(dir2, f'b{n}', carrier)

		if r < len(pieceMap)-1 and len(pieceMap[r+1]) > sectionCount and carrier in pieceMap[r+1]:
			futureMapKeys = list(pieceMap[r+1].keys())
			if sectionIdx == 0 and futureMapKeys.index(carrier) != 0: #means new left shortrow section coming
				futureNewSectionNeedles = pieceMap[r+1][futureMapKeys[0]]
				futureNewSectionRightN = convertGauge(gauge, rightN=futureNewSectionNeedles[len(futureNewSectionNeedles)-1])
				placementPass = [n1, futureNewSectionRightN] #knit up until futureLeftN on back bed #TODO: make sure it misses an extra needle here so not in the way #TODO: maybe plan ahead for future part to make up for extra pass on back bed in left shortrow section? #?

		if r > 0 and carrier in pieceMap[r-1]:
			prevNeedles = pieceMap[r-1][carrier]
			prevLeftN, prevRightN = convertGauge(gauge, prevNeedles[0], prevNeedles[len(prevNeedles)-1])

			if sectionCount > len(pieceMap[r-1]): #means new section here
				prevMapKeys = list(pieceMap[r-1].keys())

				if sectionIdx > 0 and mapKeys[sectionIdx-1] not in prevMapKeys: #means new left section was added before this section
					prevSectionEnd = convertGauge(gauge, rightN=pieceMap[r][mapKeys[sectionIdx-1]][len(pieceMap[r][mapKeys[sectionIdx-1]])-1])
					if prevLeftN < prevSectionEnd: prevLeftN = prevSectionEnd+1
				if sectionIdx < len(mapKeys)-1 and mapKeys[sectionIdx+1] not in prevMapKeys: #means new right section will be added after this section
					nextSectionStart = convertGauge(gauge, leftN=pieceMap[r][mapKeys[sectionIdx+1]][0])
					if prevRightN > nextSectionStart: prevRightN = nextSectionStart-1

			xferL = prevLeftN - n1 #dec/inc on left side (neg if dec)
			xferR = n2 - prevRightN #dec/inc on right side (neg if dec)

			# placementLeft = False
			if sectionCount < len(pieceMap[r-1]) and (xferL != 0 or xferR != 0): #a section was previously finished and we might need to change some things #new #check
				# mapKeys = list(pieceMap[r].keys()) #carriers used in this row
				prevRowMapKeys = list(pieceMap[r-1].keys())

				for pC in prevRowMapKeys:
					if pC == carrier: continue
					elif pC not in mapKeys: #the section that was finished
						finishedSectNs = pieceMap[r-1][pC]
						finishedLeftN, finishedRightN = convertGauge(gauge, finishedSectNs[0], finishedSectNs[len(finishedSectNs) - 1])
						if n1 <= finishedRightN and n2 >= finishedLeftN:
							xferL = finishedLeftN-n1
							placementLeft = True
							print('\nNOTE: adjusting for merged tube.')
						#TODO: check if need to add if n2 >= finishedLeftN

		# def insertBorder(justTuck=False, shift=0, switch=False):
		def insertBorder(justTuck=False, shiftTuckNs=[], switch=False):
			k.comment(f'insert border for row {r} to secure carrier {carrier}') #remove #?
			offLimits = []
			additionalDrop = []
			tuckOver = [[], []]

			borderLeftN = n1-1
			# if xferL > 0: borderLeftN += xferL #increase
			if xferL > 0 or xferL < 0: borderLeftN += xferL # if > 0, increase (xferL will be positive, so shifts border to the right so can increase over the border loops for security); if < 0, dec (xferL will be negative so shifts border over to left so don't knit over loops that are about to be decreased [but haven't been decreased just yet, shaping will happen after inserting the border])
			borderRightN = n2+1
			# if xferR > 0: borderRightN -= xferR
			if xferR > 0 or xferR < 0: borderRightN -= xferR
	
			nextIncRow = None
			nextBorderLeft = None
			nextBorderRight = None

			global prevBorderLeftN
			global prevBorderRightN
			# global lastWasteWeightRow #remove #?

			wKeys = list(wasteWeights.keys())
			if (r == lastWasteWeightRow): nextIncRow = r+1 #just knit one more row if about to drop waste border
			else: nextIncRow = wKeys[wKeys.index(r)+1]

			borderWidthL = (borderLeftN-leftMostBorderN)+borderWidthAdd
			borderWidthR = (rightMostBorderN-borderRightN)+borderWidthAdd

			takenNeedles = []
			currentTakenNeedles = {}
			futureTakenNeedles = {}
			
			# otherSectionsCurrentNeedles = pieceMap[r].copy()
			otherSectionsCurrentNeedles = pieceMap[cycleEnd].copy() #new
			otherSectionsFutureNeedles = pieceMap[nextIncRow].copy()
			
			otherSectionsCurrentNeedles[carrier] = pieceMap[r][carrier].copy() #change current needles for current carrier to be what happens in this row #TODO: try out r-1 and see if it's better

			for key, val in otherSectionsCurrentNeedles.items():
				if key not in mapKeys: continue #new
				currentTakenNeedles[key] = [convertGauge(gauge=gauge, leftN=val[0]), convertGauge(gauge=gauge, rightN=val[-1])]
				# if mapKeys.index(key) < sectionIdx: currentTakenNeedles[key] = [convertGauge(gauge=gauge, leftN=otherSectionsCompleted[key][0]), convertGauge(gauge=gauge, rightN=otherSectionsCompleted[key][-1])+1] #already happened
				# else: currentTakenNeedles[key] = [convertGauge(gauge=gauge, leftN=val[0]), convertGauge(gauge=gauge, rightN=val[-1])+1]

			for key, val in otherSectionsFutureNeedles.items():
				futureTakenNeedles[key] = [convertGauge(gauge=gauge, leftN=val[0]), convertGauge(gauge=gauge, rightN=val[-1])]
				if key in mapKeys and mapKeys.index(key) > sectionIdx and cycleEnd+shortrowCount < nextIncRow: futureTakenNeedles[key] = [convertGauge(gauge=gauge, leftN=pieceMap[cycleEnd+shortrowCount][key][0]), convertGauge(gauge=gauge, rightN=pieceMap[cycleEnd+shortrowCount][key][-1])] #new #temporary fix for cactus-weird-test-3 ;insert border for row 141 carrier 3

			dropForDec = [] #new #*#*#*

			for key, val in currentTakenNeedles.items():
				if key in futureTakenNeedles: # check if decrease coming up, if so, make sure don't tuck on the needles that might be involved in the dec
					leftShift = futureTakenNeedles[key][0]-val[0]
					rightShift = val[1]-futureTakenNeedles[key][1]
					if leftShift > 0: #meaning there is a dec
						rightDecBoundary = futureTakenNeedles[key][0]+1
						if gauge == 2 and leftShift == 4: rightDecBoundary += 1

						for n in range(val[0], rightDecBoundary):
							if n % gauge == 0: dropForDec.append(f'b{n}')
							if (gauge == 1 or n % gauge != 0):  dropForDec.append(f'f{n}')

					if rightShift > 0: #meaning there is a dec
						leftDecBoundary = futureTakenNeedles[key][1]
						if gauge == 2 and rightShift == 4: #dec 2 loops
							leftDecBoundary -= 1

						for n in range(leftDecBoundary, val[1]+1):
							if n % gauge == 0: dropForDec.append(f'b{n}')
							if (gauge == 1 or n % gauge != 0):  dropForDec.append(f'f{n}')
			
				if key != carrier: takenNeedles.append(range(val[0], val[1]+1)) #new #*#*#*

			tuckB = 0 #for tucking every other
			tuckF = 0
			tuckOverNs = []

			# print('\ntakenNeedles:', takenNeedles, 'borderLeftN:', borderLeftN, 'borderRightN:', borderRightN, 'borderWidthL:', borderWidthL, 'borderWidthR:', borderWidthR, 'rightMostBorderN:', rightMostBorderN, borderLeftN-borderWidthL, borderRightN+borderWidthR) #remove #debug
			for takenRange in takenNeedles:
				for n in range(borderLeftN-borderWidthL, borderRightN+borderWidthR+1):
					if n in takenRange:
						if (not len(tuckOverNs) or n-tuckOverNs[-1] > gauge) and (not len(tuckOver[0]) or len(tuckOver[0][-1])):
							tuckOver[0].append(list())
							tuckOver[1].append(list())

						if n % gauge == 0: 
							offLimits.append(f'f{n}')
							if gauge == 2 and f'b{n}' not in offLimits:
								if tuckB % 2 == 0: tuckOver[0][-1].append(f'b{n}')
								else: tuckOver[1][-1].append(f'b{n}')
								tuckOverNs.append(n)
								additionalDrop.append(f'b{n}')
							tuckB += 1
						if n % gauge != 0 or gauge == 1:
							offLimits.append(f'b{n}')
							if gauge == 2 and f'f{n}' not in offLimits:
								if tuckF % 2 == 0: tuckOver[0][-1].append(f'f{n}')
								else: tuckOver[1][-1].append(f'f{n}')
								tuckOverNs.append(n)
								additionalDrop.append(f'f{n}')
							tuckF += 1

			# remove any extra empty lists
			if len(tuckOver[0]) and not len(tuckOver[0][-1]):
				tuckOver[0].pop()
			if len(tuckOver[1]) and not len(tuckOver[1][-1]):
				tuckOver[1].pop()
			
			if (len(tuckOver[0]) and not len(tuckOver[1])): #new #v
				if len(tuckOver[0]) > 1:
					for tO in range(0, len(tuckOver[0]), 2):
						tuckOver[1].append(tuckOver[0].pop(tO))
				else: tuckOver[1] = tuckOver[0].copy()
			elif (len(tuckOver[1]) and not len(tuckOver[0])):
				if len(tuckOver[1]) > 1:
					for tO in range(0, len(tuckOver[1]), 2):
						tuckOver[0].append(tuckOver[1].pop(tO))
				else: tuckOver[0] = tuckOver[1].copy() #new #^

			if (borderStartLeft and not switch) or (switch and not borderStartLeft): #NOTE: border*[0] = leftN, border*[1] = rightN
				borderStartN = borderLeftN
				borderEndN = borderRightN

				if carrier in pieceMap[r+1]:
					nextNeedles = pieceMap[r+1][carrier]
					nextLeftN, nextRightN = convertGauge(gauge, nextNeedles[0], nextNeedles[len(nextNeedles) - 1])

				prevBorderLeftN = borderLeftN #TODO: figure out if need to remove this since probably removing this #^
				prevBorderRightN = borderRightN

				if r < lastWasteWeightRow:
					borderMissN = convertGauge(gauge=gauge, rightN=pieceMap[r][carrier][-1])
				else:
					if maxNeedle > 247: borderMissN = maxNeedle+(251-maxNeedle) #if using most of the bed
					else: borderMissN = maxNeedle+4 #miss past the right-most needle in whole piece (+4 for extra)
			else: #border starts on right (tuck in neg direction)
				borderStartN = borderRightN
				borderEndN = borderLeftN

				prevBorderLeftN = borderLeftN #TODO: figure out if need to remove this since probably removing this #^
				prevBorderRightN = borderRightN

				if r < lastWasteWeightRow:
					borderMissN = convertGauge(gauge=gauge, leftN=pieceMap[r][carrier][0])
				else:
					if maxNeedle > 247: borderMissN = 0 #TODO: maybe add some more calculation to this #?
					else: borderMissN = -4 #miss past the left-most needle in whole piece, which is automatically 0 (-4 for extra)
			
			if justTuck:
				firstTime = False
				dropBorder = False
			else:
				firstTime = (r==firstWasteWeightRow)

				if (sectionIdx < 0 and r > firstWasteWeightRow and (r-wKeys[wKeys.index(r)-1]) > maxShortrowCount): firstTime = True #if big gap btw inc #new #TODO: maybe toggle off if justTuck
				# if (r > firstWasteWeightRow and (r-wKeys[wKeys.index(r)-1]) > maxShortrowCount): firstTime = True #if big gap btw inc

				dropBorder = (r==lastWasteWeightRow)

				if sectionFinished and not finishOff and r == wasteWeightsKeys[len(wasteWeightsKeys)-2]:
					dropBorder = True #new

				if (r < lastWasteWeightRow and (nextIncRow-r) > maxShortrowCount):
					dropBorder = True #if big gap btw inc
					nextIncRow = r+maxShortrowCount

			wasteOffLimits = offLimits.copy()
			
			if justTuck:
				wasteToDrop = wasteBorder(k, borderStartN, borderEndN, nextIncRow-r, c=borderC, widthL=borderWidthL, widthR=borderWidthR, gauge=gauge, offLimits=wasteOffLimits, firstTime=firstTime, lastTime=dropBorder, justTuck=justTuck, tuckNs=shiftTuckNs, missN=borderMissN, tuckOver=tuckOver)
				nextTuckNs = []
			else: wasteToDrop, nextTuckNs = wasteBorder(k, borderStartN, borderEndN, nextIncRow-r, c=borderC, widthL=borderWidthL, widthR=borderWidthR, gauge=gauge, offLimits=wasteOffLimits, firstTime=firstTime, lastTime=dropBorder, justTuck=justTuck, tuckNs=[], missN=borderMissN, tuckOver=tuckOver)
			# wasteToDrop = wasteBorder(k, borderStartN, borderEndN, nextIncRow-r, c=borderC, widthL=borderWidthL, widthR=borderWidthR, gauge=gauge, offLimits=wasteOffLimits, firstTime=firstTime, lastTime=dropBorder, justTuck=justTuck, shift=shift, missN=borderMissN, tuckOver=tuckOver)

			if len(dropForDec) and not (dropBorder or (justTuck and (nextIncRow-r) > maxShortrowCount)): #new
				k.comment(f'drop tucks in way of dec')
				for bn in dropForDec:
					k.drop(bn)

			wasteToDrop.extend(additionalDrop)

			return wasteToDrop, borderMissN, dropBorder, nextTuckNs #new
					
		def leftShaping():
			if xferL:
				if xferL > 0: #increase
					global borderStartLeft
					global toDrop

					carrierOnLeft = borderStartLeft
					droppedTucks = False
					borderMissN = None
					dropBorder = False

					nextTuckNs = []
					if addBorder:
						if dir1 == '+' or xferR < 1: #aka if left inc is happening first or there are no right inc in this row
							for n in toDrop:
								k.drop(n)
							toDrop = []
							droppedTucks = True
							borderToDrop, borderMissN, dropBorder, nextTuckNs = insertBorder()
							toDrop.extend(borderToDrop)
							borderStartLeft = not borderStartLeft
							carrierOnLeft = borderStartLeft
							
					# if xferL <= maxSplit: splitType = 'gradual'
					if xferL == gradualSplit: splitType = 'gradual'
					else: splitType = 'double'

					newLeftN, twistedLeft = incDoubleBed(k, count=xferL, edgeNeedle=prevLeftN, c=carrier, side='l', gauge=gauge, emptyNeedles=emptyNeedles, incMethod=incMethod, splitType=splitType)
					twistedStitches.extend(twistedLeft)

					if incMethod == 'split' and addBorder and xferL == gradualSplit: #since no split for > maxSplit yet
					# if incMethod == 'split' and addBorder and xferL <= maxSplit: #since no split for > maxSplit yet
						if newLeftN % 2 == 0: k.knit('+', f'f{newLeftN}', carrier)
						else: k.knit('+', f'b{newLeftN}', carrier)

						if not borderStartLeft:
							borderToDrop, borderMissN, dummyDropBorder, dummyTuckNs = insertBorder(justTuck=True, shiftTuckNs=nextTuckNs)
							# borderToDrop, borderMissN, dummyDropBorder, nextTuckNs = insertBorder(justTuck=True, shift=1)
							toDrop.extend(borderToDrop)
							carrierOnLeft = not borderStartLeft
						
						if borderMissN is None: borderMissN = leftMostBorderN-4

						k.comment('tuck over split') #remove #?
						tuckOverDrop = k.tuckOverSplit(borderC, '+') #NOTE: currently has roller advance same as main... change?
						toDrop.extend(tuckOverDrop)

						newLeftN, twistedLeft = incDoubleBed(k, count=xferL, edgeNeedle=newLeftN, c=carrier, side='l', gauge=gauge, incMethod='split', splitType='gradual')
						twistedStitches.extend(twistedLeft)

						borderStartLeft = True
						
					if dropBorder and addBorder: #TODO: have it do this later so less messy
						global sanityDrop 
						sanityDrop = [] #TODO: make it so we dont have to do this
						global lastDropR #new #check
						lastDropR = r #new #check

						k.comment('last drop') #remove #?
						
						toDrop = sortBedNeedles(toDrop)
						for p in range(0, 2): #do it twice
							for n in toDrop:
								needleBed = n[:1]
								needleNum = int(n[1:])
								if (needleNum < newLeftN or needleNum > prevLeftN) or ((needleBed == 'f' and (needleNum % gauge != 0 or gauge == 1)) or (needleBed == 'b' and needleNum % gauge == 0)): # this prevents dropping knits, but still drops tucks
									k.drop(n)
									if p == 0: sanityDrop.append(n) #new
						toDrop = []
						
						if carrierOnLeft: k.miss('-', f'f{borderMissN-1}', borderC) #miss out of the way
					
					# return toDrop
					return sortBedNeedles(toDrop) #new
				else: #decrease
					newLeftN, stackedLoopNeedles, twistedLeft = decDoubleBed(k, abs(xferL), prevLeftN, carrier, 'l', gauge, emptyNeedles)
					twistedStitches.extend(twistedLeft)

					if dir1 == '-': #rightShaping happened first
						if xferL == -1 or xferL == -2: notEnoughNeedlesDecCheck(k, decNeedle=prevLeftN, otherEdgeNeedle=n2, count=abs(xferL), c=carrier, gauge=gauge)
					else:
						if xferL == -2 and abs(prevLeftN-(n2-1)) < 8 and xferR < 0: #TODO: #check if it applies for dec by 1 on either side, dec by > 3 on R, and inc (by xfer, ofc)
							knitStacked = []
							for n in stackedLoopNeedles:
								needleNumber = int(n[1:])
								if needleNumber < n1: k.knit('+', n, carrier)
								elif n[0] == 'b' or needleNumber > n2: knitStacked.append(n)
							return knitStacked
			return [] #just return empty list if no knitStacked or toDrop

		def rightShaping():
			if xferR:
				if xferR > 0: #increase
					global borderStartLeft
					global toDrop

					carrierOnLeft = borderStartLeft
					droppedTucks = False
					borderMissN = None
					dropBorder = False

					nextTuckNs = []
					if addBorder:
						if dir1 == '-' or xferL < 1: #aka if right inc is happening first or there are no left inc in this row
							for n in toDrop:
								k.drop(n)
							toDrop = []

							borderToDrop, borderMissN, dropBorder, nextTuckNs = insertBorder()
							toDrop.extend(borderToDrop)
							borderStartLeft = not borderStartLeft
							carrierOnLeft = borderStartLeft
						
					# if xferR <= maxSplit: splitType = 'gradual' #remove #?
					if xferR == maxSplit: splitType = 'gradual'
					else: splitType = 'double'

					newRightN, twistedRight = incDoubleBed(k, count=xferR, edgeNeedle=prevRightN, c=carrier, side='r', gauge=gauge, emptyNeedles=emptyNeedles, incMethod=incMethod, splitType=splitType)
					twistedStitches.extend(twistedRight)

					# if incMethod == 'split' and addBorder and xferR <= maxSplit: #since no split for > 1 yet #remove #?
					if incMethod == 'split' and addBorder and xferR == gradualSplit:
						if newRightN % 2 == 0: k.knit('-', f'f{newRightN}', carrier)
						else: k.knit('-', f'b{newRightN}', carrier)

						if borderStartLeft:
							borderToDrop, borderMissN, dummyDropBorder, dummyTuckNs = insertBorder(justTuck=True, shiftTuckNs=nextTuckNs)
							toDrop.extend(borderToDrop)
							carrierOnLeft = not borderStartLeft
						
						if borderMissN is None: borderMissN = rightMostBorderN+4

						k.comment('tuck over split') #remove #?
						tuckOverDrop = k.tuckOverSplit(borderC, '-')
						toDrop.extend(tuckOverDrop)

						newRightN, twistedRight = incDoubleBed(k, count=xferR, edgeNeedle=newRightN, c=carrier, side='r', gauge=gauge, incMethod='split', splitType='gradual')
						twistedStitches.extend(twistedRight)

						borderStartLeft = False

					if dropBorder and addBorder:
						global sanityDrop
						sanityDrop = []

						global lastDropR #new #check
						lastDropR = r #new #check
						
						toDrop = sortBedNeedles(toDrop)
						k.comment('last drop') #remove #?
						for p in range(0, 2): #do it twice
							for n in toDrop:
								needleBed = n[:1]
								needleNum = int(n[1:])
								if (needleNum > newRightN or needleNum < prevRightN) or ((needleBed == 'f' and (needleNum % gauge != 0 or gauge == 1)) or (needleBed == 'b' and needleNum % gauge == 0)): # this prevents dropping knits, but still drops tucks
									k.drop(n)
									if p == 0: sanityDrop.append(n) #new
						toDrop = []
													
						if carrierOnLeft: k.miss('-', f'f{borderMissN-1}', borderC) #miss out of the way

					# return toDrop
					return sortBedNeedles(toDrop)
				else: #decrease
					newRightN, stackedLoopNeedles, twistedRight = decDoubleBed(k, abs(xferR), prevRightN, carrier, 'r', gauge, emptyNeedles)
					twistedStitches.extend(twistedRight)

					if dir1 == '+': #leftShaping happened first
						if xferR == -1 or xferR == -2: notEnoughNeedlesDecCheck(k, decNeedle=prevRightN, otherEdgeNeedle=n1, count=abs(xferR), c=carrier, gauge=gauge)
					else:
						if xferR == -2 and abs((prevRightN-1)-n1) < 8 and xferL < 0: #TODO: #check if it applies for dec by 1 on either side, dec by > 3 on L, and inc (by xfer, ofc)
							knitStacked = []
							for n in stackedLoopNeedles:
								needleNumber = int(n[1:])
								if needleNumber > n2: k.knit('-', n, carrier)
								elif n[0] == 'f' or needleNumber < n1: knitStacked.append(n)
							return knitStacked
			return [] #just return empty list if no knitStacked

		def backBedPass():
			knitStacked = []
			if addBorder and xferR > 0: toDrop = rightShaping()
			else: knitStacked = rightShaping()
			if incMethod != 'split' and dir1 == '+' and xferR > 0 and xferR < 2: #so can 1. get twisted stitches in *after* xfers, not before and 2. not have ladder #TODO: check if this interferes with anything for split
			# if dir1 == '+' and xferR > 0 and xferR < 3: #so can 1. get twisted stitches in *after* xfers, not before and 2. not have ladder #TODO: check if this interferes with anything for split
				for n in range(prevRightN+1, n2+1):
					if f'f{n}' not in emptyNeedles: k.knit('+', f'f{n}', carrier)

			if dir1 == '-' and prevLeftN is not None and n1 < prevLeftN: leftMostN = prevLeftN
			else: leftMostN = n1

			#TODO: have stitch pattern occur here if relevant #*#*#*
			def plainKnitBack(passLeftN, passRightN):
				for n in range(passRightN, passLeftN-1, -1):
					twist = None
					if f'b{n}' in twistedStitches: twist = f'b{n}'
					elif f'f{n}' in twistedStitches: twist = f'f{n}'
					if twist is not None:
						k.knit('-', twist, carrier) #to be twisted
						k.twist(twist, -rollerAdvance) #do twisted stitch now so can add another knit on that needle without additional knit being interpreted as twisted stitch
						twistedStitches.remove(twist) #get rid of it since we already twisted it
					elif f'b{n}' not in emptyNeedles and (dir1 == '+' or xferL <= 0 or n >= prevLeftN):
						k.knit('-', f'b{n}', carrier) #TODO: determine if best to knit over it if twisted stitch; maybe tuck instead? #if go to knit, add knit over for twisted fn too; else, have it be an 'else' after if twist is not none
					elif n == passLeftN: k.miss('-', f'b{n}', carrier) #new #check
					# if n == passLeftN and passLeftN != leftMostN and (dir1 == '+' or xferL <= 0 or n >= prevLeftN): #check #new #remove #? #v
					# 	if (n-1) % 2 == 0 and f'f{n-1}' not in emptyNeedles: k.tuck('-', f'f{n-1}', carrier) #front bed
					# 	elif (n-1) % 2 != 0 and f'b{n-1}' not in emptyNeedles: k.tuck('-', f'b{n-1}', carrier) #remove #? #^
				
				if jerseyPassesB > 1: #new
					if jerseyPassesB % 2 == 1: #whole odd number (great!)
						currPassCt = jerseyPassesB
					elif jerseyPassesB % 2 == 0: #whole even number; will alternate between two odd numbers
						passCt1 = jerseyPassesB + 1
						passCt2 = jerseyPassesB - 1
						if r % 2 == 0: currPassCt = passCt1
						else: currPassCt = passCt2
					
					if currPassCt != 1: #new (only tuck if doing more than one pass) #TODO: #check and decide if keep like this
						# if dir1 == '+' or xferL <= 0 or passLeftN >= prevLeftN: #TODO determine what to do if these aren't true #removed this because assigning left-most needle should take care of condition check
						# if passLeftN != leftMostN: #remove #? or #go back!
						if passLeftN > leftMostN: #new #check
							k.rollerAdvance(0)
							if (passLeftN-1) % 2 != 0 and f'b{passLeftN-1}' not in emptyNeedles: k.tuck('-', f'b{passLeftN-1}', carrier)
							elif passLeftN-1 != leftMostN and f'b{passLeftN-2}' not in emptyNeedles: k.tuck('-', f'b{passLeftN-2}', carrier)
							k.rollerAdvance(rollerAdvance)
						else: #to prevent holes along edges where front and back bed meet #new #v #TODO: check to make sure this doesn't mess up stretchiness of e.g. garter; try increasing stitch size for these tucks in it does affect it
							otherBedEndN = (leftMostN if (leftMostN % gauge == 0) else leftMostN+1)
							if otherBedEndN not in emptyNeedles:
								k.rollerAdvance(0) #new #check
								k.tuck('+', f'f{otherBedEndN}', carrier)
								k.miss('-', f'b{leftMostN}', carrier) #get it back out of the way #new #^ #check
								k.rollerAdvance(rollerAdvance) #new #check
						# if passLeftN != leftMostN and (dir1 == '+' or xferL <= 0 or passLeftN >= prevLeftN):
						# 	if (passLeftN-1) % 2 != 0 and f'b{passLeftN-1}' not in emptyNeedles: k.tuck('-', f'b{passLeftN-1}', carrier)
						# 	elif passLeftN-1 != leftMostN and f'b{passLeftN-2}' not in emptyNeedles: k.tuck('-', f'b{passLeftN-2}', carrier)
					
					for p in range(1, currPassCt):
						if p % 2 != 0:
							for n in range(passLeftN, passRightN+1):
								if f'b{n}' not in emptyNeedles and (dir1 == '+' or xferL <= 0 or n >= prevLeftN): k.knit('+', f'b{n}', carrier) #TODO: see if condition should still be met
								elif n == passRightN: k.miss('+', f'b{n}', carrier) #new #check
								if p < currPassCt-1 and n == passRightN:
									if passRightN != n2:
										if (n+1) % 2 != 0 and f'b{n+1}' not in emptyNeedles: k.tuck('+', f'b{n+1}', carrier)
										elif n+1 != n2 and f'b{n+2}' not in emptyNeedles: k.tuck('+', f'b{n+2}', carrier) #new #check
									else: #to prevent holes along edges where front and back bed meet #new #v
										otherBedEndN = (n2 if (n2 % gauge == 0) else n2-1)
										if otherBedEndN not in emptyNeedles:
											k.rollerAdvance(0) #new #check
											k.tuck('-', f'f{otherBedEndN}', carrier)
											k.miss('+', f'b{n2}', carrier) #new #^ #check
											k.rollerAdvance(rollerAdvance) #new #check
								# if p < currPassCt-1 and n == passRightN and passRightN != n2: #new #TODO: #check and decide if keep like this
								# 	if (n+1) % 2 != 0 and f'b{n+1}' not in emptyNeedles: k.tuck('+', f'b{n+1}', carrier)
								# 	elif n+1 != n2 and f'b{n+2}' not in emptyNeedles: k.tuck('+', f'b{n+2}', carrier) #new #check
						else:
							for n in range(passRightN, passLeftN-1, -1):
								if f'b{n}' not in emptyNeedles and (dir1 == '+' or xferL <= 0 or n >= prevLeftN): k.knit('-', f'b{n}', carrier)
								elif n == passLeftN: k.miss('-', f'b{n}', carrier) #new #check
								if p < currPassCt-1 and n == passLeftN:
									if passLeftN != leftMostN: #removed (dir1 == '+' or xferL <= 0 or n >= prevLeftN) since assigning leftMostN deals with this
										if (n-1) % 2 != 0 and f'b{n-1}' not in emptyNeedles: k.tuck('-', f'b{n-1}', carrier)
										elif n-1 != leftMostN and f'b{n-2}' not in emptyNeedles: k.tuck('-', f'b{n-2}', carrier)
									else: #new #v #check
										otherBedEndN = (leftMostN if (leftMostN % gauge == 0) else leftMostN+1)
										if otherBedEndN not in emptyNeedles:
											k.rollerAdvance(0) #new #check
											k.tuck('+', f'f{otherBedEndN}', carrier)
											k.miss('-', f'b{leftMostN}', carrier) #get it back out of the way #new #^ #check
											k.rollerAdvance(rollerAdvance) #new #check
								# if p < currPassCt-1 and n == passLeftN and passLeftN != leftMostN and (dir1 == '+' or xferL <= 0 or n >= prevLeftN): #TODO: #check and decide if keep like this
								# 	if (n-1) % 2 != 0 and f'b{n-1}' not in emptyNeedles: k.tuck('-', f'b{n-1}', carrier)
								# 	elif n-1 != leftMostN and f'b{n-2}' not in emptyNeedles: k.tuck('-', f'b{n-2}', carrier)

			# if xferR > 0 and xferR <= maxSplit: twistEdgeN = True #remove #?
			# else: twistEdgeN = False #remove #?

			if len(patternsB):
				passRightN = n2
				# passLeftN = n1 #remove #?
				passLeftN = leftMostN #new #check

				# if dir1 == '-' and prevLeftN is not None and n1 < prevLeftN: leftMostN = prevLeftN
				# else: leftMostN = n1

				for idx in reversed(list(patternsB.keys())):
					# patCarrier = carrier
					patNs = patternsB[idx].copy()
					patLeftN = patNs[0]
					patRightN = patNs[-1]

					# if 'side' in stitchPatDetailsB[idx].info: patSide = stitchPatDetailsB[idx].info['side']
					# else: patSide = 'r'

					if patRightN < leftMostN: break #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0 #new #check
					# if prevLeftN is not None and dir1 == '-' and patRightN < prevLeftN: break #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0 #new #check

					# if passRightN > patRightN: #check
					if passRightN > (patRightN+1): #new
						plainKnitBack(patRightN+1, passRightN)

					if patLeftN < leftMostN: patNs[0] = leftMostN #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0 #new #check
					# if prevLeftN is not None and dir1 == '-' and patLeftN < prevLeftN: patNs[0] = prevLeftN #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0 #new #check
					
					tuckDrop = []
					# if 'plaitC' in stitchPatDetailsB[idx].info and stitchPatDetailsB[idx].info['plaitC'] == None:
					plaitC = None
					if 'plaitC' in stitchPatDetailsB[idx].info:
						plaitC = stitchPatDetailsB[idx].info['plaitC']
						if (stitchPatDetailsB[idx].info['plaitC'] == None or r == workingRows[stitchPatDetailsB[idx].info['plaitC']][0]):
							if plaitC is None:
								if len(reusableCarriers):
									plaitC = reusableCarriers.pop()
									stitchPatDetailsB[idx].info['plaitC'] = plaitC
									print(f'\nat row {r}, a reusable carrier ({plaitC}) was just assigned to a plaiting section on the back bed.')
									plaitInfo['assigned'] += 1
									plaitInfo['carriers'].append(plaitC) #new
									plaitInfo['lastRows'][plaitC] = len(stitchPatDataB)-1 - next((i for i, data in enumerate(reversed(stitchPatDataB)) if idx in data.keys()), 0) #new #check
									# plaitInfo['lastRows'][len(stitchPatDataB)-1 - next((i for i, data in enumerate(reversed(stitchPatDataB)) if idx in data.keys()), 0)] = plaitC #new #check

									if plaitC in takenOutCarriers:
										k.incarrier(plaitC)
										takenOutCarriers.remove(plaitC) #new
										takeOutAtEnd.append(plaitC)

							if plaitC is not None:
								if abs(patNs[0]-leftMostN) < abs(patNs[-1]-n2):
									stitchPatDetailsB[idx].info['plaitCside'] = 'l'
									tuckDrop = placeCarrier(k, leftN=patNs[0], rightN=None, carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
								else:
									stitchPatDetailsB[idx].info['plaitCside'] = 'r'
									tuckDrop = placeCarrier(k, leftN=None, rightN=patNs[-1], carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*

								# tuckDrop = placeCarrier(k, leftN=None, rightN=n2, carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
							else: print(f'WARNING: at row {r}, we needed a carrier for plaiting but none were available. Note that the piece will have no plaiting in this section (back bed) until one does become available.')
						else: #tuck if far away #come back!
							if stitchPatDetailsB[idx].info['plaitCside'] == 'l': tuckDrop = placeCarrier(k, leftN=patNs[0], rightN=None, carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
							else: tuckDrop = placeCarrier(k, leftN=None, rightN=patNs[-1], carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
					# if 'plaitC' in stitchPatDetailsB[idx].info:
					# 	if stitchPatDetailsB[idx].info['plaitC'] == None:
					# 		if len(reusableCarriers):
					# 			plaitC = reusableCarriers.pop() #TODO: add tuck and then drop to get it in correct spot if applicable 
					# 			tuckDrop = placeCarrier(k, leftN=None, rightN=n2, carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
					# 			stitchPatDetailsB[idx].info['plaitC'] = plaitC
					# 			patCarrier = plaitC
					# 			if plaitC in takenOutCarriers:
					# 				k.incarrier(plaitC)
					# 				takenOutCarriers.remove(plaitC) #new
					# 				takeOutAtEnd.append(plaitC)
					# 	else: patCarrier = [carrier, stitchPatDetailsB[idx].info['plaitC']]

					if 'secureStartN' in stitchPatDetailsB[idx].args:
						if patNs[-1] == n2 or (gauge == 2 and patNs[-1] == n2-1): stitchPatDetailsB[idx].args['secureStartN'] = True #new n2-1
						else: stitchPatDetailsB[idx].args['secureStartN'] = False

						if patNs[0] == leftMostN or (gauge == 2 and patNs[0] == leftMostN+1): stitchPatDetailsB[idx].args['secureEndN'] = True #new leftMostN+1
						else: stitchPatDetailsB[idx].args['secureEndN'] = False

					patPasses = 1
					if 'passes' in stitchPatDetailsB[idx].info and stitchPatDetailsB[idx].info['passes'] > 1: #if multiple passes per pass of jersey
						passCt = stitchPatDetailsB[idx].info['passes']
						patNeedles = []
						if passCt % 2 == 1: #whole odd number (great!)
							patPasses = passCt
							for p in range(0, passCt):
								patNeedles.append(patNs)
						elif passCt % 2 == 0: #whole even number; will alternate between two odd numbers
							passCt1 = passCt + 1
							passCt2 = passCt - 1
							# if stitchPatDetailsB[idx].pattern == 'garter': mod = stitchPatDetailsB[idx].args['patternRows']
							# else: mod = 1
							# if stitchPatDetailsB[idx].info['count'] % (2*mod) <= mod-1: currPassCt = passCt1
							if stitchPatDetailsB[idx].info['count'] % 2 == 0: currPassCt = passCt1
							else: currPassCt = passCt2
							patPasses = currPassCt
							for p in range(0, currPassCt):
								patNeedles.append(patNs)
					else: patNeedles = patNs

					# # leftMissPlaitCs = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNs[0]]
					# # rightMissPlaitCs = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc <= patNs[-1]]
					# leftMissPlaitCs = [carr for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNeedles[0][0]]
					# rightMissPlaitCs = [carr for carr, loc in plaitInfo['carrierPark'].items() if loc <= patNeedles[0][-1]]
					# # plaitCsInTheWay = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNs[0] or ]
					# if len(leftMissPlaitCs):
					# 	for pC in leftMissPlaitCs:
					# 		k.comment(f'miss plaitC ({pC}) out of way of stitch pattern')
					# 		k.rollerAdvance(0)
					# 		k.miss('-', f'f{patNeedles[0][0]-3}', pC)
					# 		k.rollerAdvance(rollerAdvance)
					# if len(rightMissPlaitCs):
					# 	for pC in rightMissPlaitCs:
					# 		k.comment(f'miss plaitC ({pC}) out of way of stitch pattern')
					# 		k.rollerAdvance(0)
					# 		k.miss('+', f'f{patNeedles[0][-1]+3}', pC)
					# 		k.rollerAdvance(rollerAdvance)
					# plaitCsInTheWay = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNeedles[0][0] and loc <= patNeedles[0][-1]] #remove #?
					plaitCsInTheWay = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNs[0] and loc <= patNs[-1]] #new #*
					if len(plaitCsInTheWay):
						k.rollerAdvance(0)
						for pC in plaitCsInTheWay:
							k.comment(f'miss plaitC ({pC[0]}) out of way of stitch pattern')
							if abs((patNs[0])-pC[1]) < abs((patNs[-1])-pC[1]): #new #v
								k.miss('-', f'f{patNs[0]-3}', pC[0])
								plaitInfo['carrierPark'][pC[0]] = patNs[0]-3
							else:
								k.miss('+', f'f{patNs[-1]+3}', pC[0]) #closer to right side, pos miss
								plaitInfo['carrierPark'][pC[0]] = patNs[-1]+3 #^
							# if abs((patNeedles[0][0])-pC[1]) < abs((patNeedles[0][-1])-pC[1]): #remove #? #v
							# 	k.miss('-', f'f{patNeedles[0][0]-3}', pC[0])
							# 	plaitInfo['carrierPark'][pC[0]] = patNeedles[0][0]-3
							# else:
							# 	k.miss('+', f'f{patNeedles[0][-1]+3}', pC[0]) #closer to right side, pos miss
							# 	plaitInfo['carrierPark'][pC[0]] = patNeedles[0][-1]+3 #^
						k.rollerAdvance(rollerAdvance)
					

					k.comment(f'insert stitch pattern for bed b ({patPasses} pass count)') #remove #?

					if 'stitchNumber' in stitchPatDetailsB[idx].info: k.stitchNumber(stitchPatDetailsB[idx].info['stitchNumber'])

					insertStitchPattern(k, stitchPat=stitchPatDetailsB[idx], needles=patNeedles, passEdgeNs=[leftMostN, n2], bed='b', side='r', c=carrier)

					if 'stitchNumber' in stitchPatDetailsB[idx].info: k.stitchNumber(stitchNumber) #reset

					if len(twistedStitches):
						for n in range(patNs[-1], patNs[0], -1): #TODO: have this be possible for if stitch pattern length > 1 #new
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
					# if twistEdgeN: #remove #? #v
					# 	notFound = k.twist(f'b{n2}', -rollerAdvance) #turn edge-most needle into twisted stitch so don't have to worry about it getting dropped
					# 	if not len(notFound): twistEdgeN = False #remove #? #^

					if plaitC is not None and sectionCountChangeNext:
						k.comment(f'miss plaitC out of way of upcoming new section')
						k.rollerAdvance(0)
						if stitchPatDetailsB[idx].info['plaitCside'] == 'l':
							k.miss('-', f'f{rowsEdgeNeedles[r][0]}', plaitC) #new #*#*#*#*#*#* #new
							plaitInfo['carrierPark'][plaitC] = rowsEdgeNeedles[r][0]
						else:
							k.miss('+', f'f{rowsEdgeNeedles[r][-1]}', plaitC) #new #*#*#*#*#*#* #new
							plaitInfo['carrierPark'][plaitC] = rowsEdgeNeedles[r][-1]
						k.rollerAdvance(rollerAdvance)
				
					passRightN = patLeftN-1 #check
				
				if passRightN > passLeftN: plainKnitBack(passLeftN, passRightN)
			else:
				plainKnitBack(n1, n2)
				# if twistEdgeN: k.twist(f'b{n2}', -rollerAdvance) #turn edge-most needle into twisted stitch so don't have to worry about it getting dropped #remove #?

			# for n in range(n2, n1-1, -1): #go back! #*#*#*#*#*#*
			# 	twist = None
			# 	if f'b{n}' in twistedStitches: twist = f'b{n}'
			# 	elif f'f{n}' in twistedStitches: twist = f'f{n}'
			# 	if twist is not None:
			# 		k.knit('-', twist, carrier) #to be twisted
			# 		k.twist(twist, -rollerAdvance) #do twisted stitch now so can add another knit on that needle without additional knit being interpreted as twisted stitch
			# 		twistedStitches.remove(twist) #get rid of it since we already twisted it
			# 	elif f'b{n}' not in emptyNeedles and (dir1 == '+' or xferL <= 0 or n >= prevLeftN):
			# 		k.knit('-', f'b{n}', carrier) #TODO: determine if best to knit over it if twisted stitch; maybe tuck instead? #if go to knit, add knit over for twisted fn too; else, have it be an 'else' after if twist is not none

			if len(knitStacked):
				for n in knitStacked:
					k.knit('-', n, carrier)

		for n in range(n0, n1):
			visualization[r].append(0)

		if addBorder and r == lastWasteWeightRow and len(toDrop):
			# global lastDropR #new #check
			lastDropR = r #new #check
			# global sanityDrop
			sanityDrop = []

			if borderStartLeft: k.miss('-', f'f{leftMostBorderN-borderWidthAdd}', borderC)
			else: k.miss('+', f'f{rightMostBorderN+borderWidthAdd}', borderC)
			# if sectionFinished and not finishOff and r == wasteWeightsKeys[len(wasteWeightsKeys)-2]:
			k.comment('drop whatever is left') #new #check
			# toDrop = sortBedNeedles(toDrop)
			# print(r, rowsTakenNeedles)
			# toDrop = list(filter(lambda bn: int(bn[1:]) not in rowsTakenNeedles[r], toDrop))
			toDrop = list(filter(lambda bn: bn not in rowsTakenNeedles[r], toDrop))
			for n in toDrop:
				k.drop(n)
				sanityDrop.append(n)
			
			if gauge == 2 and f'f{leftMostBorderN-borderWidthAdd}' not in toDrop and f'b{leftMostBorderN-borderWidthAdd}': # drop waste borders too
				for n in range(leftMostBorderN-borderWidthAdd, rowsEdgeNeedles[r][0]):
					if n % gauge == 0: k.drop(f'f{n}')
					else: k.drop(f'b{n}')
				for n in range(rowsEdgeNeedles[r][1]+1, rightMostBorderN+borderWidthAdd+1):
					if n % gauge == 0: k.drop(f'f{n}')
					else: k.drop(f'b{n}')
			toDrop = []

		if addBorder and r == lastDropR+2:
			# print('lastDrop', lastDropR) #remove #debug
			# global sanityDrop
			if len(sanityDrop):
				# print('\nsanityDrop:', sanityDrop) #remove #debug
				sanityDrop = list(filter(lambda bn: bn not in rowsTakenNeedles[r], sanityDrop))
				# sanityDrop = list(filter(lambda bn: int(bn[1:]) not in rowsTakenNeedles[r], sanityDrop))
				# print('now sanityDrop:', sanityDrop) #remove #debug

				k.comment(f'sanity drop') #remove #debug
				for n in sanityDrop:
					k.drop(n)
				sanityDrop = []

		# if addBorder and r == (lastWasteWeightRow+2) and len(sanityDrop): #new #TODO: maybe move sanityDrop to earlier? (lastWasteWeightRow+1)
		# 	k.comment(f'sanity drop {sanityDrop}')
		# 	for n in sanityDrop:
		# 		k.drop(n)
		
		if dir1 == '-':
			backBedPass()
			if (xferL <-2): #so no ladder (carrier is in correct spot to dec)
				for n in range(n1-1, prevLeftN-1, -1):
					if f'b{n}' not in emptyNeedles: k.knit('-', f'b{n}', carrier)

		knitStacked = []
		if addBorder and xferL > 0: toDrop = leftShaping()
		else: knitStacked = leftShaping()

		if dir1 == '+' and prevRightN is not None and n2 > prevRightN: rightMostN = prevRightN
		else: rightMostN = n2

		def plainKnitFront(passLeftN, passRightN):
			if placementLeft and passLeftN <= (prevLeftN-1): #new #check
				passLeftN = prevLeftN #for now
				# for n in range(prevLeftN-1, passLeftN-1, -1): #check
				# 	if f'b{n}' not in emptyNeedles: k.knit('-', f'b{n}', carrier)

			for n in range(passLeftN, passRightN+1):
				twist = None
				if f'b{n}' in twistedStitches: twist = f'b{n}'
				elif f'f{n}' in twistedStitches: twist = f'f{n}'
				if twist is not None:
					k.knit('+', twist, carrier) #to be twisted
					k.twist(twist, -rollerAdvance) #do twisted stitch now so can add another knit on that needle without additional knit being interpreted as twisted stitch
					twistedStitches.remove(twist) #get rid of it since we already twisted it
				elif (dir1 == '-' or xferR <= 0 or n <= prevRightN) and f'f{n}' not in emptyNeedles: #don't add the knits if increasing, since they will be added anyway thru increasing
					k.knit('+', f'f{n}', carrier) #TODO: determine if best to knit over it if twisted stitch; maybe tuck instead? #if go to knit, add knit over for twisted fn too; else, have it be an 'else' after if twist is not none
				elif n == passRightN: k.miss('+', f'f{n}', carrier) #new #check
				# if n == passRightN and passRightN != rightMostN and (dir1 == '-' or xferR <= 0 or n <= prevRightN): #new #check #remove or #go back! #? #v
				# 	if (n+1) % 2 == 0 and f'f{n+1}' not in emptyNeedles: k.tuck('+', f'f{n+1}', carrier) #front bed
				# 	elif (n+1) % 2 != 0 and f'b{n+1}' not in emptyNeedles: k.tuck('+', f'b{n+1}', carrier) #remove or #go back! #? #^
			
			if jerseyPassesF > 1: #new
				if jerseyPassesF % 2 == 1: #whole odd number (great!)
					currPassCt = jerseyPassesF
				elif jerseyPassesF % 2 == 0: #whole even number; will alternate between two odd numbers
					passCt1 = jerseyPassesF + 1
					passCt2 = jerseyPassesF - 1
					if r % 2 == 0: currPassCt = passCt1
					else: currPassCt = passCt2
				
				if currPassCt != 1: #new (only tuck if doing more than one pass) #TODO: #check and decide if keep like this
					# if dir1 == '-' or xferR <= 0 or passRightN <= prevRightN: #removed since assigning rightMostN prevents this
					# if passRightN != rightMostN:
					if passRightN < rightMostN: #new #check
						if (passRightN+1) % 2 == 0 and f'f{passRightN+1}' not in emptyNeedles: k.tuck('+', f'f{passRightN+1}', carrier) #front bed
						elif passRightN+1 != rightMostN and f'f{passRightN+2}' not in emptyNeedles: k.tuck('+', f'f{passRightN+2}', carrier)
					else: #new #v
						otherBedEndN = (rightMostN-1 if (rightMostN % 2 == 0) else rightMostN)
						if otherBedEndN not in emptyNeedles:
							k.rollerAdvance(0) #new #check
							k.tuck('-', f'b{otherBedEndN}', carrier)
							k.miss('+', f'f{rightMostN}', carrier) #new #^ #check
							k.rollerAdvance(rollerAdvance) #new #check
					# if passRightN != rightMostN and (dir1 == '-' or xferR <= 0 or passRightN <= prevRightN):
					# 	if (passRightN+1) % 2 == 0 and f'f{passRightN+1}' not in emptyNeedles: k.tuck('+', f'f{passRightN+1}', carrier) #front bed
					# 	elif passRightN+1 != rightMostN and f'f{passRightN+2}' not in emptyNeedles: k.tuck('+', f'f{passRightN+2}', carrier)

				for p in range(1, currPassCt): #won't execute if only one pass (already did it above)
					if p % 2 != 0:
						for n in range(passRightN, passLeftN-1, -1):
							if f'f{n}' not in emptyNeedles and (dir1 == '-' or xferR <= 0 or n <= prevRightN): k.knit('-', f'f{n}', carrier)
							elif n == passLeftN: k.miss('-', f'f{n}', carrier) #new #check
							if p < currPassCt-1 and n == passLeftN:
								if passLeftN != n1: #new #TODO: #check and decide if keep like this
									if (n-1) % 2 == 0 and f'f{n-1}' not in emptyNeedles: k.tuck('-', f'f{n-1}', carrier) #front bed
									elif n-1 != n1 and f'f{n-2}' not in emptyNeedles: k.tuck('-', f'f{n-2}', carrier)
								else: #new #v
									otherBedEndN = (n1+1 if (n1 % 2 == 0) else n1)
									if otherBedEndN not in emptyNeedles:
										k.rollerAdvance(0) #new #check
										k.tuck('+', f'b{otherBedEndN}', carrier)
										k.miss('-', f'f{n1}', carrier) #new #^ #check
										k.rollerAdvance(rollerAdvance) #new #check
							# if p < currPassCt-1 and n == passLeftN and passLeftN != n1: #TODO: #check and decide if keep like this
							# 	if (n-1) % 2 == 0 and f'f{n-1}' not in emptyNeedles: k.tuck('-', f'f{n-1}', carrier) #front bed
							# 	elif n-1 != n1 and f'f{n-2}' not in emptyNeedles: k.tuck('-', f'f{n-2}', carrier)
					else:
						for n in range(passLeftN, passRightN+1):
							if f'f{n}' not in emptyNeedles and (dir1 == '-' or xferR <= 0 or n <= prevRightN): k.knit('+', f'f{n}', carrier) #TODO: see if condition and (dir1 == '-' or xferR <= 0 or n <= prevRightN) should still be met
							elif n == passRightN: k.miss('+', f'f{n}', carrier) #new #check
							if p < currPassCt-1 and n == passRightN:
								if passRightN != rightMostN: #removed < and (dir1 == '-' or xferR <= 0 or n <= prevRightN) > since assigning rightMostN should take care of this
									k.rollerAdvance(0) #new #check
									if (n+1) % 2 == 0 and f'f{n+1}' not in emptyNeedles: k.tuck('+', f'f{n+1}', carrier) #front bed
									elif n+1 != rightMostN and f'f{n+2}' not in emptyNeedles: k.tuck('+', f'f{n+2}', carrier) #front bed
									k.rollerAdvance(rollerAdvance) #new #check
								else:
									otherBedEndN = (rightMostN-1 if (rightMostN % 2 == 0) else rightMostN)
									if otherBedEndN not in emptyNeedles:
										k.rollerAdvance(0) #new #check
										k.tuck('-', f'b{otherBedEndN}', carrier)
										k.miss('+', f'f{rightMostN}', carrier) #new #^ #check
										k.rollerAdvance(rollerAdvance) #new #check
							# if p < currPassCt-1 and n == passRightN and passRightN != rightMostN and (dir1 == '-' or xferR <= 0 or n <= prevRightN): #TODO: #check and decide if keep like this
							# 	if (n+1) % 2 == 0 and f'f{n+1}' not in emptyNeedles: k.tuck('+', f'f{n+1}', carrier) #front bed
							# 	elif n+1 != rightMostN and f'f{n+2}' not in emptyNeedles: k.tuck('+', f'f{n+2}', carrier) #front bed

		if len(patternsF):
			passLeftN = n1
			# passRightN = n2
			passRightN = rightMostN #new #check

			# if dir1 == '+' and prevRightN is not None and n2 > prevRightN: rightMostN = prevRightN
			# else: rightMostN = n2

			# for idx, patNs in reversed(patternsB):
			# elif (dir1 == '-' or xferR <= 0 or n <= prevRightN) and f'f{n}' not in emptyNeedles: #don't add the knits if increasing, since they will be added anyway thru increasing
			for idx in list(patternsF.keys()):
				# patCarrier = carrier
				patNs = patternsF[idx].copy()
				patLeftN = patNs[0]
				patRightN = patNs[-1]

				# if 'side' in stitchPatDetailsF[idx].info: patSide = stitchPatDetailsF[idx].info['side']
				# else: patSide = 'l'

				if patLeftN > rightMostN: break #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0
				# if prevRightN is not None and dir1 == '+' and patLeftN > prevRightN: break #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0

				# if passLeftN < patLeftN: #remove #?
				if passLeftN < (patLeftN-1): #new
					plainKnitFront(passLeftN, patLeftN-1)

				if patRightN > rightMostN: patNs[-1] = rightMostN #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0
				# if prevRightN is not None and dir1 == '+' and patRightN > prevRightN: patNs[-1] = prevRightN #don't add the knits if increasing, since they will be added anyway thru increasing # and xferR > 0
				
				tuckDrop = []
				plaitC = None #new
				# if 'plaitC' in stitchPatDetailsF[idx].info and stitchPatDetailsF[idx].info['plaitC'] == None:
				if 'plaitC' in stitchPatDetailsF[idx].info:
					plaitC = stitchPatDetailsF[idx].info['plaitC']
					if (stitchPatDetailsF[idx].info['plaitC'] == None or r == workingRows[stitchPatDetailsF[idx].info['plaitC']][0]): #new
						# plaitC = stitchPatDetailsF[idx].info['plaitC']
						if plaitC is None: #new
							if len(reusableCarriers):
								plaitC = reusableCarriers.pop()
								stitchPatDetailsF[idx].info['plaitC'] = plaitC
								print(f'\nat row {r}, a reusable carrier ({plaitC}) was just assigned to a plaiting section on the front bed.')
								plaitInfo['assigned'] += 1
								plaitInfo['carriers'].append(plaitC) #new
								plaitInfo['lastRows'][plaitC] = len(stitchPatDataF)-1 - next((i for i, data in enumerate(reversed(stitchPatDataF)) if idx in data.keys()), 0) #new #check
								# plaitInfo['lastRows'][len(stitchPatDataF)-1 - next((i for i, data in enumerate(reversed(stitchPatDataF)) if idx in data.keys()), 0)] = plaitC #new #check

								if plaitC in takenOutCarriers:
									k.incarrier(plaitC)
									takenOutCarriers.remove(plaitC) #new
									takeOutAtEnd.append(plaitC)

						if plaitC is not None: #new
							if abs(patNs[-1]-rightMostN) < abs(patNs[0]-n1):
								stitchPatDetailsF[idx].info['plaitCside'] = 'r'
								tuckDrop = placeCarrier(k, leftN=None, rightN=patNs[-1], carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
							else:
								stitchPatDetailsF[idx].info['plaitCside'] = 'l'
								tuckDrop = placeCarrier(k, leftN=patNs[0], rightN=None, carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
								
							# tuckDrop = placeCarrier(k, leftN=n1, rightN=None, carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
						else: print(f'WARNING: at row {r}, we needed a carrier for plaiting but none were available. Note that the piece will have no plaiting in this section (front bed) until one does become available.')
					else: #tuck if far away
						if stitchPatDetailsF[idx].info['plaitCside'] == 'l': tuckDrop = placeCarrier(k, leftN=patNs[0], rightN=None, carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
						else: tuckDrop = placeCarrier(k, leftN=None, rightN=patNs[-1], carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*

				# if 'plaitC' in stitchPatDetailsF[idx].info:
				# 	if stitchPatDetailsF[idx].info['plaitC'] == None:
				# 		if len(reusableCarriers):
				# 			plaitC = reusableCarriers.pop()
				# 			tuckDrop = placeCarrier(k, leftN=n1, rightN=None, carrierOpts=[plaitC], gauge=gauge)[0] #new #here#*
				# 			stitchPatDetailsF[idx].info['plaitC'] = plaitC
				# 			patCarrier = [carrier, plaitC]
				# 			if plaitC in takenOutCarriers:
				# 				k.incarrier(plaitC)
				# 				takenOutCarriers.remove(plaitC) #new
				# 				takeOutAtEnd.append(plaitC)
				# 	else: patCarrier = [carrier, stitchPatDetailsF[idx].info['plaitC']]

				# if 'plaitC' in stitchPatDetailsF[idx].info and stitchPatDetailsF[idx].info['plaitC'] == None:
				# 	if len(reusableCarriers): stitchPatDetailsF[idx].info['plaitC'] = reusableCarriers.pop() #new #TODO: add tuck and then drop to get it in correct spot if applicable

				if 'secureStartN' in stitchPatDetailsF[idx].args:
					if patNs[0] == n1 or (gauge == 2 and patNs[0] == n1+1): stitchPatDetailsF[idx].args['secureStartN'] = True #new n1+1
					else: stitchPatDetailsF[idx].args['secureStartN'] = False

					if patNs[-1] == rightMostN or (gauge == 2 and patNs[-1] == rightMostN-1): stitchPatDetailsF[idx].args['secureEndN'] = True #new rightMostN-1
					else: stitchPatDetailsF[idx].args['secureEndN'] = False

				patPasses = 1
				if 'passes' in stitchPatDetailsF[idx].info and stitchPatDetailsF[idx].info['passes'] > 1: #if multiple passes per pass of jersey
					passCt = stitchPatDetailsF[idx].info['passes']
					patNeedles = []
					if passCt % 2 == 1: #whole odd number (great!)
						patPasses = passCt
						for p in range(0, passCt):
							patNeedles.append(patNs)
					elif passCt % 2 == 0: #whole even number; will alternate between two odd numbers
						passCt1 = passCt + 1
						passCt2 = passCt - 1
						# if stitchPatDetailsF[idx].pattern == 'garter': mod = stitchPatDetailsF[idx].args['patternRows'] #new
						# else: mod = 1
						# if stitchPatDetailsF[idx].info['count'] % (2*mod) <= mod-1: currPassCt = passCt1 #new
						if stitchPatDetailsF[idx].info['count'] % 2 == 0: currPassCt = passCt1
						else: currPassCt = passCt2
						patPasses = currPassCt
						for p in range(0, currPassCt):
							patNeedles.append(patNs)
				else: patNeedles = patNs

				# if placementLeft and patNs[0] <= (prevLeftN-1): #new #check #come back! #here #*#*#*
				if placementLeft and patNs[0] < prevLeftN: #new #check #come back! #here #*#*#*
					if type(patNeedles[0]) == list: patNeedles[0][0] = prevLeftN #new#new
					else: patNeedles[0] = prevLeftN #have first (or only) pass start at prevLeftN
					# insertStitchPattern(k, stitchPat=stitchPatDetailsF[idx], needles=[patNs[0], prevLeftN-1], passEdgeNs=[n1, rightMostN], bed='b', side='r', c=carrier, updateInfo=False)
				# for n in range(prevLeftN-1, passLeftN-1, -1): #check
				# 	if f'b{n}' not in emptyNeedles: k.knit('-', f'b{n}', carrier)

				# leftMissPlaitCs = [carr for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNeedles[0][0]]
				# rightMissPlaitCs = [carr for carr, loc in plaitInfo['carrierPark'].items() if loc <= patNeedles[0][-1]]
				# plaitCsInTheWay = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNeedles[0][0] and loc <= patNeedles[0][-1]] #remove #?
				plaitCsInTheWay = [[carr, loc] for carr, loc in plaitInfo['carrierPark'].items() if loc >= patNs[0] and loc <= patNs[-1]] #new #*
				if len(plaitCsInTheWay):
					k.rollerAdvance(0)
					for pC in plaitCsInTheWay:
						k.comment(f'miss plaitC ({pC[0]}) out of way of stitch pattern')
						if abs((patNs[-1])-pC[1]) < abs((patNs[0])-pC[1]): #new #v
							k.miss('+', f'f{patNs[-1]+3}', pC[0]) #closer to right side, pos miss
							plaitInfo['carrierPark'][pC[0]] = patNs[-1]+3
						else:
							k.miss('-', f'f{patNs[0]-3}', pC[0])
							plaitInfo['carrierPark'][pC[0]] = patNs[0]-3 #new #^
						# if abs((patNeedles[0][-1])-pC[1]) < abs((patNeedles[0][0])-pC[1]): #remove #? #v
						# 	k.miss('+', f'f{patNeedles[0][-1]+3}', pC[0]) #closer to right side, pos miss
						# 	plaitInfo['carrierPark'][pC[0]] = patNeedles[0][-1]+3
						# else:
						# 	k.miss('-', f'f{patNeedles[0][0]-3}', pC[0])
						# 	plaitInfo['carrierPark'][pC[0]] = patNeedles[0][0]-3 #remove #? #^
					k.rollerAdvance(rollerAdvance)
				# if len(leftMissPlaitCs):
				# 	for pC in leftMissPlaitCs:
				# 		print('!!L', plaitInfo['carrierPark'][pC], patNeedles[0][0]) #remove #debug
				# 		akfbsjkfd
				# 		k.comment(f'miss plaitC ({pC}) out of way of stitch pattern')
				# 		k.rollerAdvance(0)
				# 		k.miss('-', f'f{patNeedles[0][0]-3}', pC)
				# 		k.rollerAdvance(rollerAdvance)
				# if len(rightMissPlaitCs):
				# 	for pC in rightMissPlaitCs:
				# 		print('!!R', plaitInfo['carrierPark'][pC], patNeedles[0][-1]) #remove #debug
				# 		skdfjbskjds
				# 		k.comment(f'miss plaitC ({pC}) out of way of stitch pattern')
				# 		k.rollerAdvance(0)
				# 		k.miss('+', f'f{patNeedles[0][-1]+3}', pC)
				# 		k.rollerAdvance(rollerAdvance)

				k.comment(f'insert stitch pattern for bed f ({patPasses} pass count)') #remove #?

				if 'stitchNumber' in stitchPatDetailsF[idx].info: k.stitchNumber(stitchPatDetailsF[idx].info['stitchNumber'])

				insertStitchPattern(k, stitchPat=stitchPatDetailsF[idx], needles=patNeedles, passEdgeNs=[n1, rightMostN], bed='f', side='l', c=carrier)
				
				if 'stitchNumber' in stitchPatDetailsF[idx].info: k.stitchNumber(stitchNumber) #reset it

				if len(twistedStitches):
					for n in range(patNs[0], patNs[-1]): #TODO: have this be possible for if stitch pattern length > 1 #new
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

				if plaitC is not None and sectionCountChangeNext:
					k.comment(f'miss plaitC out of way of upcoming new section')
					k.rollerAdvance(0)
					if stitchPatDetailsF[idx].info['plaitCside'] == 'l':
						k.miss('-', f'f{rowsEdgeNeedles[r][0]}', plaitC) #new #*#*#*#*#*#* #new
						plaitInfo['carrierPark'][plaitC] = rowsEdgeNeedles[r][0]
					else:
						k.miss('+', f'f{rowsEdgeNeedles[r][-1]}', plaitC) #new #*#*#*#*#*#* #new
						plaitInfo['carrierPark'][plaitC] = rowsEdgeNeedles[r][-1]
					k.rollerAdvance(rollerAdvance)
					# k.miss('-', f'f{rowsEdgeNeedles[r][0]}', plaitC) #new #*#*#*#*#*#* #new
				# for (key, val) in returns.items():
				# 		if key in stitchPatDetailsF[idx]['info']: stitchPatDetailsF[idx]['info'][key] = val
				# 		elif key in stitchPatDetailsF[idx]['args']: stitchPatDetailsF[idx]['args'][key] = val

				passLeftN = patRightN+1 #check
			
			if passRightN > passLeftN: plainKnitFront(passLeftN, passRightN) #check
		else:
			plainKnitFront(n1, n2)

		for n in range(n1, n2 + 1):
			visualization[r].append(int(carrier))

			# twist = None #go back! #? #v #here
			# if f'b{n}' in twistedStitches: twist = f'b{n}'
			# elif f'f{n}' in twistedStitches: twist = f'f{n}'
			# if twist is not None:
			# 	k.knit('+', twist, carrier) #to be twisted
			# 	k.twist(twist, -rollerAdvance) #do twisted stitch now so can add another knit on that needle without additional knit being interpreted as twisted stitch
			# 	twistedStitches.remove(twist) #get rid of it since we already twisted it
			# elif (dir1 == '-' or xferR <= 0 or n <= prevRightN) and f'f{n}' not in emptyNeedles: #don't add the knits if increasing, since they will be added anyway thru increasing
			# 	k.knit('+', f'f{n}', carrier) #TODO: determine if best to knit over it if twisted stitch; maybe tuck instead? #if go to knit, add knit over for twisted fn too; else, have it be an 'else' after if twist is not none #go back! #? #^

		if len(knitStacked):
			for n in knitStacked:
				k.knit('+', n, carrier)

		if dir1 == '+' and (xferR < -2): #so no ladder (carrier is in correct spot to dec or inc with yarn)
			for n in range(n2+1, prevRightN+1):
				if f'f{n}' not in emptyNeedles: k.knit('+', f'f{n}', carrier)

		if dir1 == '+': backBedPass()

		if len(placementPass): #if applicable, place middle section carrier by new left-most needle to get it out of the way for new left-most shortrow section in next row
			for n in range(placementPass[0], placementPass[1]+1):
				if f'b{n}' not in emptyNeedles: k.knit('+', f'b{n}', carrier)
			k.miss('+', f'b{placementPass[1]+1}', carrier)

		for bn in twistedStitches:
			k.twist(bn, -rollerAdvance)

		# if (plaitInfo['count'] != plaitInfo['assigned'] or (leftDropWasteC is None and rightDropWasteC is None)) and r in plaitInfo['lastRows'].values(): #new #check
		if sectionIdx == (sectionCount-1) and (plaitInfo['count'] != plaitInfo['assigned'] or (leftDropWasteC is None and rightDropWasteC is None)) and r in plaitInfo['lastRows'].values(): #new #check
			for lC, lR in plaitInfo['lastRows'].items():
				if lR == r:
					reusableCarriers.append(lC)
					if plaitInfo['count'] != plaitInfo['assigned']: print(f'at row {r}, a carrier that was being used for plaiting ({lC}) just became available, which we needed for a plaiting section!') #new
					else: print(f'at row {r}, a carrier that was being used for plaiting ({lC}) just became available, which we needed for the drop waste border!') #new
				# reusableCarriers.append(plaitInfo['lastRows']) #new #check #TODO: miss out of the way #here#* #new #check
			# reusableCarriers.append(plaitInfo['lastRows'][r]) #TODO: miss out of the way #here#*

		if sectionFinished:
			if dir1 == '+':
				bindSide = 'l'
				bindXferN = n1
			else:
				bindSide = 'r'
				bindXferN = n2
			if addBindoff:
				if closedCaston or openBindoff == True: halfGaugeOpenBindoff(k, (n2-n1+1), bindXferN, carrier, bindSide)
				else: bindoff(k, (n2-n1+1), bindXferN, carrier, bindSide, emptyNeedles=emptyNeedles)
			else: #drop finish
				outCarriers = []

				if addBorder: widthAdd = borderWidthAdd
				else: widthAdd = 0

				# if r == len(pieceMap)-1:
				if r == len(pieceMap)-1 and sectionIdx == sectionCount-1: #new
					rollOut = True
					outCarriers.append(carrier)
					outCarriers.extend(takeOutAtEnd)
					outCarriers = list(set(outCarriers)) #ensure no duplicates
				else:
					# if len(plaitInfo['count']) == len(plaitInfo['assigned']):
					if (plaitInfo['count'] == plaitInfo['assigned']) and (leftDropWasteC is not None or rightDropWasteC is not None):
						outCarriers.append(carrier)
						takeOutAtEnd.remove(carrier) #new #check
					else: #might need the carrier for plaiting
						if plaitInfo['count'] != plaitInfo['assigned']: print(f'at row {r}, a carrier that was being used in the main piece ({carrier}) just became available, which we needed for a plaiting section!') #new
						else: print(f'at row {r}, a carrier that was being used in the main piece ({carrier}) just became available, which we needed for the drop waste border!') #new
						reusableCarriers.append(carrier) #new
					# 	print(r, '%', plaitInfo['lastRows']) #remove #debug
					# 	if r in plaitInfo['lastRows']: reusableCarriers.append(plaitInfo['lastRows'][r]) #new #check
					 
					if abs(bindXferN-(leftMostBorderN-widthAdd)) < abs(bindXferN-(rightMostBorderN+widthAdd)):
						dropMissDir = '-'
						k.miss('-', f'f{leftMostBorderN-widthAdd}', carrier)
						# takeOutAtEnd.append(carrier)
					# outCarriers.append(carrier) #TODO: maybe don't do this #?
					else:
						dropMissDir = '+'
						k.miss('+', f'f{rightMostBorderN+widthAdd}', carrier)
						# takeOutAtEnd.append(carrier)
					rollOut = False
				# if len(takeOutAtEnd): dropBorderC = takeOutAtEnd[0]
				# else: dropBorderC = None #for now

				# dropBorderC = None #for now #go back! #?

				# takenOutCarriers.extend(outCarriers) #new

				# dropTuckDir = dir1 #go back! #?
				# tuckDrop = [] #go back! #?

				recycledCarrier = False #new #v
				if leftDropWasteC is None and len(reusableCarriers):
					leftDropWasteC = reusableCarriers[0]
					if leftDropWasteC in takenOutCarriers:
						k.incarrier(leftDropWasteC)
						takeOutAtEnd.append(leftDropWasteC)
						takenOutCarriers.remove(leftDropWasteC)
					recycledCarrier = True #new #^

				# return placedCarrier, tuckDrop, tuckDir
				tuckDrop, dropBorderC, dropTuckDir = placeCarrier(k, leftN=n1, rightN=n2, carrierOpts=[leftDropWasteC, rightDropWasteC], gauge=gauge) #new #here#*
				if dropTuckDir is None: dropTuckDir = dir1

				# if leftDropWasteC is not None: lastLineLeftDropC = k.returnLastOp(carrier=leftDropWasteC)
				# else: lastLineLeftDropC = None

				# if rightDropWasteC is not None: lastLineRightDropC = k.returnLastOp(carrier=rightDropWasteC)
				# else: lastLineRightDropC = None

				# distances = {}
				# needleNums = {}

				# if lastLineLeftDropC is not None:
				# 	needleNum = int(lastLineLeftDropC.split()[2][1:])
				# 	needleNums[leftDropWasteC] = needleNum
				# 	distances[abs(needleNum-n1)] = {'carrier': leftDropWasteC, 'direction': '+'}
				# 	distances[abs(needleNum-n2)] = {'carrier': leftDropWasteC, 'direction': '-'}

				# if lastLineRightDropC is not None:
				# 	needleNum = int(lastLineRightDropC.split()[2][1:])
				# 	needleNums[rightDropWasteC] = needleNum
				# 	distances[abs(needleNum-n1)] = {'carrier': rightDropWasteC, 'direction': '+'}
				# 	distances[abs(needleNum-n2)] = {'carrier': rightDropWasteC, 'direction': '-'}
				
				# if len(distances): 
				# 	minDist = min(distances.keys())
				# 	dropBorderC = distances[minDist]['carrier']
				# 	dropTuckDir = distances[minDist]['direction']

				# 	if minDist > 5: #need to tuck to get it in correct spot
				# 		tuckB = 0 #for tucking every other
				# 		tuckF = 0 

				# 		if dropTuckDir == '+':
				# 			for t in range(needleNums[dropBorderC]+1, n1):
				# 				if t % gauge == 0:
				# 					if tuckB % 2 == 0:
				# 						k.tuck('+', f'b{t}', dropBorderC)
				# 						tuckDrop.append(f'b{t}')
				# 					tuckB += 1
				# 				elif t % gauge != 0:
				# 					if tuckF % 2 == 0:
				# 						k.tuck('+', f'f{t}', dropBorderC)
				# 						tuckDrop.append(f'f{t}')
				# 					tuckF += 1
				# 		else:
				# 			for t in range(needleNums[dropBorderC]-1, n2, -1):
				# 				if t % gauge == 0:
				# 					if tuckB % 2 == 0:
				# 						k.tuck('-', f'b{t}', dropBorderC)
				# 						tuckDrop.append(f'b{t}')
				# 					tuckB += 1
				# 				elif t % gauge != 0:
				# 					if tuckF % 2 == 0:
				# 						k.tuck('-', f'f{t}', dropBorderC)
				# 						tuckDrop.append(f'f{t}')
				# 					tuckF += 1
				if finishOff: dropFinish(k, [n1, n2], [n1, n2], outCarriers, rollOut, emptyNeedles, direction=dropTuckDir, borderC=dropBorderC, borderStPat='rib')
				# if finishOff: dropFinish(k, [n1, n2], [n1, n2], outCarriers, rollOut, emptyNeedles, direction=dropTuckDir, borderC=dropBorderC)
				else:
					for oC in outCarriers:
						k.outcarrier(oC) #new #check
						if oC in takeOutAtEnd: takeOutAtEnd.remove(oC) #new #check #*#*#*#*#*

				# dropFinish(k, [n1, n2], [n1, n2], outCarriers, rollOut, emptyNeedles, direction=dropTuckDir, borderC=dropBorderC)

				takenOutCarriers.extend(outCarriers) #new

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
				
				if recycledCarrier: leftDropWasteC = None #new so it is available for other stuff

		#-------------------------
		n0 = n2 + 1

		if sectionIdx == sectionCount-1:
			for n in range(n0, width):
				row.append(0)
				visualization[r].append(0)
		else: endPoints.append(n0)

		shortrowCount += 1

		r += 1 #*

		if sectionIdx < sectionCount-1:
			if sectionCountChangeNext:
				if sectionIdx == 0: cycleEnd = r-1 #new #check
				sectionIdx += 1
				r -= shortrowCount
				shortrowCount = 0
			elif (shortrowCount == maxShortrowCount) or r == len(pieceMap):
			# elif shortrowCount == maxShortrowCount:
				if sectionIdx == 0: cycleEnd = r-1 #new #check
				if r == len(pieceMap):
					r -= shortrowCount #new
					shortrowCount = 0
					sectionIdx += 1
				else:
					shortrowCount = 0
					sectionIdx += 1
					r -= maxShortrowCount
				# shortrowCount = 0
				# sectionIdx += 1
				# else: r -= maxShortrowCount
		else:
			if sectionCountChangeNext or shortrowCount == maxShortrowCount:
				shortrowCount = 0
				sectionIdx = 0
		
		#do it until: maxShortrowCount or sectionCountChangeNext #come back! #*

	# if addBindoff: #take out extra carriers if not already done thru dropFinish
	# 	for carrier in wasteWeightCarriers: k.outcarrier(carrier)

	vFile = open('./visualization.txt', 'w')
	 
	# print('\nvisualization:') #remove
	for v in visualization:
		for c in v: vFile.write(''.join(str(c)))
		vFile.write('\n')
		# print(v) #remove

	vFile.close()

	print('\ndone.')


#----------------------
#--- TEST FUNCTIONS ---
#----------------------

def testHalfGaugeInc(k, incMethod='split', startWidth=40, endWidth=50, length=21, splitType='gradual'): #TODO: add option of inc by > 1 per row
	'''
	*startWidth is number of needles to start with at base of fabric (NOTE: *NOT* number of loops)
	'''
	dropWaste = False #remove #?
	tuckForBothSides = False #remove #?
	# tuckOverSplit = True #does gradual split once, tucks over it, then does gradual split again
	tuckOverSplit = False #does gradual split once, tucks over it, then does gradual split again

	if splitType == 'gradual': gradualSplit = True
	else: gradualSplit = False

	gauge = 2
	posBed = 'f'
	negBed = 'b'

	leftN = 0
	rightN = startWidth-1
	mainC = '2'
	drawC = '1'
	borderC='3'

	incCount = endWidth-startWidth # //2 since half gauge
	
	rowsBtwInc = (length//(incCount//2))*2 #assumes inc on either side each time # *2 since half gauge
	print('rowsBtwInc:', rowsBtwInc) #remove

	wasteSection(k, leftN=leftN, rightN=rightN, wasteC=mainC, drawC=drawC, otherCs=[borderC], endOnRight=[mainC], gauge=gauge)

	k.outcarrier(drawC)

	closedTubeCaston(k, startN=rightN, endN=leftN, c=mainC, gauge=gauge)

	k.pause(f'{rowsBtwInc} rows btw inc') #remove #?

	#knit 6 rows
	circular(k, startN=leftN, endN=rightN, length=6, c=mainC, gauge=gauge)

	leftoverTwistedStitches = []

	prevRowsBtwInc = rowsBtwInc

	borderStartN = leftN #starts on left
	borderEndN = rightN
	borderStartLeft = True
	borderWidth = endWidth-startWidth+6 #not //2 bc half gauge, so would be *2 anyway #+6 for extra
	toDrop = []
	offLimits = []

	def shiftBorder(startN, endN, startLeft, borderWidth): #returns new borderStartN, borderEndN
		if startLeft: mult = -1
		else: mult = 1
		dropN = startN

		for y in range(0, 2):
			for n in range(1, gauge+1):
				if dropWaste and (dropN+(mult*n)) % gauge == 0: k.drop(f'f{dropN+(mult*n)}')
			for n in range(1, gauge+1):
				if dropWaste and (gauge == 1 or (dropN+(mult*n)) % gauge != 0): k.drop(f'b{dropN+(mult*n)}')
			if tuckForBothSides: break
			else:
				mult *= -1
				dropN = endN
		
		borderWidth -= gauge #only here
		if startLeft: #startLeft if inc on left
			startN -= gauge
			if not tuckForBothSides and not onlyLeft: endN += gauge #remove #? 
		else:
			if not onlyLeft: startN += gauge
			if not tuckForBothSides: endN -= gauge #remove #? #go back! #?

		return endN, startN, borderWidth
	
	skipInc = True
	onlyLeft = False
	leftTwistedStitches = None
	rightTwistedStitches = None

	for r in range(0, length):
		if r == length-1: dropWaste = True
		emptyNeedles = []

		if not onlyLeft and (rightN-leftN)+1 == endWidth: skipInc = True
		elif (r == length-1 and (rightN-leftN)+1 < endWidth) or (r == length-2 and gradualSplit and (rightN-leftN)+1 < endWidth): #so one extra
			onlyLeft = True
		if onlyLeft: skipInc = False

		twistedStitches = []

		if r > 0 and (r % rowsBtwInc == 0 or (onlyLeft and (rightN-leftN)+1 < endWidth)): #inc on left side
			for n in toDrop:
				k.drop(n)
			toDrop = []

			if tuckForBothSides: lastTime = False
			else: lastTime = (r==length-1) #TODO: move this up #?
			# else: lastTime = onlyLeft

			offLimits = []
			for n in range(0, 3):
				offLimits.append(f'f{leftN-n}')
				offLimits.append(f'b{leftN-n}')
				offLimits.append(f'f{rightN+n}')
				offLimits.append(f'b{rightN+n}')
			
			toDrop = wasteBorder(k, borderStartN, borderEndN, rowsBtwInc, c=borderC, widthL=borderWidth, widthR=borderWidth, gauge=2, offLimits=offLimits, firstTime=(r==rowsBtwInc), lastTime=lastTime)

			if onlyLeft: #TODO: add this to shapeImg*-border
				needle1 = borderEndN+borderWidth
				needle2 = borderEndN+borderWidth+1
				if needle1 % 2 == 0:
					needle1 = f'f{needle1}'
					needle2 = f'b{needle2}'
				else:
					needle1 = f'b{needle1}'
					needle2 = f'f{needle2}'
				toDrop.extend([needle1, needle2])

			borderStartN, borderEndN, borderWidth = shiftBorder(borderStartN, borderEndN, borderStartLeft, borderWidth)
			borderStartLeft = not borderStartLeft

			if not skipInc:
				if tuckOverSplit:
					leftN, leftTwistedStitches = incDoubleBed(k, count=1, edgeNeedle=leftN, c=mainC, side='l', gauge=gauge, incMethod=incMethod, splitType='gradual')

					if leftN % 2 == 0: k.knit('+', f'f{leftN}', mainC) #remove #? v
					else: k.knit('+', f'b{leftN}', mainC)

					if not borderStartLeft:
						toDrop.extend(wasteBorder(k, borderStartN, borderEndN, c=borderC, widthL=rowsBtwInc, widthR=rowsBtwInc, gauge=2, offLimits=offLimits, justTuck=True, shift=1))
					tuckOverDrop = k.tuckOverSplit(borderC, '+')
					toDrop.extend(tuckOverDrop)
					leftN, leftTwistedStitches = incDoubleBed(k, count=1, edgeNeedle=leftN, c=mainC, side='l', gauge=gauge, incMethod=incMethod, splitType='gradual')
					if not borderStartLeft:
						tuckOverDrop.extend(offLimits)
						toDrop.extend(wasteBorder(k, borderEndN, borderStartN, c=borderC, widthL=rowsBtwInc, widthR=rowsBtwInc, gauge=2, offLimits=tuckOverDrop, justTuck=True))
				else: leftN, leftTwistedStitches = incDoubleBed(k, count=1, edgeNeedle=leftN, c=mainC, side='l', gauge=gauge, incMethod=incMethod, splitType=splitType)

				if gradualSplit:
					if leftN % 2 == 0 and posBed == 'b': k.knit('+', f'f{leftN}', mainC)
					elif leftN % 2 != 0 and posBed == 'f': k.knit('+', f'b{leftN}', mainC)

			if leftTwistedStitches is not None: twistedStitches.extend(leftTwistedStitches)
		elif gradualSplit and not skipInc and ((r-1) % rowsBtwInc == 0 or onlyLeft): #skipInc already if r == 0
			toDrop.extend(wasteBorder(k, borderStartN, borderEndN, c=borderC, widthL=rowsBtwInc, widthR=rowsBtwInc, gauge=2, offLimits=offLimits, justTuck=True, shift=1))
			toDrop.extend(k.tuckOverSplit(borderC, '-', 1))
			borderStartN, borderEndN = borderEndN, borderStartN
			borderStartLeft = not borderStartLeft

			leftN, leftTwistedStitches = incDoubleBed(k, count=1, edgeNeedle=leftN, c=mainC, side='l', gauge=gauge, incMethod=incMethod, splitType='gradual')
		
		knitPass(k, startN=leftN, endN=rightN, c=mainC, bed=posBed, gauge=gauge, emptyNeedles=emptyNeedles) #pos pass

		if onlyLeft: skipInc = True

		if r > 0 and r % rowsBtwInc == 0: #inc on right side
			if tuckForBothSides: #remove #?
				# for n in toDrop:
				for n in sortBedNeedles(toDrop):
					k.drop(n)
				toDrop = []

				toDrop = wasteBorder(k, borderStartN, borderEndN, c=borderC, widthL=borderWidth, widthR=rowsBtwInc, gauge=2, offLimits=[f'f{leftN}', f'b{leftN}', f'f{rightN}', f'b{rightN}'], firstTime=False, lastTime=((length-r) <= rowsBtwInc))

				borderStartN, borderEndN = shiftBorder(borderStartN, borderEndN, borderStartLeft)
				borderStartLeft = not borderStartLeft
			
			if not skipInc:
				if tuckOverSplit:
					rightN, rightTwistedStitches = incDoubleBed(k, count=1, edgeNeedle=rightN, c=mainC, side='r', gauge=gauge, incMethod=incMethod, splitType='gradual') #inc 1 on right

					if rightN % 2 == 0: k.knit('-', f'f{rightN}', mainC) #remove #? v
					else: k.knit('-', f'b{rightN}', mainC)

					if borderStartLeft:
						toDrop.extend(wasteBorder(k, borderStartN, borderEndN, c=borderC, widthL=rowsBtwInc, widthR=rowsBtwInc, gauge=2, offLimits=offLimits, justTuck=True, shift=1))
					tuckOverDrop = k.tuckOverSplit(borderC, '-')
					toDrop.extend(tuckOverDrop)
					rightN, rightTwistedStitches = incDoubleBed(k, count=1, edgeNeedle=rightN, c=mainC, side='r', gauge=gauge, incMethod=incMethod, splitType='gradual') #inc 1 on right
					if borderStartLeft:
						tuckOverDrop.extend(offLimits)
						toDrop.extend(wasteBorder(k, borderEndN, borderStartN, c=borderC, widthL=rowsBtwInc, widthR=rowsBtwInc, gauge=2, offLimits=tuckOverDrop, justTuck=True))
				else: rightN, rightTwistedStitches = incDoubleBed(k, count=1, edgeNeedle=rightN, c=mainC, side='r', gauge=gauge, incMethod=incMethod, splitType=splitType) #inc 1 on right

				if gradualSplit:
					if rightN % 2 == 0 and negBed == 'b': k.knit('-', f'f{rightN}', mainC)
					elif rightN % 2 != 0 and negBed == 'f': k.knit('-', f'b{rightN}', mainC)

			prevRowsBtwInc = rowsBtwInc

			if rightTwistedStitches is not None: twistedStitches.extend(rightTwistedStitches)
		elif gradualSplit and not skipInc and (r-1) % rowsBtwInc == 0: #skipInc already if r == 0
			rightN, rightTwistedStitches = incDoubleBed(k, count=1, edgeNeedle=rightN, c=mainC, side='r', gauge=gauge, incMethod=incMethod, splitType='gradual') #inc 1 on right

		knitPass(k, startN=rightN, endN=leftN, c=mainC, bed=negBed, gauge=gauge, emptyNeedles=emptyNeedles) #neg pass

		if len(leftoverTwistedStitches): k.twist(leftoverTwistedStitches, -rollerAdvance)

		if r % rowsBtwInc == 0 and len(twistedStitches):
			leftoverTwistedStitches = k.twist(twistedStitches, -rollerAdvance)

		if (r == 0 and not gradualSplit) or r == 1: skipInc = False #new #check

	print('final width:', rightN-leftN+1) #remove
	#knit 6 rows
	circular(k, startN=leftN, endN=rightN, length=6, c=mainC, gauge=gauge)

	dropFinish(k, frontNeedleRanges=[leftN, rightN], backNeedleRanges=[leftN, rightN], carriers=[mainC, borderC])
