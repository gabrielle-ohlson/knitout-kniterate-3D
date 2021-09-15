# knitout-kniterate-3D
Code for producing [knitout](github.com/textiles-lab/knitout) files to do 3D knitting on the [kniterate](kniterate.com) knitting machine (and also optionally adding stitch patterns along the 3D surface).

# Graphic Specifications
## Overview
The program uses 2D raster (or bitmap) graphics (with full opacity!) to generate knitout files for 3D shapes that can then be converted to knitting machine instructions in k-code using the [knitout-to-kniterate-backend](github.com/textiles-lab/knitout-backend-kniterate). It also allows for incorpating stitch patterns to overlay onto the shape graphic (kind of like a cookie cutter).

You can use adobe photoshop or [photopea](photopea.com) (a fantastic & free in-browser photoshop alternative) to create these graphics.

For all of these graphics, an individual pixel is mapped to an individual stitch (so the height and width of the graphic respectively determine the row and needle count of the resulting knitted object). If the stitch pattern graphic is a different size from the shape graphic, it will be resized to match the latter.

## 3D Shapes
The graphic that represents the shape should have a white background and a flat black fill as the shape. This graphic will be used for both the front and the back of the shape (currently, the program does not support variation in these).

## Stitch Patterns
Optionally, the shape can be composed of a variety stitch patterns at different points along its 3D surface. This is acheived by processing user-provided 2D raster graphics that include blobs of unique colors to designate an area where a particular stitch pattern should be used when knitting the given shape. The specifications of each stitch pattern are based on the info you pass as arguments to the `shapeImgToKnitout` function.\
(*NOTE:* no two blobs separated by any white space can be the same color, even if they represent the exact stitch patterns).\
Different stitch pattern graphics can be provided for the front and back of the shape.

# Function Parameters
## `shapeImgToKnitout`
TODO

# Workflow
Generate the graphics that you will be using for the knitted object. It is recommended that you place these graphics in the `graphics` sub-directory.\
Create a python file (e.g. `my-file.py`) in the `scripts` sub-directory and import the libraries by adding the following code to your file:
```
from lib import knit3D, knitout
```
(*NOTE:* the `lib.py` file makes it possible to import the relevant libraries located in the `src` folder directly from the `scripts` folder)

Then add the following code to initiate the knitout writer:
```
k = knitout.Writer('1 2 3 4 5 6')
```
Then, call the `shapeImgToKnitout` function from the `knit3D` library and pass any relevant information (see the function docstring in `knit3D.py` [located in the `src` sub-directory] for more information).
```
TODO
```
Finally, use the knitout writer to output the file:
```
k.write(f'{fileName}.k')
```