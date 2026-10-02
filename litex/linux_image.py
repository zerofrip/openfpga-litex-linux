#!/usr/bin/env python3

import argparse
import os
from pathlib import Path


SDRAM_BASE = 0x40000000
SDRAM_SIZE = 0x04000000

LAYOUT = (
    ("Image", 0x40000000, 0x40EF0000),
    ("rv32.dtb", 0x40EF0000, 0x40F00000),
    ("opensbi.bin", 0x40F00000, 0x41000000),
    ("rootfs.cpio.gz", 0x41000000, SDRAM_BASE + SDRAM_SIZE),
)


def build_linux_image(inputs, output):
    output = Path(output)
    components = []

    for name, start, end in LAYOUT:
        path = Path(inputs[name])
        size = path.stat().st_size
        if size == 0:
            raise ValueError(f"{name} is empty: {path}")
        if size > end - start:
            raise ValueError(
                f"{name} is {size} bytes, but its slot only allows {end - start} bytes"
            )
        components.append((name, path, start - SDRAM_BASE, size))

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    try:
        with temporary.open("wb") as image:
            for name, path, offset, size in components:
                image.seek(offset)
                with path.open("rb") as component:
                    while chunk := component.read(1024 * 1024):
                        image.write(chunk)
                print(
                    f"Packed {name}: {path} -> 0x{SDRAM_BASE + offset:08x} "
                    f"({size} bytes)"
                )

            # APF transfers are word-oriented; keep the final image word-aligned.
            end = image.tell()
            image.truncate((end + 3) & ~3)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()

    print(f"Wrote {output} ({output.stat().st_size} bytes)")


def main():
    parser = argparse.ArgumentParser(
        description="Pack the LiteX Linux payloads into the Pocket slot-0 boot.bin."
    )
    parser.add_argument("--image", default=os.path.join("images", "Image"))
    parser.add_argument(
        "--dtb", default=os.path.join("build", "litex", "pocket.dtb")
    )
    parser.add_argument("--opensbi", default=os.path.join("images", "opensbi.bin"))
    parser.add_argument(
        "--rootfs", default=os.path.join("images", "rootfs.cpio.gz")
    )
    parser.add_argument(
        "--output",
        default=os.path.join(
            "..", "pkg", "pocket", "Assets", "riscv", "common", "boot.bin"
        ),
    )
    args = parser.parse_args()

    build_linux_image(
        {
            "Image": args.image,
            "rv32.dtb": args.dtb,
            "opensbi.bin": args.opensbi,
            "rootfs.cpio.gz": args.rootfs,
        },
        args.output,
    )


if __name__ == "__main__":
    main()
