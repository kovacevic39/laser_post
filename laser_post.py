
# ***************************************************************************
# *   Copyright (c) 2014 sliptonic <shopinthewoods@gmail.com>               *
# *   Copyright (c) 2021 Mark Riem <mriem667@gmail.com>                     *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD
from FreeCAD import Units
import Path
import argparse
import datetime
import shlex
import Path.Post.Utils as PostUtils
import PathScripts.PathUtils as PathUtils
from builtins import open as pyopen
import re

TOOLTIP = """
This is a postprocessor file for the Path workbench. Generate g-code that is compatible with a laser.
"""

now = datetime.datetime.now()

parser = argparse.ArgumentParser(prog="laser", add_help=False)
parser.add_argument("--no-header", action="store_true", help="suppress header output")
parser.add_argument("--no-comments", action="store_true", help="suppress comment output")
parser.add_argument("--line-numbers", action="store_true", help="prefix with line numbers")
parser.add_argument(
    "--no-show-editor",
    action="store_true",
    help="don't pop up editor before writing output",
)
parser.add_argument("--precision", default="3", help="number of digits of precision, default=3")
parser.add_argument(
    "--preamble",
    help='set commands to be issued before the first command, default="G17\nG90"',
)
parser.add_argument(
    "--postamble",
    help='set commands to be issued after the last command, default="M05\nG17 G90\nM2"',
)
parser.add_argument(
    "--inches", action="store_true", help="Convert output for US imperial mode (G20)"
)
parser.add_argument(
    "--modal",
    action="store_true",
    help="Output the Same G-command Name USE NonModal Mode",
)
parser.add_argument("--axis-modal", action="store_true", help="Output the Same Axis Value Mode")
parser.add_argument(
    "--no-tlo",
    action="store_true",
    help="suppress tool length offset (G43) following tool changes",
)

parser.add_argument(
    "--laser-on",
    help="Command to turn laser on, use \\n for newline.Default is M3",
)

parser.add_argument(
    "--laser-off",
    help="Command to turn laser on, use \\n for newline.Default is M5",
)

parser.add_argument(
    "--laser-power",
    help='"Laser power command, use \\n for newline.Default is spindle speed "S####"Use "NONE" or "" to suppress any power commands.',
)

TOOLTIP_ARGS = parser.format_help()

# These globals set common customization preferences
OUTPUT_COMMENTS = True
OUTPUT_HEADER = True
OUTPUT_LINE_NUMBERS = False
SHOW_EDITOR = True
MODAL = False  # if true commands are suppressed if the same as previous line.
USE_TLO = True  # if true G43 will be output following tool changes
OUTPUT_DOUBLES = True  # if false duplicate axis values are suppressed if the same as previous line.
COMMAND_SPACE = " "
LINENR = 100  # line number starting value

# These globals will be reflected in the Machine configuration of the project
UNITS = "G21"  # G21 for metric, G20 for us standard
UNIT_SPEED_FORMAT = "mm/min"
UNIT_FORMAT = "mm"

MACHINE_NAME = "LinuxCNC"
CORNER_MIN = {"x": 0, "y": 0, "z": 0}
CORNER_MAX = {"x": 500, "y": 300, "z": 300}
PRECISION = 3

# Preamble text will appear at the beginning of the GCODE output file.
PREAMBLE = "G17 G90"

# Postamble text will appear following the last operation.
POSTAMBLE = "M5\nG17 G90\nM2"

# Pre operation text will be inserted before every operation
PRE_OPERATION = """"""

# Post operation text will be inserted after every operation
POST_OPERATION = """"""

# Tool Change commands will be inserted before a tool change
TOOL_CHANGE = """"""

LASER_ON = "M3"
LASER_OFF = "M5"
LASER_POWER = "S0"
PRINT_LINE_NUMBERS = False

