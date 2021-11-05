from lib import knitout, knit3D
# from knitout_kniterate_3D import knit3D, knitout

k = knitout.Writer('1 2 3 4 5 6')

fileName = 'stitch-tube'

mainC = '1'
wasteC = '3'
drawC = '2'

gauge = 2

leftN = 0
rightN = 39
rows = 40

side = 'l'

# --- STITCH PATTERN TUBE FUNCTIONS ---


knit3D.stitchPatternTube(k, leftN=leftN, rightN=rightN, c=mainC, wasteC=wasteC, drawC=drawC, featureCs=[wasteC, drawC], side='l', patterns=[
	['jersey', { 'plaiting': True }],
	# ['jersey', { 'extensions': {'stitchNumber': 6, 'rollerAdvance': 600} }],
	['jersey', { 'extensions': {'stitchNumber': 5} }],
	['garter', {'patternRows': 3}],
	['rib', {'sequence': 'fb', 'extensions': {'stitchNumber': 8, 'rollerAdvance': 600} }, ],
	'interlock',
	['jersey', { 'extensions': {'stitchNumber': 3} }],
	['jersey', { 'extensions': {'stitchNumber': 2} }],
], defaultLength=rows, wasteDivider=True)

knit3D.dropFinish(k, frontNeedleRanges=[leftN, rightN], backNeedleRanges=[leftN, rightN], carriers=[mainC, drawC, wasteC], direction='+', borderC=wasteC)

k.write(f'{fileName}.k')