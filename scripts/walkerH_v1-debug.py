# from lib import knitout, knit3D
from knitout_kniterate_3D import knit3D, knitout
import os

k = knitout.Writer('1 2 3 4 5 6')
cur_WD=os.getcwd()


fileName = 'walkerH_v1_2-1'
imagePath = cur_WD+ '/graphics/Walker_v1/WalkerH-v1-BW.png'


stitchPatImgPathF = cur_WD+ '/graphics/Walker_v1/WalkerH-v1-colors.png'

stitchPatternsF = {'garter': ['blue','red','green','yellow']}

colorArgsF = {'red': {'patternRows': 4, 'passes': 2},'blue': {'patternRows': 4, 'passes': 2},
    'green': {'patternRows': 4, 'passes': 2},'yellow': {'patternRows': 4, 'passes': 2}} #need to revisit- what does this mean


stitchPatImgPathB = cur_WD + '/graphics/Walker_v1/WalkerH-v1-colors.png'

stitchPatternsB = {'garter': ['blue','red','green','yellow']}

colorArgsB = {'red': {'patternRows': 4, 'passes': 2},'blue': {'patternRows': 4, 'passes': 2},
    'green': {'patternRows': 4, 'passes': 2},'yellow': {'patternRows': 4, 'passes': 2}}

stitchsize = 5
knit3D.setSettings(roller=500,stitch = stitchsize)


knit3D.shapeImgToKnitout(k, imagePath=imagePath, gauge=2, maxShortrowCount=4,
    addBindoff=False, excludeCarriers=['4','1','2'], addBorder=False,
    stitchPatternsFront={'imgPath': stitchPatImgPathF, 'patterns': stitchPatternsF, 'colorArgs': colorArgsF},
    stitchPatternsBack={'imgPath': stitchPatImgPathB, 'patterns': stitchPatternsB, 'colorArgs': colorArgsB})


k.write(f'{fileName}.k')
