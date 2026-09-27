#!/usr/bin/env python3

import argparse
import math
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ModuleNotFoundError:
    # Pillow lives in Homebrew Python; /usr/bin/python3 and project venvs often lack it.
    brew = "/opt/homebrew/bin/python3"
    if os.path.exists(brew) and not os.environ.get("CONTACT_SHEET_REEXEC"):
        os.environ["CONTACT_SHEET_REEXEC"] = "1"
        os.execv(brew, [brew, *sys.argv])
    sys.exit("contact-sheet.py needs Pillow: /opt/homebrew/bin/python3 -m pip install Pillow")

parser = argparse.ArgumentParser(
    description="Combine images into a contact sheet",
    epilog="Example: contact-sheet.py out.png a.png b.png c.png --columns 3 --cell 480x300",
)
parser.add_argument("output", type=Path)
parser.add_argument("images", nargs="+", type=Path)
parser.add_argument("--columns", type=int, default=3)
parser.add_argument("--cell", default="480x300")
args = parser.parse_args()

cell_width, cell_height = map(int, args.cell.lower().split("x", 1))
rows = math.ceil(len(args.images) / args.columns)
sheet = Image.new("RGB", (args.columns * cell_width, rows * cell_height), "white")

for index, path in enumerate(args.images):
    with Image.open(path) as image:
        image = ImageOps.contain(image.convert("RGB"), (cell_width, cell_height))
        x = (index % args.columns) * cell_width + (cell_width - image.width) // 2
        y = (index // args.columns) * cell_height + (cell_height - image.height) // 2
        sheet.paste(image, (x, y))

sheet.save(args.output)
