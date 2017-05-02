#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import display
from command import Command


class Controller:
    """Reads output of 'xrandr -q' to get all connected displays
    and their resolutions.
    Stores available displays.
    Handles user input to determine the respective xrandr commands.

    Provides the following methods:

        1) get_common_resolutions()
        2) print_status()
        3) get_built_in_display()
        4) reduce_viewport(display)
        5) clone_viewport()
        6) extend_viewport(diretion)
    """
    def __init__(self):
        """Get connected displays and their resolutions."""
        cmd = Command("xrandr -q")
        output = cmd.call(feedback=True).strip().split("\n")
        self._displays = []

        # Iterate over xrandr output
        for i in range(len(output)):
            # Detect connected displays
            if " connected" in output[i]:
                displayName = output[i].split(" ")[0]
                resolutions = []

                # Get available resolutions
                for j in range(i+1, len(output)):
                    line = output[j]

                    if line.startswith(" "):
                        line = line.strip(" ").split(" ")[0]
                        res = display.Resolution(line)
                        resolutions.append(res)
                    else:
                        break

                # Store display data
                disp = display.Display(displayName, resolutions)
                self._displays.append(disp)

        # Assume that the first display listed by xrandr is the main one.
        self._builtIn = self._displays[0]


    def get_common_resolutions(self):
        """Return list of resolutions shared by all connected displays."""
        # Create copy of first display
        dummy = display.Display("Dummy", self._builtIn.get_resolutions())

        # Iterate over remaining displays
        for disp in self._displays[1:]:
            # Create dummy display with intersection of all resolutions
            dummy = display.Display("Dummy", dummy & disp)

        return dummy.get_resolutions()


    def print_status(self, message):
        """Print final message about what the program just did
        before exiting.
        """
        print(message)
        sys.exit(0)


    def get_built_in_display(self):
        """Return built-in display."""
        return self._builtIn


    def reduce_viewport(self, disp):
        """Reduce the viewport to single display.
        The resolution is determined automatically by xrandr.
        """
        # Set output to display disp
        cmd = Command("xrandr")
        cmd += "--output"
        cmd += str(disp)
        cmd += "--auto"
        cmd += "--rotate normal"
        cmd += "--pos 0x0"

        # Turn off output of all other displays
        for disp in (x for x in self._displays if x != disp):
            cmd += "--output " + str(disp) + " --off"

        cmd.call()
        self.print_status("Reduced viewport.")


    def clone_viewport(self):
        """Clone viewport to all registered displays.
        Use the highest shared resolution.
        """
        if len(self._displays) > 1:
            # Make sure each display gets the same resolution
            res = str(max(self.get_common_resolutions()))
            cmd = Command("xrandr")

            for disp in self._displays:
                cmd += "--output " + str(disp)
                cmd += "--mode " + res
                cmd += "--rotate normal"
                cmd += "--pos 0x0"

            cmd.call()
            self.print_status("Cloned viewport.")

        else:
            print("Only one display connected. Cannot clone.")
            sys.exit(0)


    def extend_viewport(self, direction):
        """Extend the viewport to another display left or right
        of the built-in display.
        Assumes that exactly two displays are connected.
        The resolution is determined automatically by xrandr.
        """
        if len(self._displays) < 2:
            print("Bad number of displays.")
            sys.exit(1)

        else:
            # Normalize direction
            if direction in ("right", "r"):
                direction = "right"
            elif direction in ("left", "l"):
                direction = "left"
            else:
                print("Bad direction.")
                sys.exit(1)

            # Set output for built-in display
            cmd = Command("xrandr")
            cmd += "--output " + str(self._builtIn)
            cmd += "--auto"
            cmd += "--rotate normal"
            cmd += "--pos 0x0"

            # Set output for remaining display
            prev = self._builtIn
            for disp in (x for x in self._displays if x != self._builtIn):
                cmd += "--output " + str(disp)
                cmd += "--auto"
                cmd += "--rotate normal"
                cmd += "--" + direction + "-of " + str(prev)
                
                prev = disp

            cmd.call()
            self.print_status("Extended viewport.")


def main():
    """Parse arguments and call the respective methods."""
    # Quit program if too few arguments are provided.
    if len(sys.argv) < 2:
        sys.exit(1)

    else:
        args = sys.argv[1:]
        mode = args[0]
        c = Controller()

        # Clone viewport.
        if mode in ("clone", "c"):
            c.clone_viewport()

        # Extend viewport.
        elif mode in ("extend", "e"):
            c.extend_viewport(args[1])

        # Reduce viewport to single display.
        elif mode in ("solo", "s"):
            c.reduce_viewport(c.get_built_in_display())

        # Unknown command, so quit program.
        else:
            sys.exit(1)


if __name__ == "__main__":


    main()