def processArguments(argstring):
    global OUTPUT_HEADER
    global OUTPUT_COMMENTS
    global OUTPUT_LINE_NUMBERS
    global SHOW_EDITOR
    global PRECISION
    global PREAMBLE
    global POSTAMBLE
    global UNITS
    global UNIT_SPEED_FORMAT
    global UNIT_FORMAT
    global MODAL
    global USE_TLO
    global OUTPUT_DOUBLES
    global LASER_ON
    global LASER_OFF
    global LASER_POWER
    global PRINT_LINE_NUMBERS

    try:
        args = parser.parse_args(shlex.split(argstring))
        if args.no_header:
            OUTPUT_HEADER = False
        if args.no_comments:
            OUTPUT_COMMENTS = False
        if args.line_numbers:
            PRINT_LINE_NUMBERS = True
        if args.no_show_editor:
            SHOW_EDITOR = False
        print("Show editor = %d" % SHOW_EDITOR)
        PRECISION = args.precision
        #if args.preamble is not None:
         #   PREAMBLE = args.preamble
        #if args.postamble is not None:
         #   POSTAMBLE = args.postamble
        if args.inches:
            UNITS = "G20"
            UNIT_SPEED_FORMAT = "in/min"
            UNIT_FORMAT = "in"
            PRECISION = 4
        if args.modal:
            MODAL = True
        if args.no_tlo:
            USE_TLO = False
        if args.axis_modal:
            print("here")
            OUTPUT_DOUBLES = False

        if args.preamble is not None:
            #new_argstring += "--preamble TOP_MARKER "
            #PREAMBLE = "TOP_MARKER" + args.preamble
            PREAMBLE = args.preamble.replace("\\n", '\n')

        if args.postamble is not None:
            #new_argstring += "--postamble BOTTOM_MARKER "
            #POSTAMBLE = "BOTTOM_MARKER" + args.preamble
            POSTAMBLE = args.postamble.replace("\\n", '\n')

        if args.laser_on is not None:
            LASER_ON = args.laser_on.replace("\\n", '\n')

        if args.laser_off is not None:
            LASER_OFF = args.laser_off.replace("\\n", '\n')

        if args.laser_power is not None:
            LASER_POWER = args.laser_power.replace("NONE", "")
            LASER_POWER = args.laser_power.replace("\\n", '\n')

    except Exception:
        return False

    return True

def printlinenumbers():

    global LINENR

    if PRINT_LINE_NUMBERS is True:
        LINENR += 10
        return "N" + str(LINENR) + " "
    return ""

