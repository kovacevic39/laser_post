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

TOOLTIP = '''
Generate g-code that is compatible with a laser.
import laser_post
laser_post.export(object, "/path/to/file.ncc", "")
'''

#   This postprocessor imports an existing "stock" postprocessor to generate gcode
#   as a starting point for further customization and formatting.

#   The export() function in this file is the entry point.

import FreeCAD
import linuxcnc_post
import re
import argparse
import shlex

try:
    import Path.Post.Utils as PostUtils
except:
    pass

try:
    from PathScripts import PostUtils
except:
    pass

def init_variables():

    variables = dict(

        PREAMBLE = "G17 G90",
        POSTAMBLE = "M5\nG17 G90\nM2",
        LASER_ON = "M3",
        LASER_OFF = "M5",
        LASER_POWER = "S0",
        SHOW_EDITOR = True,
        PRECISION = "3",
        OUTPUT_LINE_NUMBERS = False,
        LINENR = 100

        )

    return variables

def init_parser():

    #   Initialises the parser with some custom tags to format TOOLTIP_ARGS and is intended
    #   for use with the format_tooltips() function. See the bottom of this file
    #   to see how it's used.
    #   {sp} = 1 space, {tab} = 4 spaces , {nl} = newline

    parser = argparse.ArgumentParser(prog='laser', add_help=False)
    parser.add_argument('--no-header', action='store_true',
                help = '{tab}Don\'t include header.{nl}')

    parser.add_argument('--no-comments', action='store_true',
                help = '{tab}Don\'t include comments.{nl}')

    parser.add_argument('--line-numbers', action='store_true',
                help = '{tab}Output line numbers.{nl}')

    parser.add_argument('--no-show-editor', action='store_true',
                help = '{tab}Don\'t show editor after postprocess.{nl}')

    parser.add_argument('--inches', action='store_true',
                help = '{tab}Output US imperial units.{nl}')

    parser.add_argument('--precision',
                help = '{tab}Decimal precision. Default is 3{nl}')

    parser.add_argument('--preamble',
                help = '{nl}{tab}First commands written to gcode file, use \\n for newline.{nl}\
                            {tab}{tab}Default is "G17 G90"{nl}')

    parser.add_argument('--postamble',
                help = '{nl}{tab}Last commands written to gcode file, use \\n for newline.{nl}\
                            {tab}{tab}Default is "M5\\nG17 G90\\nM2"{nl}\
                            {tab}{tab}{tab}M5{nl}\
                            {tab}{tab}{tab}G17 G90{nl}\
                            {tab}{tab}{tab}M2{nl}')

    parser.add_argument('--laser-on',
                help = '{nl}{tab}Command to turn laser on, use \\n for newline.{nl}\
                            {tab}{tab}Default is "M3"{nl}')

    parser.add_argument('--laser-off',
                help = '{nl}{tab}Command to turn laser off, use \\n for newline.{nl}\
                            {tab}{tab}Default is "M5"{nl}')

    parser.add_argument('--laser-power',
                help = '{nl}{tab}Laser power command, use \\n for newline.{nl}\
                            {tab}{tab}Default is spindle speed "S####"{nl}\
                            {tab}{tab}Use "NONE" or "" to supress any power commands.{nl}')
    return parser

def format_tooltips(tooltips):

    #   This is a simple formatter for argparse help
    space = " "
    new_tooltips = ""

    for line in tooltips.splitlines(True):
        if "[" not in line:                 #leave the usage section alone
            line = line.replace("\n", "")   #remove all newlines
            line = re.sub(" +", " ", line)  #remove extra whitespace
            line = line.replace("--", "\n --")  #add only one newline per arg
            line = line.replace("{sp}", " ")    #add our own white space and newlines
            line = line.replace("{tab}", "    ")
            line = line.replace("{nl}", "\n")
            line = line.replace("options:", "\noptions:")
            new_tooltips += line
        else:
            new_tooltips += line

    return new_tooltips

