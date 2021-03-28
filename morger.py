#!/d/Python37/python

import argparse
import os
import re
import sys

ORIG_FOLDER = "ORIGINAL_FILES_BACKUP"
MOD_FOLDER = "PUT_MOD_FILES_IN_THIS_FOLDER"

class Entry:
    def __init__(self, basepath, status):
        self.basepath = basepath
        self.status = status

class Config:
    """Class to store config data"""

    def __init__(self, filename):
        """Init"""
        self.filename = filename
        self.entries = dict()
        entry = None
        title, base, status = None, None, None
        with open(filename, "r") as fin:
            for line in fin.readlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                match = re.match(r"\[\s*([A-Za-z0-9 ]+)\s*\]", line)
                if match:
                    title = match.group(1)
                    continue
                match = re.match(r"(\w+)\s*=\s*(.+?)\s*$", line)
                if match:
                    k, v = match.groups()
                    if k == "GamePath":
                        basepath = v
                    elif k == "Active":
                        status = v

                if not line and title:
                    entry = Entry(basepath, status)
                    self.entries[title] = entry
                    if status not in ("Yes", "No"):
                        print("-W- Invalid status found:", status)
                    title, basepath, status = None, None, None

    def write(self):
        """Write out config file"""
        with open(self.filename, "w") as fout:
            for title, entry in self.entries.items():
                fout.write(f"[{title}]\n")
                fout.write(f"    GamePath = {entry.basepath}\n")
                fout.write(f"    Active   = {entry.status}\n")
                fout.write("\n")

def modswap(args, entry):
    """Install or uninstall a mod"""
    title = args.swap
    bakpath = os.path.join(args.modpath, title, MOD_FOLDER)
    origpath = os.path.join(args.modpath, title, ORIG_FOLDER)
    gamepath = entry.basepath

    if entry.status == "Yes":
        dest1 = bakpath
        src2 = origpath
    elif entry.status == "No":
        dest1 = origpath
        src2 = bakpath
    src1 = dest2 = gamepath

    for dpath, dnames, fnames in os.walk("."):
        for fname in fnames:
            fpath = os.path.join(dpath, fname)
            fpath = os.path.relpath(fpath, start=src2)
            os.renames(
                os.path.join(src1, fpath),
                os.path.join(dest1, fpath)
            )
            os.renames(
                os.path.join(src2, fpath),
                os.path.join(dest2, fpath)
            )

    entry.status = "No" if entry.status == "Yes" else "Yes"

def setup_args():
    """Initialize arguments"""
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", "-c",
        default="mods.cfg",
        dest="config")
    parser.add_argument("--modpath", default="mods")

    meg_mode = parser.add_mutually_exclusive_group(required=True)

    meg_mode.add_argument("--list", action="store_true")
    meg_mode.add_argument("--init")
    meg_mode.add_argument("--swap", "-s")

    return parser.parse_args()

if __name__ == "__main__":
    args = setup_args()
    config = Config(args.config)
    if args.list:
        for k, v in config.entries.items():
            print(k)
            print("    Game Path = " + v.basepath)
            print("    Mod active? " + v.status)
            print()
    elif args.init:
        if args.init in config.entries:
            print("-E- Config already contains that entry!")
            sys.exit(1)
        entry = Entry("Put game path here", "No")
        config.entries[args.init] = entry
        config.write()
        os.makedirs(os.path.join(args.modpath, args.init, ORIG_FOLDER))
        os.makedirs(os.path.join(args.modpath, args.init, MOD_FOLDER))
    elif args.swap:
        modswap(args, config.entries[args.swap])
        config.write()
