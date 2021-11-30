# from lib import knitout, knit3D
from knitout_kniterate_3D import knit3D, knitout
import os

cur_WD=os.getcwd()
k = knitout.Writer('1 2 3 4 5 6')

import os

working_dir = os.getcwd() #TODO: add to main knit3D

fileName = 'cactus-gripper-demo'
<<<<<<< HEAD
imagePath = working_dir + '/../graphics/cactus-gripper-demo.png'
=======
imagePath = cur_WD + '/graphics/cactus-gripper-demo.png'
>>>>>>> dc7c6157516087f2968e2420d97476440a1ad1fd

stitchPatImgPathF = cur_WD + '/graphics/stitch-patterns/cactus-gripper-st-demo.png'

stitchPatternsF = { 'jersey': ['yellow', 'red'], 'garter': ['orange', 'purple', 'green', 'fuchsia', 'blue'] }

colorArgsF = {'yellow': { 'features': {'plaiting': True} }, 'red': { 'features': {'plaiting': True} }, 'orange': {'patternRows': 2, 'passes': 1.5}, 'purple': {'patternRows': 2, 'passes': 1.5}, 'green': {'patternRows': 4, 'passes': 2}, 'blue': {'patternRows': 4, 'passes': 2}, 'pink': {'patternRows': 4, 'passes': 2}}


stitchPatImgPathB = cur_WD + '/graphics/stitch-patterns/cactus-gripper-st-demo.png'

stitchPatternsB = { 'jersey': ['yellow', 'red'], 'garter': ['orange', 'purple', 'green', 'fuchsia', 'blue'] }

colorArgsB = {'yellow': { 'features': {'plaiting': True} }, 'red': { 'features': {'plaiting': True} }, 'orange': {'patternRows': 2, 'passes': 1.5}, 'purple': {'patternRows': 2, 'passes': 1.5}, 'green': {'patternRows': 4, 'passes': 2}, 'blue': {'patternRows': 4, 'passes': 2}, 'pink': {'patternRows': 4, 'passes': 2}}

stitchsize = 4
knit3D.setSettings(roller=400,stitch = stitchsize)
knit3D.shapeImgToKnitout(k, imagePath=imagePath, gauge=2, maxShortrowCount=4, addBindoff=False, excludeCarriers=['4'], addBorder=True, stitchPatternsFront={'imgPath': stitchPatImgPathF, 'patterns': stitchPatternsF, 'colorArgs': colorArgsF}, stitchPatternsBack={'imgPath': stitchPatImgPathB, 'patterns': stitchPatternsB, 'colorArgs': colorArgsB})


k.write(f'{fileName}.k')
<<<<<<< HEAD


'''
import os

working_dir = os.getcwd()
'''
=======
>>>>>>> dc7c6157516087f2968e2420d97476440a1ad1fd