def laser_gcode(gcode):

    global LASER_ON
    global LASER_OFF
    global LASER_POWER
    global PRINT_LINE_NUMBERS

    nl = "\n"
    laser_gcode = ""
    prev_line = ""
    temp_gcode = ""
    cur_state = {"LASER":"ON", "G":"","X":"", "Y":"", "Z":"", "F":""}
    prev_state = {"LASER":"ON", "G":"NULL", "X":"NULL", "Y":"NULL", "Z":"NULL", "F":"NULL"}
    g_word = x_word = y_word = z_word = i_word = j_word = f_word = ""

    #   Format imported postprocessor gcode.

    for line in gcode.splitlines(True):

        temp_line = ""

        if "(" in line:             #just print comments if included
            if "linuxcnc" in line:  #replace the imported postprocessor name with ours
                line = line.replace("linuxcnc", "laser")
            temp_gcode += line
            continue

    #   Store spindle speed for laser power if no command line arg has changed it.

        if "S" in line and "(" not in line and ")" not in line and LASER_POWER == "S0":
            LASER_POWER = (re.search(r"S.*?(?=\s)", line)).group()

    #   Remove unwanted commands.

        if "M3 " in line or "M6 " in line or "G43 " in line:
            continue

    #   Make sure laser off command matches LASER_OFF

        if "M5\n" in line or "M5 " in line:
            line = line.replace("M5", LASER_OFF)

    #   Print custom preamble and postamble

        #if "TOP_MARKER" in line:
            #temp_gcode += f'{variables["PREAMBLE"]}{nl}'
            #continue

        #if "BOTTOM_MARKER" in line:
            #temp_gcode += f'{variables["POSTAMBLE"]}{nl}'
            #continue

    #   Store relevant values.

        if "G" in line:
            cur_state["G"] = (re.search(r"G.*?(?=\s)", line)).group()
            g_word = f'{cur_state["G"]} '

        if "X" in line:
            cur_state["X"] = (re.search(r"X.*?(?=\s)", line)).group()
            x_word = f'{cur_state["X"]} '

        if "Y" in line:
            cur_state["Y"] = (re.search(r"Y.*?(?=\s)", line)).group()
            y_word = f'{cur_state["Y"]} '

        if "Z" in line:
            cur_state["Z"] = (re.search(r"Z.*?(?=\s)", line)).group()
            z_word = f'{cur_state["Z"]} '

        if "I" in line:
            i_word = (re.search(r"I.*?(?=\s)", line)).group() + " "

        if "J" in line:
            j_word = (re.search(r"J.*?(?=\s)", line)).group() + " "

        if "F" in line:
            cur_state["F"] = (re.search(r"F.*?(?=\s)", line)).group()
            f_word = f'{cur_state["F"]} '

    #   Feedrate semi-modal. Freedrate is printed at the beginning of each motion controlled group.

        if  cur_state["F"] == prev_state["F"] and prev_state["G"] != "G0":
            f_word = ""

    #   Remove redundant moves created when ignoring the Z axis.

        if "G0 " in line and prev_state["G"] in ["G0", "G1", "G2", "G3"]\
            and cur_state["X"] == prev_state["X"] and cur_state["Y"] == prev_state["Y"]:
                continue

        elif "G1 " in line and prev_state["G"] in ["G0", "G1", "G2", "G3"]\
            and cur_state["X"] == prev_state["X"] and cur_state["Y"] == prev_state["Y"]:
                continue

    #   Remove G0 moves that only include the Z axis.

        elif "G0 " in line and "Z" in line and "X" not in line and "Y" not in line:
            continue

    #   Turn the laser on for feed controlled moves and off for rapid moves.
    #   This code could be more compact, but I chose to avoid any nesting
    #   to keep it easy to follow.

        elif "G0 " in line and cur_state["LASER"] == "OFF":
            temp_line += f"{g_word}{x_word}{y_word}{nl}"

        elif "G0 " in line and cur_state["LASER"] == "ON":
            cur_state["LASER"] = "OFF"                      #turn laser off
            temp_line += f'{LASER_OFF}{nl}'    #print laser off command
            temp_line += f"{g_word}{x_word}{y_word}{nl}"    #print gcode line

        elif "G1 " in line and cur_state["LASER"] == "ON":
            temp_line += f"{g_word}{x_word}{y_word}{f_word}{nl}"

        elif "G1 " in line and cur_state["LASER"] == "OFF":
            cur_state["LASER"] = "ON"
            temp_line += f'{LASER_ON} {LASER_POWER}{nl}'
            temp_line += f"{g_word}{x_word}{y_word}{f_word}{nl}"

        elif "G2 " in line or "G3 " in line and cur_state["LASER"] == "ON":
            temp_line += f"{g_word}{x_word}{y_word}{i_word}{j_word}{f_word}{nl}"

        elif "G2 " in line or "G3 " in line and cur_state["LASER"] == "OFF":
            cur_state["LASER"] = "ON"
            temp_line += f'{LASER_ON} {LASER_POWER}{nl}'
            temp_line += f"{g_word}{x_word}{y_word}{i_word}{j_word}{f_word}{nl}"

        else:
            temp_line = line

        temp_line = temp_line.replace(" \n", "\n")  #remove any trailing white space

        if temp_line == prev_line:  #remove duplicate lines
            continue

        else:

            prev_state = cur_state.copy()
            prev_line = temp_line
            temp_gcode += temp_line

    if PRINT_LINE_NUMBERS:

        for line in temp_gcode.splitlines(True):

            laser_gcode += printlinenumbers() + line
    else:
        laser_gcode = temp_gcode

    return laser_gcode


