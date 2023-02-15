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

from __future__ import print_function
import FreeCAD
from FreeCAD import Units
import Path
import argparse
import datetime
import shlex
from PathScripts import PostUtils
from PathScripts import PathUtils

TOOLTIP = '''
Generate g-code from a Path that is compatible with a laser.
import laser_post
laser_post.export(object, "/path/to/file.ncc")
'''
now = datetime.datetime.now()

parser = argparse.ArgumentParser(prog='laser', add_help=False)
parser.add_argument('--no-header', action='store_true', help='suppress header output')
parser.add_argument('--no-comments', action='store_true', help='suppress comment output')
parser.add_argument('--line-numbers', action='store_true', help='prefix with line numbers')
parser.add_argument('--no-show-editor', action='store_true', help='don\'t pop up editor before writing output')
parser.add_argument('--precision', default='3', help='number of digits of precision, default=3')
parser.add_argument('--preamble', help='set commands to be issued before the first command, ";" for newline')
parser.add_argument('--postamble', help='set commands to be issued after the last command, ";" for newline')
parser.add_argument('--inches', action='store_true', help='Convert output for US imperial mode (G20)')
parser.add_argument('--modal', action='store_true', help='If true, suppress command if the same as last command')
parser.add_argument('--feed-non-modal', action='store_true', help='If true, output "F" values for all non rapid moves')
parser.add_argument('--laser-3d', action='store_true', help='If --laser-3d is true format gcode for 3d laser.')
parser.add_argument('--laser-off', help='Command used to turn laser off, use ";" for newline, default="M5"')
parser.add_argument('--laser-on', help='Command used to turn laser on, use ";" for newline, default="M3"')
parser.add_argument('--no-s', action='store_true', help='Don\'t output "S" values speed(laser power)')
parser.add_argument('--output-k', action='store_true', help='Output "K" values, suppressed by default')

TOOLTIP_ARGS = parser.format_help()

# These globals set common customization preferences
OUTPUT_COMMENTS = True
OUTPUT_HEADER = True
OUTPUT_LINE_NUMBERS = False
SHOW_EDITOR = True
MODAL = False
FEED_NON_MODAL = False  # if true, output F value for all non rapid moves.
COMMAND_SPACE = " "
LINENR = 100  # line number starting value
LASER_3D = False
LASER_POWER = "" # Don't edit this, use --laser-on or S value in tool controller.
LASER_OFF = "M5"
LASER_ON = "M3"
NO_S = False
OUTPUT_K = False

# These globals will be reflected in the Machine configuration of the project
UNITS = "G21"  # G21 for metric, G20 for us standard
UNIT_SPEED_FORMAT = 'mm/min'
UNIT_FORMAT = 'mm'

PRECISION = 3

# Preamble text will appear at the beginning of the GCODE output file.
PREAMBLE = '''G17 G90
'''

# Postamble text will appear following the last operation.
POSTAMBLE = '''M5
M2
'''

# Pre operation text will be inserted before every operation
PRE_OPERATION = ''''''

# Post operation text will be inserted after every operation
POST_OPERATION = ''''''

# Tool Change commands will be inserted before a tool change
TOOL_CHANGE = ''''''

# to distinguish python built-in open function from the one declared below
if open.__module__ in ['__builtin__','io']:
    pythonopen = open


