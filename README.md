<h1 align="center">laser_post</h1>

## FreeCAD Path post processor for laser control.

This post processor outputs gcode for laser control, it should work  
with most gcode lasers.

**Defaults:**  
- Z axis moves are removed  
- M5 is added before all rapid moves  
- M3 S##### is added before each group of motion controlled moves.

The following command line options have been added:

<code>--laser-off</code> Overrides the default "M5" command for laser off.

<code>--laser-on</code> Overrides the default "M3" command for laser on.

<code>--laser-power</code> Overrides the default "S####" command for laser on.
--laser-power "" or --laser-power "NONE" suppresses the power command.
  
  Use "\n" for newlines.

**Examples :**
<pre>
  My laser max power setting is 1000 so if spindle speed is set
  at 900 that gives me 90%.
  
  Default output would be:
    M3 S900  for laser on
    M5  for laser off
  
  --laser-on "M4" would produce:
       M4 S900
       
  --laser-power "NONE" --laser-on "M4" would produce:
       M4

  --laser-on "G4 P1\nM3" --laser-power "\nfull power" would produce:
       G4 P1
       M3
       full power

</pre>  

**Installation :**

* Copy **laser_post.py** to your macro directory
* Select the laser post processor in your [Path job](https://wiki.freecad.org/Path_Job).

## License
LGPL v2.1 [License](LICENSE)