def export(objectslist, filename, argstring):
    if not processArguments(argstring):
        return None
    global UNITS
    global UNIT_FORMAT
    global UNIT_SPEED_FORMAT

    for obj in objectslist:
        if not hasattr(obj, "Path"):
            print(
                "the object " + obj.Name + " is not a path. Please select only path and Compounds."
            )
            return None

    print("postprocessing...")
    gcode = ""

    # write header
    if OUTPUT_HEADER:
        gcode += linenumber() + "(Exported by FreeCAD)\n"
        gcode += linenumber() + "(Post Processor: " + __name__ + ")\n"
        gcode += linenumber() + "(Output Time:" + str(now) + ")\n"

    # Write the preamble
    if OUTPUT_COMMENTS:
        gcode += linenumber() + "(begin preamble)\n"
    for line in PREAMBLE.splitlines(False):
        gcode += linenumber() + line + "\n"
    gcode += linenumber() + UNITS + "\n"

    for obj in objectslist:

        # Skip inactive operations
        if hasattr(obj, "Active"):
            if not obj.Active:
                continue
        if hasattr(obj, "Base") and hasattr(obj.Base, "Active"):
            if not obj.Base.Active:
                continue

        # do the pre_op
        if OUTPUT_COMMENTS:
            gcode += linenumber() + "(begin operation: %s)\n" % obj.Label
            gcode += linenumber() + "(machine units: %s)\n" % (UNIT_SPEED_FORMAT)
        for line in PRE_OPERATION.splitlines(True):
            gcode += linenumber() + line

        # get coolant mode
        coolantMode = "None"
        if hasattr(obj, "CoolantMode") or hasattr(obj, "Base") and hasattr(obj.Base, "CoolantMode"):
            if hasattr(obj, "CoolantMode"):
                coolantMode = obj.CoolantMode
            else:
                coolantMode = obj.Base.CoolantMode

        # turn coolant on if required
        if OUTPUT_COMMENTS:
            if not coolantMode == "None":
                gcode += linenumber() + "(Coolant On:" + coolantMode + ")\n"
        if coolantMode == "Flood":
            gcode += linenumber() + "M8" + "\n"
        if coolantMode == "Mist":
            gcode += linenumber() + "M7" + "\n"

        # process the operation gcode
        gcode += parse(obj)

        # do the post_op
        if OUTPUT_COMMENTS:
            gcode += linenumber() + "(finish operation: %s)\n" % obj.Label
        for line in POST_OPERATION.splitlines(True):
            gcode += linenumber() + line

        # turn coolant off if required
        if not coolantMode == "None":
            if OUTPUT_COMMENTS:
                gcode += linenumber() + "(Coolant Off:" + coolantMode + ")\n"
            gcode += linenumber() + "M9" + "\n"

    # do the post_amble
    if OUTPUT_COMMENTS:
        gcode += "(begin postamble)\n"
    for line in POSTAMBLE.splitlines(True):
        gcode += linenumber() + line
    
    # format gcode for laser
    gcode = laser_gcode(gcode)

    if FreeCAD.GuiUp and SHOW_EDITOR:
        final = gcode
        if len(gcode) > 100000:
            print("Skipping editor since output is greater than 100kb")
        else:
            dia = PostUtils.GCodeEditorDialog()
            dia.editor.setText(gcode)
            result = dia.exec_()
            if result:
                final = dia.editor.toPlainText()
    else:
        final = gcode

    print("done postprocessing.")

    if not filename == "-":
        gfile = pyopen(filename, "w")
        gfile.write(final)
        gfile.close()

    return final


def linenumber():
    global LINENR
    if OUTPUT_LINE_NUMBERS is True:
        LINENR += 10
        return "N" + str(LINENR) + " "
    return ""


