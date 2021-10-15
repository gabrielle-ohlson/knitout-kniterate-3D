# from lib import knitout, knit3D
from knitout_kniterate_3D import knit3D, knitout

k = knitout.Writer('1 2 3 4 5 6')

fileName = 'donut-gripper-demo'
imagePath = '../graphics/donut-gripper-demo.png'

stitchPatImgPathF = '../graphics/stitch-patterns/donut-gripper-st-demo.png'

stitchPatternsF = { 'garter': ['green', 'purple'], 'rib': 'red', 'jersey': ['blue', 'yellow'] }

colorArgsF = {'green': {'patternRows': 4, 'passes': 2}, 'purple': {'patternRows': 4, 'passes': 2}, 'red': {'sequence': 'fb'}, 'blue': {'extensions': {'stitchNumber': 6}}, 'yellow': {'extensions': {'stitchNumber': 6}}}


stitchPatImgPathB = '../graphics/stitch-patterns/donut-gripper-st-demo.png'

stitchPatternsB = { 'garter': ['green', 'purple'], 'rib': 'red', 'jersey': ['blue', 'yellow'] }

colorArgsB = {'green': {'patternRows': 4}, 'purple': {'patternRows': 4}, 'red': {'sequence': 'fb'}, 'blue': {'extensions': {'stitchNumber': 6}}, 'yellow': {'extensions': {'stitchNumber': 6}}}


knit3D.shapeImgToKnitout(k, imagePath=imagePath, gauge=2, maxShortrowCount=4, addBindoff=False, excludeCarriers=['4'], addBorder=True, stitchPatternsFront={'imgPath': stitchPatImgPathF, 'patterns': stitchPatternsF, 'colorArgs': colorArgsF}, stitchPatternsBack={'imgPath': stitchPatImgPathB, 'patterns': stitchPatternsB, 'colorArgs': colorArgsB})


k.write(f'{fileName}.k')