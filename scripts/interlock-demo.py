from lib import knitout, knit3D
# from knitout_kniterate_3D import knit3D, knitout

k = knitout.Writer('1 2 3 4 5 6')

fileName = 'interlock-test'
imagePath = '../graphics/interlock-shape-demo.png'

stitchPatImgPathF = '../graphics/stitch-patterns/interlock-st-demo.png'

stitchPatternsF = { 'interlock': ['red', 'blue'] }

colorArgsF = {'red': {'gauge': 1}, 'blue': {'gauge': 1}}


stitchPatImgPathB = '../graphics/stitch-patterns/interlock-st-demo.png'

stitchPatternsB = { 'interlock': ['red', 'blue'] }

colorArgsB = {'red': {'gauge': 1}, 'blue': {'gauge': 1}}

knit3D.shapeImgToKnitout(k, imagePath=imagePath, gauge=2, maxShortrowCount=4, addBindoff=False, excludeCarriers=['4'], addBorder=False, stitchPatternsFront={'imgPath': stitchPatImgPathF, 'patterns': stitchPatternsF, 'colorArgs': colorArgsF}, stitchPatternsBack={'imgPath': stitchPatImgPathB, 'patterns': stitchPatternsB, 'colorArgs': colorArgsB})


k.write(f'{fileName}.k')
