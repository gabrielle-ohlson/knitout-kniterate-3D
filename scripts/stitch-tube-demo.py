from lib import knitout, knit3D
# from knitout_kniterate_3D import knit3D, knitout

k = knitout.Writer('1 2 3 4 5 6')

fileName = 'stitch-tube-textures-3'

mainC = '1'
wasteC = '3'
drawC = '2'

gauge = 2

leftN = 0
rightN = 39
rows = 40

side = 'l'

# --- STITCH PATTERN TUBE FUNCTIONS ---

knit3D.setSettings(k=k, stitch=5, xferStitch=3, wasteStitch=5)

# --- debug ---
# knit3D.stitchPatternTube(k, leftN=leftN, rightN=rightN, c=mainC, wasteC=wasteC, drawC=drawC, featureCs=[wasteC, drawC], side='l', patterns=[
# 	# ['jersey', { 'plaiting': True }],
# 	# ['jersey', { 'extensions': {'stitchNumber': 3} }],
# 	# ['jersey', { 'extensions': {'stitchNumber': 4} }],
# 	# ['jersey', { 'extensions': {'stitchNumber': 5} }],
# 	# ['jersey', { 'extensions': {'stitchNumber': 6} }],
# 	# ['jersey', { 'extensions': {'stitchNumber': 'A'} }], #10
# 	['garter', {'patternRows': 1}],
# 	['garter', {'patternRows': 1}],
# 	['garter', {'patternRows': 1}],
# 	['garter', {'patternRows': 1}],
# 	['garter', {'patternRows': 1}],
# ], defaultLength=8, wasteDivider=True, wasteLength=10)
# ------------


knit3D.stitchPatternTube(k, leftN=leftN, rightN=rightN, c=mainC, wasteC=wasteC, drawC=drawC, featureCs=[wasteC, drawC], side='l', patterns=[
	# ['jersey', { 'plaiting': True }],
	# ['jersey', { 'extensions': {'stitchNumber': 3} }],
	# ['jersey', { 'extensions': {'stitchNumber': 4} }],
	# ['jersey', { 'extensions': {'stitchNumber': 5} }],
	# ['jersey', { 'extensions': {'stitchNumber': 6} }],
	# ['jersey', { 'extensions': {'stitchNumber': 8} }],
	# ['jersey', { 'extensions': {'stitchNumber': 'A'} }], #10
	# ['garter', {'patternRows': 1}],
	['garter', {'patternRows': 2}],
	['garter', {'patternRows': 3}],
	['garter', {'patternRows': 4}],
	['garter', {'patternRows': 6}],
	['garter', {'patternRows': 8}],
	['garter', {'patternRows': 10}],
	['rib', {'sequence': 'fb' } ], #1x1
	['rib', {'sequence': 'ffbb' } ], #2x2
	['rib', {'sequence': 'fffbbb' } ], #3x3
	['rib', {'sequence': 'ffffbbbb' } ], #4x4
	['rib', {'sequence': 'ffffffbbbbbb' } ], #6x6
	['rib', {'sequence': 'ffffffffbbbbbbbb' } ], #8x8
	['rib', {'sequence': 'ffffffffffbbbbbbbbbb' } ], #10x10
	'interlock',
	['jersey', { 'extensions': {'stitchNumber': 3} }]
], defaultLength=rows, wasteDivider=True, wasteLength=10)

# knit3D.stitchPatternTube(k, leftN=leftN, rightN=rightN, c=mainC, wasteC=wasteC, drawC=drawC, featureCs=[wasteC, drawC], side='l', patterns=[
# 	['jersey', { 'plaiting': True }],
# 	# ['jersey', { 'extensions': {'stitchNumber': 6, 'rollerAdvance': 600} }],
# 	['jersey', { 'extensions': {'stitchNumber': 5} }],
# 	['garter', {'patternRows': 3}],
# 	['rib', {'sequence': 'fb', 'extensions': {'stitchNumber': 8, 'rollerAdvance': 600} }, ],
# 	'interlock',
# 	['jersey', { 'extensions': {'stitchNumber': 3} }],
# 	['jersey', { 'extensions': {'stitchNumber': 2} }],
# ], defaultLength=rows, wasteDivider=True)

knit3D.dropFinish(k, frontNeedleRanges=[leftN, rightN], backNeedleRanges=[leftN, rightN], carriers=[mainC, drawC, wasteC], direction='+', borderC=wasteC)

k.write(f'{fileName}.k')