def processArguments(argstring):
    # pylint: disable=global-statement
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
    global FEED_NON_MODAL
    global LASER_3D
    global LASER_OFF
    global LASER_ON
    global NO_S
    global OUTPUT_K

    try:
        args = parser.parse_args(shlex.split(argstring))
        if args.no_header:
            OUTPUT_HEADER = False
        if args.no_comments:
            OUTPUT_COMMENTS = False
        if args.line_numbers:
            OUTPUT_LINE_NUMBERS = True
        if args.no_show_editor:
            SHOW_EDITOR = False
        print("Show editor = %d" % SHOW_EDITOR)
        PRECISION = args.precision
        if args.preamble is not None:
            PREAMBLE = args.preamble
        if args.postamble is not None:
            POSTAMBLE = args.postamble
        if args.inches:
            UNITS = 'G20'
            UNIT_SPEED_FORMAT = 'in/min'
            UNIT_FORMAT = 'in'
            PRECISION = 4
        if args.modal:
            MODAL = True
        if args.feed_non_modal:
            FEED_NON_MODAL = True
        if args.laser_3d:
            LASER_3D = True
        if args.laser_off is not None:
            LASER_OFF = args.laser_off
        if args.laser_on is not None:
            LASER_ON = args.laser_on
        if args.no_s:
            NO_S = True
        if args.output_k:
            OUTPUT_K = True

    except Exception: # pylint: disable=broad-except
        return False

    return True

def export(objectslist, filename, argstring):
    # pylint: disable=global-statement
    if not processArguments(argstring):
        return None
    global UNITS
    global UNIT_FORMAT
    global UNIT_SPEED_FORMAT
    global LASER_OFF
    global PREAMBLE
    global POSTAMBLE

    for obj in objectslist:
        if not hasattr(obj, "Path"):
            print("the object " + obj.Name + " is not a path. Please select only path and Compounds.")
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

    # Add newline functionality to the command line input box. ";" for newline.
    PREAMBLE = PREAMBLE.replace(";", "\n")
    for line in PREAMBLE.splitlines(False):
        gcode += linenumber() + line + "\n"
    gcode += linenumber() + UNITS + "\n"

    for obj in objectslist:

        # Skip inactive operations
        if hasattr(obj, 'Active'):
            if not obj.Active:
                continue
        if hasattr(obj, 'Base') and hasattr(obj.Base, 'Active'):
            if not obj.Base.Active:
                continue

        # do the pre_op
        if OUTPUT_COMMENTS:
            gcode += linenumber() + "(begin operation: %s)\n" % obj.Label
            gcode += linenumber() + "(machine units: %s)\n" % (UNIT_SPEED_FORMAT)
        for line in PRE_OPERATION.splitlines(True):
            gcode += linenumber() + line

        # get coolant mode
        coolantMode = 'None'
        if hasattr(obj, "CoolantMode") or hasattr(obj, 'Base') and  hasattr(obj.Base, "CoolantMode"):
            if hasattr(obj, "CoolantMode"):
                coolantMode = obj.CoolantMode
            else:
                coolantMode = obj.Base.CoolantMode

        # turn coolant on if required
        if OUTPUT_COMMENTS:
            if not coolantMode == 'None':
                gcode += linenumber() + '(Coolant On:' + coolantMode + ')\n'
        if coolantMode == 'Flood':
            gcode  += linenumber() + 'M8' + '\n'
        if coolantMode == 'Mist':
            gcode += linenumber() + 'M7' + '\n'

        # process the operation gcode
        gcode += parse(obj)

        # Make sure the laser is turned off after the last operation.
        gcode+= LASER_OFF + "\n"

        # do the post_op
        if OUTPUT_COMMENTS:
            gcode += linenumber() + "(finish operation: %s)\n" % obj.Label
        for line in POST_OPERATION.splitlines(True):
            gcode += linenumber() + line

        # turn coolant off if required
        if not coolantMode == 'None':
            if OUTPUT_COMMENTS:
                gcode += linenumber() + '(Coolant Off:' + coolantMode + ')\n'
            gcode  += linenumber() +'M9' + '\n'

    # do the post_amble
    if OUTPUT_COMMENTS:
        gcode += "(begin postamble)\n"

    # Add newline functionality to the command line input box. ";" for newline.
    POSTAMBLE = POSTAMBLE.replace(";", "\n")
    for line in POSTAMBLE.splitlines(True):
        gcode += linenumber() + line

    ###### Reprocess the "raw" output for laser #######
    gcode = laser_gcode(gcode, filename)

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

