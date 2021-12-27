<h1 align="center">laser_post</h1>

## FreeCAD Path post processor for laser control.

This post processor outputs gcode for laser control, it should work  
with most gcode lasers.

Defaults:  
- Z axis moves are removed  
- M5 is added before all rapid moves  
- M3 S##### is added before each group of motion controlled moves.

The following command line options have been added:

--laser-on Overrides the defalt "M3" command for laser on.

--laser-no-s Suppresses the "S" word after the on command.

--laser-off Overrides the default "M5" command for laser off.

--laser-3d Allows Z moves but only turns the laser on if there is motion in X Y.  
    So this can be used to cut over contours or step up or down between cuts.
  
  Use ";" for newlines.  

**Examples :**
<pre>
  My laser max power setting is 1000 so if spindle speed is set
  at 900 that gives me 90%.
  
  Default output would be:
    M3 S900  for laser on
    M5  for laser off
  
  --laser-on="M4" would produce:
       M4 S900
       
  --laser-no-s --laser-on="Turn on;100%" would produce:
       Turn on
       100%
</pre>  

**Installation :**
  
* Copy **laser_post.py** to your macro directory
* Select the laser post processor in your [Path job](https://wiki.freecad.org/Path_Job).

## License
LGPL v2.1 [License](LICENSE)