def parse(pathobj):
    global PRECISION
    global MODAL
    global OUTPUT_DOUBLES
    global UNIT_FORMAT
    global UNIT_SPEED_FORMAT

    out = ""
    lastcommand = None
    precision_string = "." + str(PRECISION) + "f"
    currLocation = {}  # keep track for no doubles

    # the order of parameters
    # linuxcnc doesn't want K properties on XY plane  Arcs need work.
    params = [
        "X",
        "Y",
        "Z",
        "A",
        "B",
        "C",
        "I",
        "J",
        "F",
        "S",
        "T",
        "Q",
        "R",
        "L",
        "H",
        "D",
        "P",
    ]
    firstmove = Path.Command("G0", {"X": -1, "Y": -1, "Z": -1, "F": 0.0})
    currLocation.update(firstmove.Parameters)  # set First location Parameters

    if hasattr(pathobj, "Group"):  # We have a compound or project.
        # if OUTPUT_COMMENTS:
        #     out += linenumber() + "(compound: " + pathobj.Label + ")\n"
        for p in pathobj.Group:
            out += parse(p)
        return out
    else:  # parsing simple path

        # groups might contain non-path things like stock.
        if not hasattr(pathobj, "Path"):
            return out

        # if OUTPUT_COMMENTS:
        #     out += linenumber() + "(" + pathobj.Label + ")\n"

        # The following "for" statement was fairly recently added
        # but seems to be using the A, B, and C parameters in ways
        # that don't appear to be compatible with how the PATH code
        # uses the A, B, and C parameters.  I have reverted the
        # change here until we can figure out what it going on.
        #
        # for c in PathUtils.getPathWithPlacement(pathobj).Commands:
        for c in pathobj.Path.Commands:

            outstring = []
            command = c.Name
            outstring.append(command)

            # if modal: suppress the command if it is the same as the last one
            if MODAL is True:
                if command == lastcommand:
                    outstring.pop(0)

            if c.Name[0] == "(" and not OUTPUT_COMMENTS:  # command is a comment
                continue

            # Now add the remaining parameters in order
            for param in params:
                if param in c.Parameters:
                    if param == "F" and (
                        currLocation[param] != c.Parameters[param] or OUTPUT_DOUBLES
                    ):
                        if c.Name not in [
                            "G0",
                            "G00",
                        ]:  # linuxcnc doesn't use rapid speeds
                            speed = Units.Quantity(c.Parameters["F"], FreeCAD.Units.Velocity)
                            if speed.getValueAs(UNIT_SPEED_FORMAT) > 0.0:
                                outstring.append(
                                    param
                                    + format(
                                        float(speed.getValueAs(UNIT_SPEED_FORMAT)),
                                        precision_string,
                                    )
                                )
                        else:
                            continue
                    elif param == "T":
                        outstring.append(param + str(int(c.Parameters["T"])))
                    elif param == "H":
                        outstring.append(param + str(int(c.Parameters["H"])))
                    elif param == "D":
                        outstring.append(param + str(int(c.Parameters["D"])))
                    elif param == "S":
                        outstring.append(param + str(int(c.Parameters["S"])))
                    else:
                        if (
                            (not OUTPUT_DOUBLES)
                            and (param in currLocation)
                            and (currLocation[param] == c.Parameters[param])
                        ):
                            continue
                        else:
                            if param in ("A", "B", "C"):
                                outstring.append(
                                    param + format(float(c.Parameters[param]), precision_string)
                                )
                            else:
                                pos = Units.Quantity(c.Parameters[param], FreeCAD.Units.Length)
                                outstring.append(
                                    param
                                    + format(float(pos.getValueAs(UNIT_FORMAT)), precision_string)
                                )

            # store the latest command
            lastcommand = command
            currLocation.update(c.Parameters)

            # Check for Tool Change:
            if command == "M6":
                # stop the spindle
                out += linenumber() + "M5\n"
                for line in TOOL_CHANGE.splitlines(True):
                    out += linenumber() + line

                # add height offset
                if USE_TLO:
                    tool_height = "\nG43 H" + str(int(c.Parameters["T"]))
                    outstring.append(tool_height)

            if command == "message":
                if OUTPUT_COMMENTS is False:
                    out = []
                else:
                    outstring.pop(0)  # remove the command

            # prepend a line number and append a newline
            if len(outstring) >= 1:
                if OUTPUT_LINE_NUMBERS:
                    outstring.insert(0, (linenumber()))

                # append the line to the final output
                for w in outstring:
                    out += w + COMMAND_SPACE
                # Note: Do *not* strip `out`, since that forces the allocation
                # of a contiguous string & thus quadratic complexity.
                out += "\n"

        return out


# print(__name__ + " gcode postprocessor loaded.")