def laser_gcode(gcode, filename):
    # pylint: disable=global-statement
    global LINENR
    global LASER_POWER
    global LASER_ON
    global LASER_OFF

    # Add newline functionality to the command line input box. ";" for newline.
    LASER_OFF = LASER_OFF.replace(";", "\n")
    LASER_ON = LASER_ON.replace(";", "\n")

    # Reset the line number. Line numbers are removed during reprocessing and
    # added back in to avoid skipped numbers when removing lines.
    LINENR = 100

    gfile = open(filename, "w")

    isLaserOn = False
    isFirstMove = True
    modal_list = ['G0 ', 'G1 ', 'G2 ', 'G3 ']
    last_line = ""
    position = ['-1', '-1']
    last_position = ['0', '0']
    feed = ""
    last_feed = ""
    command = ""
    last_command = ""

    for line in gcode.splitlines(True): # Reprocess lines.

        if line == last_line: # Remove any duplicate lines.
            continue

        # Remove G0 commands that only have Z moves if 2d laser.
        if 'Z' in line and 'G0' in line and not LASER_3D:
            if 'X' not in line and 'Y' not in line:
                continue

        # Remove unwanted M6 command. Tool changes add unwanted laser on commands.
        if 'M6' in line:
            line = "(Laser)"

        gcode_line = line.split(" ")
        parameter = ""
        new_gcode_line = ""

        # Store relavent commands and values, remove the rest.
        for parameter in gcode_line:
            if 'G' in parameter:
                command = parameter
            elif 'X' in parameter:
                last_position[0] = position[0]
                position[0] = parameter
            elif 'Y' in parameter:
                last_position[1] = position[1]
                position[1] = parameter

            # F value is only output if it changes by default.
            # If --feed-non-modal is selected from the command line F value is output for all
            # feed controlled moves.
            elif 'F' in parameter:
                feed = parameter
                if feed == last_feed and last_command != 'G0' and not FEED_NON_MODAL:
                    continue

            # Remove first M3 command to avoid turning the laser on at program start.
            elif 'M3' in parameter:
                continue
            elif 'S' in parameter: # Don't use default S values e.g after a tool change command.
                continue
            elif 'N' in parameter:
                continue
            elif 'Z' in parameter and not LASER_3D: # Remove Z moves if 2d laser.
                continue
            elif 'K' in parameter and not OUTPUT_K: # Output K values with --output-k on command line.
                continue

            if '\n' in parameter:
                new_gcode_line += parameter # Don't add a space after the end of the line.
            else:
                new_gcode_line += parameter + " "

            new_gcode_line = new_gcode_line.replace(" \n", "\n") # Remove trailing whitespace.

        # 3d laser output, Z moves are retained but laser is only on during X Y motion.
        if LASER_3D:
            # Turn laser off for rapid moves. Don't toggle laser if first move.
            if command == 'G0':
                if isFirstMove:
                    gfile.write(linenumber() + LASER_OFF + "\n")
                    isFirstMove = False
                if isLaserOn:
                    gfile.write(linenumber() + LASER_OFF + "\n")
                    isLaserOn = False

            # Turn laser off if X and Y are stationary.
            elif command == 'G1' and position == last_position:
                gfile.write(linenumber() + LASER_OFF + "\n")
                isLaserOn = False

            # Turn laser on if X and Y are in motion.
            elif command in ['G1', 'G2', 'G3'] and position != last_position:
                if not isLaserOn:
                    gfile.write(linenumber() + LASER_ON + " " + LASER_POWER + "\n")
                    isLaserOn = True

        # 2d laser output, all Z moves are removed.
        else:
            # Remove duplicate and redundant commands.
            if command == 'G0' and last_command in ['G0', 'G1', 'G2', 'G3'] and position == last_position:
                continue
            elif command == 'G1' and last_command in ['G0', 'G1', 'G2', 'G3'] and position == last_position:
                continue

            # Turn laser off for rapid moves.
            if command == 'G0':
                gfile.write(linenumber() + LASER_OFF + "\n")

            # Turn laser on for feed controlled moves.
            elif command in ['G1', 'G2', 'G3'] and last_command == 'G0':
                gfile.write(linenumber() + LASER_ON + " " + LASER_POWER + "\n")

            # For some reason the output for G0 moves is sometimes modal. The code below adds the missing
            # axis back in. This shouldn't really matter, it's mostly for aesthetics.
            if 'G0' in new_gcode_line and 'X' in new_gcode_line and not 'Y' in new_gcode_line:
                new_gcode_line = "G0 " + position[0] + " " + last_position[1] + "\n"
                position[1] = last_position[1]

            elif 'G0' in new_gcode_line and 'Y' in new_gcode_line and not 'X' in new_gcode_line:
                new_gcode_line = "G0 " + last_position[0] + " " + position[1] + "\n"
                position[0] = last_position[0]


        last_feed = feed
        last_line = line

        # If --modal is selected from the command line, suppress duplicate commands.
        for c in modal_list:
            if command == last_command and c in new_gcode_line and MODAL:
                new_gcode_line = new_gcode_line.replace(c, "")

        last_command = command
        gfile.write(linenumber() + new_gcode_line) # Write the line to file.
    gfile.close()

    #read back the laser processed gcode so we can optionally display it
    gfile = open(filename, "r")
    gcode = gfile.read()
    gfile.close()

    print("Done postprocessing.")

    #return laser gcode
    return gcode