def parse_args(variables, argstring, parser):

    #   Process the arguments we are interested in and pass the rest
    #   on to the imported postprocessor

    new_argstring = "--no-show-editor " #suppress popup editor in the
                                        #imported potprocessor
    args = parser.parse_args(shlex.split(argstring))

    if args.no_header:
        new_argstring += "--no-header "

    if args.no_comments:
        new_argstring += "--no-comments "

    if args.line_numbers:
        variables["OUTPUT_LINE_NUMBERS"] = True

    if args.no_show_editor:
        variables["SHOW_EDITOR"] = False

    if args.inches:
        new_argstring += "--inches "

    if args.precision is not None:
        variables["PRECISION"] = args.precision
        new_argstring += f'--precision {args.precision} '
    else:
        new_argstring += f'--precision {variables["PRECISION"]} '

    #   Place markers in the initial gcode before reformat so we can
    #   add newlines to the preamble and postamble.
    #   We save the --preamble from the argstring and pass the markers on to
    #   the imported postprocessor.
    #   Don't use PREAMBLE or POSTAMBLE for markers, it confuses the parser.

    if args.preamble is not None:
        new_argstring += "--preamble TOP_MARKER "
        variables["PREAMBLE"] = args.preamble.replace("\\n", '\n')
    else:
        new_argstring += f'--preamble """{variables["PREAMBLE"]}""" '

    if args.postamble is not None:
        new_argstring += "--postamble BOTTOM_MARKER "
        variables["POSTAMBLE"] = args.postamble.replace("\\n", '\n')

    else:
        new_argstring += f'--postamble """{variables["POSTAMBLE"]}""" '

    if args.laser_on is not None:
        variables["LASER_ON"] = args.laser_on.replace("\\n", '\n')

    if args.laser_off is not None:
        variables["LASER_OFF"] = args.laser_off.replace("\\n", '\n')

    if args.laser_power is not None:
        args.laser_power = args.laser_power.replace("NONE", "")
        variables["LASER_POWER"] = args.laser_power.replace("\\n", '\n')

    return new_argstring

def linenumber(variables):

    if variables["OUTPUT_LINE_NUMBERS"] is True:
        variables["LINENR"] += 10
        return "N" + str(variables["LINENR"]) + " "
    return ""

def laser_gcode(gcode, variables):

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

        if "S" in line and variables["LASER_POWER"] == "S0":
            variables["LASER_POWER"] = (re.search(r"S.*?(?=\s)", line)).group()

    #   Remove unwanted commands.

        if "M3 " in line or "M6 " in line or "G43 " in line:
            continue

    #   Make sure laser off command matches LASER_OFF

        if "M5\n" in line or "M5 " in line:
            line = line.replace("M5", variables["LASER_OFF"])

    #   Print custom preamble and postamble

        if "TOP_MARKER" in line:
            temp_gcode += f'{variables["PREAMBLE"]}{nl}'
            continue

        if "BOTTOM_MARKER" in line:
            temp_gcode += f'{variables["POSTAMBLE"]}{nl}'
            continue

    #   Store relavent values.

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

    #   Feedrate semi-modal. Freedrate is printed at the beginning of each motion contolled group.

        if  cur_state["F"] == prev_state["F"] and prev_state["G"] != "G0":
            f_word = ""

    #   Remove redundent moves created when ignoring the Z axis.

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
            temp_line += f'{variables["LASER_OFF"]}{nl}'    #print laser off command
            temp_line += f"{g_word}{x_word}{y_word}{nl}"    #print gcode line

        elif "G1 " in line and cur_state["LASER"] == "ON":
            temp_line += f"{g_word}{x_word}{y_word}{f_word}{nl}"

        elif "G1 " in line and cur_state["LASER"] == "OFF":
            cur_state["LASER"] = "ON"
            temp_line += f'{variables["LASER_ON"]} {variables["LASER_POWER"]}{nl}'
            temp_line += f"{g_word}{x_word}{y_word}{f_word}{nl}"

        elif "G2 " in line or "G3 " in line and cur_state["LASER"] == "ON":
            temp_line += f"{g_word}{x_word}{y_word}{i_word}{j_word}{f_word}{nl}"

        elif "G2 " in line or "G3 " in line and cur_state["LASER"] == "OFF":
            cur_state["LASER"] = "ON"
            temp_line += f'{variables["LASER_ON"]} {variables["LASER_POWER"]}{nl}'
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

    if variables["OUTPUT_LINE_NUMBERS"]:

        for line in temp_gcode.splitlines(True):

            laser_gcode += linenumber(variables) + line
    else:
        laser_gcode = temp_gcode

    return laser_gcode

def export(objectslist, filename, argstring):

    parser = init_parser()

    variables = init_variables()

    #   Format the argument string for our purposes before passing it on to
    #   the imported postprocessor

    new_argstring = parse_args(variables, argstring, parser)

    #   Call the imported postprocessor and format the output.

    gcode = linuxcnc_post.export(objectslist, filename, new_argstring)

    gcode = laser_gcode(gcode, variables)

    if FreeCAD.GuiUp and variables["SHOW_EDITOR"]:
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

    gcode_file = open(filename, "w")
    gcode_file.write(final)
    gcode_file.close()

    return final

#   Generate popup tooltips for arguments

tooltip_parser = init_parser()

#   Use format_tooltips() to make popup help more readable

TOOLTIP_ARGS = format_tooltips(tooltip_parser.format_help())

# print(__name__ + " gcode postprocessor loaded.")

