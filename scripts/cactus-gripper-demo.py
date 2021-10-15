# from lib import knitout, knit3D
from knitout_kniterate_3D import knit3D, knitout

k = knitout.Writer('1 2 3 4 5 6')

fileName = 'cactus-gripper-demo'
imagePath = '../graphics/cactus-gripper-demo.png'

stitchPatImgPathF = '../graphics/stitch-patterns/cactus-gripper-st-demo.png'

stitchPatternsF = { 'jersey': ['yellow', 'red'], 'garter': ['orange', 'purple', 'green', 'fuchsia', 'blue'] }

colorArgsF = {'yellow': { 'features': {'plaiting': True} }, 'red': { 'features': {'plaiting': True} }, 'orange': {'patternRows': 2, 'passes': 1.5}, 'purple': {'patternRows': 2, 'passes': 1.5}, 'green': {'patternRows': 4, 'passes': 2}, 'blue': {'patternRows': 4, 'passes': 2}, 'pink': {'patternRows': 4, 'passes': 2}}


stitchPatImgPathB = '../graphics/stitch-patterns/cactus-gripper-st-demo.png'

stitchPatternsB = { 'jersey': ['yellow', 'red'], 'garter': ['orange', 'purple', 'green', 'fuchsia', 'blue'] }

colorArgsB = {'yellow': { 'features': {'plaiting': True} }, 'red': { 'features': {'plaiting': True} }, 'orange': {'patternRows': 2, 'passes': 1.5}, 'purple': {'patternRows': 2, 'passes': 1.5}, 'green': {'patternRows': 4, 'passes': 2}, 'blue': {'patternRows': 4, 'passes': 2}, 'pink': {'patternRows': 4, 'passes': 2}}


knit3D.shapeImgToKnitout(k, imagePath=imagePath, gauge=2, maxShortrowCount=4, addBindoff=False, excludeCarriers=['4'], addBorder=True, stitchPatternsFront={'imgPath': stitchPatImgPathF, 'patterns': stitchPatternsF, 'colorArgs': colorArgsF}, stitchPatternsBack={'imgPath': stitchPatImgPathB, 'patterns': stitchPatternsB, 'colorArgs': colorArgsB})


k.write(f'{fileName}.k')