def linenumber():
    # pylint: disable=global-statement
    global LINENR
    if OUTPUT_LINE_NUMBERS is True:
        LINENR += 10
        return "N" + str(LINENR) + " "
    return ""

def parse(pathobj):
    # pylint: disable=global-statement
    global PRECISION
    global UNIT_FORMAT
    global UNIT_SPEED_FORMAT
    global LASER_POWER

    out = ""

    precision_string = '.' + str(PRECISION) + 'f'

    # the order of parameters

    params = ['X', 'Y', 'Z', 'A', 'B', 'C', 'I', 'J', 'K', 'F', 'S', 'T', 'Q', 'R', 'L', 'H', 'D', 'P']

    if hasattr(pathobj, "Group"):  # We have a compound or project.
        for p in pathobj.Group:
            out += parse(p)
        return out
    else:  # parsing simple path

        # groups might contain non-path things like stock.
        if not hasattr(pathobj, "Path"):
            return out

        for c in pathobj.Path.Commands:

            outstring = []
            command = c.Name
            outstring.append(command)

            if c.Name[0] == '(' and not OUTPUT_COMMENTS: # command is a comment
                continue

            # Now add the remaining parameters in order
            for param in params:
                if param in c.Parameters:
                    if param == 'F':
                        if c.Name not in ["G0", "G00"]:
                            speed = Units.Quantity(c.Parameters['F'], FreeCAD.Units.Velocity)
                            if speed.getValueAs(UNIT_SPEED_FORMAT) > 0.0:
                                outstring.append(param + format(float(speed.getValueAs(UNIT_SPEED_FORMAT)), precision_string))
                        else:
                            continue
                    elif param in ['T', 'H', 'D', 'S', 'P', 'L']:

                        # Store spindle speed(laser power). If --no-s is selected from the command line
                        # the S value is suppressed.
                        if param == 'S' and not NO_S:
                            LASER_POWER = param + str(c.Parameters[param])
                        else:
                            outstring.append(param + str(c.Parameters[param]))
                    else:
                        pos = Units.Quantity(c.Parameters[param], FreeCAD.Units.Length)
                        outstring.append(param + format(float(pos.getValueAs(UNIT_FORMAT)), precision_string))

            if command == "message":
                if OUTPUT_COMMENTS is False:
                    out = []
                else:
                    outstring.pop(0)  # remove the command

            if len(outstring) >= 1:
                # append the line to the final output
                for w in outstring:
                    out += w + COMMAND_SPACE
                # Note: Do *not* strip `out`, since that forces the allocation
                # of a contiguous string & thus quadratic complexity.
                out += "\n"

        return out

# print(__name__ + " gcode postprocessor loaded.")
