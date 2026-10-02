# Custom LiteX RISC-V SoC for Analogue Pocket

This SoC is intended to serve as a host platform for any kind of software that may be useful/fun/interesting to run on the Analogue Pocket, such as calculators, cart dumpers, internet access, custom game consoles/emulation, and more. The system is constructed to provide access to as many of the Pocket's core systems as possible in a simple, software-friendly manner. As opportunities arrive, some functionality may be hardware accelerated.

The core is not intended for use by end users directly, but for developers, who may use either the distributed built assets (the `agg23.RISCV....zip` release) or this repo itself, customized to provide the experience desired.

## Features

* Full input handing
* ~~Cart slot and link port access~~ - `Coming soon`
* Serial bus, with program hot reloading, via USB Blaster JTAG adapter or Analogue Pocket Dev Kit UART cart
* File access API for load/store - [See Analogue Docs](https://www.analogue.co/developer/docs/core-definition-files/data-json) - `Writing to disk broken in Pocket firmware`
* Vblank and vsync access; frame counter
* 48kHz audio playback with 4096 sample buffer
* Live RTC access
* Cyclone V unique chip ID access

## Hardware Definition

General RISC-V notation for this core is: `riscv32imafdc`. See [Standard Extensions](https://en.wikichip.org/wiki/risc-v/standard_extensions) to learn what each of the letters mean.

Notably, this core contains:

* 32 bit CPU, buses, RAM
* Atomics
* A FPU supporting both 32 and 64 bit floats

Pocket RAM used:

* 31% of FPGA BRAM
* SDRAM

### Linux Bring-up Profile

The optional Linux profile uses the LiteX `linux` CPU variant and removes the
Pocket framebuffer and example Wishbone slave so that no SDRAM framebuffer
region is reserved. The generated hardware contract is checked by
`litex/linux_check.py` on every `make linux` build.

* VexRiscv-SMP: 1 hart, RV32IMAFDC, Sv32 MMU
* 57.12 MHz system clock
* 4 KiB direct-mapped instruction and data caches
* 4-entry instruction and data TLBs
* 64 MiB SDRAM at `0x4000_0000`
* OpenSBI region at `0x40f0_0000`
* CSR, CLINT, and PLIC at `0xf000_0000`, `0xf001_0000`, and `0xf0c0_0000`
* Timer IRQ 1 and UART IRQ 2

The Pocket slot-0 Linux image layout is:

| Component | Load address | Maximum size |
| --- | ---: | ---: |
| Linux `Image` | `0x4000_0000` | `0x00ef_0000` (14.94 MiB) |
| Device tree | `0x40ef_0000` | 64 KiB |
| OpenSBI | `0x40f0_0000` | 1 MiB |
| Initramfs | `0x4100_0000` | 48 MiB |

## General Operation

### Data

The core automatically loads and boots from the `data.json` slot id 0 entry. This defaults to a file named `/Assets/riscv/common/boot.bin`. Replacing this allows you to automatically start your own program. The program is written to `0x4000_0000`, with the jump vector at that address.

Adding additional dataslots allows you to request reads/writes via [File API](./docs/control.md#file-api). You can choose the address you send the data to. I would recommend not clobbering your loaded program, but maybe you can do something neat with self-modifying programs.

### UART

The core supports UART over serial and JTAG, and can boot programs over UART. JTAG requires [a supported USB Blaster](https://www.digikey.com/en/products/detail/terasic-inc/P0302/2003484) (**NOTE:** Don't buy a Chinese clone. This has killed at least one Pocket). Serial requires the developer kit dev cart (not available for purchase), OR you could build the cart yourself (contact me and our group of devs will help you figure out what you need). `/lang/rust` gives an example of how to write to the UART with `println!()`; just like writing to `stdout`.

The serial UART is pinned to the max speed supported by the dev cart, 2,000,000bps. Serial UART is disabled when JTAG is enabled. Before you can use the dev cart, you must first enable the cart slot and link port power. Edit `core.json`, and change:
```json
"hardware": {
  "link_port": false,
  "cartridge_adapter": -1
}

// to

"hardware": {
  "link_port": false,
  "cartridge_adapter": 0
}
```

Without performing this change, you will not be able to do anything over the cartridge slot, including serial UART.

You can connect using the LiteX tooling via:
```bash
python3 ./litex/litex_term.py --speed 2000000 /dev/ttyUSB0

# To automatically upload a program named `rust.bin`
python3 ./litex/litex_term.py --speed 2000000 --kernel rust.bin /dev/ttyUSB0
```

JTAG UART must be explicitly enabled in the [Core Settings](#core-settings). JTAG UART has fewer options:
```bash
python3 ./litex/litex_term.py --jtag-config=openocd_usb_blaster.cfg jtag

# To automatically upload a program named `rust.bin`
python3 ./litex/litex_term.py --jtag-config=openocd_usb_blaster.cfg --kernel rust.bin jtag
```

The kernel program will be uploaded on core reset, so you can either start the core fresh, or reset it from the menu (or configured reset button).

You may opt to send a custom command over UART to your running core that causes reset. This would allow for full automation and deployment of a program when building.

### Core Settings

Core Settings are defined in `interact.json`, and the core defaults with two options:

* `Enable + Btn Reset` - When enabled, the + button (to the right of the Analogue button) will be configured to act as a core reset. This is handy if you are actively developing a core, and quickly want to upload a new version.
* `Enable JTAG UART` - When enabled, the JTAG adapter will be used for platform UART; the serial UART port will be disabled.

When releasing your core, you likely want to remove both of these options, as they are not likely to be beneficial to your users.

## Getting Started

### Software Only

You can simply [download the latest release](https://github.com/agg23/openfpga-litex2/releases/latest) and start writing code. For language setup help and examples, see [Languages](/lang/README.md).

I suggest you make this repo a submodule of your main project so you can reference import libraries and files, along with pinning the core version. Otherwise, you may want to download the repo recursively (to grab the submodules) so that you have the expected headers and libraries for your software to link to.

### Customize Hardware

**NOTE:** You will probably have a bad time if you try to do this with Windows. It should be possible, but I just found lots of pain.

Python 3.11 is known to work with the pinned Migen version; Python 3.14 fails
during clock-domain name extraction. A complete FPGA build also requires
Quartus Prime Lite 18.1 with Cyclone V device support, a RISC-V bare-metal GCC
toolchain, and Scala/sbt when the VexRiscv-SMP RTL must be regenerated. GCC
13.2.0 is known to work; GCC 14
turns a conversion in the pinned LiteX BIOS into a build error.

```bash
# Clone this Linux bring-up branch and all pinned vendor repositories.
git clone --recursive --branch codex/linux-bringup \
  https://github.com/zerofrip/openfpga-litex-linux.git
cd openfpga-litex-linux
git submodule update --init --recursive --jobs 8

# Create the Python environment.
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install pyserial requests packaging pyyaml meson ninja

# Put riscv-none-elf-* (or a compatible multilib RISC-V toolchain), sbt,
# and Quartus 18.1 on PATH before building.
export PATH=/path/to/riscv-toolchain/bin:/path/to/quartus/18.1/quartus/bin:$PATH
```

The RISC-V toolchain can be built from
[riscv-gnu-toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain) or
installed from a compatible prebuilt distribution. If building it locally,
enable the newlib multilib target so RV32IMAFDC/ILP32D is available.

```bash
./configure --prefix=/opt/riscv --enable-multilib
make
```

This produces binaries such as `riscv64-unknown-elf-gcc`; the multilib build
can also target RV32. LiteX also detects the `riscv-none-elf-*` prefix used by
the xPack embedded toolchain.

#### Linux FPGA build

Generate the Linux LiteX SoC and validate its CPU, memory map, SDRAM, interrupt,
timer, and framebuffer settings:

```bash
cd litex
make linux
```

Then run the complete Quartus flow from the repository root:

```bash
cd ..
quartus_sh --flow compile projects/openFPGA-RISC-V_pocket.qpf
```

The primary outputs are:

* `projects/output_files/openFPGA-RISC-V_pocket.rbf` for the Pocket core
* `projects/output_files/openFPGA-RISC-V_pocket.sof` for JTAG programming
* `projects/output_files/openFPGA-RISC-V_pocket.sta.summary` for timing results

To create the Pocket slot-0 `boot.bin`, install `dtc`, put the Linux `Image`,
OpenSBI binary, and initramfs at `litex/images/Image`,
`litex/images/opensbi.bin`, and `litex/images/rootfs.cpio.gz`, then run:

```bash
cd litex
make linux-package
```

This generates the device tree and writes
`pkg/pocket/Assets/riscv/common/boot.bin`. The packer rejects empty or oversized
components before replacing the output image.

## Writing Software

[Guides and examples for several languages are available](/lang/README.md). Check those first.

The `/lang/linker/` directory contains the required linker files for you to build against the SoC. `memory.x` was written by hand, and `regions.ld` is generated by the LiteX build process and copied over to this directory.

You need to build against the [specific RISC-V extension target used by the core](#hardware-definition). Using the standard `riscv32-unknown-elf-gcc`, building for this architecture would look something like this:

```bash
riscv32-unknown-elf-gcc -march=rv32imacfd -mabi=ilp32fd
```

Notably, you _must_ build targetting the FPU (`-mabi=ilp32fd`). Software built targetting a soft-float implementation will not run.

### Accessing Control Registers

To actually do anything with the hardware, you need to access many different control registers. These provide the CPU with an interface to modify how the hardware SoC operates. LiteX provides this nice, generic mechanism for specifying control information via [the SVD file](/litex/pocket.svd). This file provides a machine readable list of all the interaction points in the SoC and provides short descriptions on how to use them. [A human readable description, with additional details, is also provided](/docs/control.md).

The SVD file can be used to generate support packages to automatically keep your program address constants up to date with the current iteration of the hardware. An example of this can be found in the [Rust `litex-pac` crate](/lang/rust/crates/litex-pac).

## Modifying the Hardware

* [Adjusting Resolution](/docs/resolution.md)
