import importlib.util
import pathlib
import tempfile
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "linux_image.py"
SPEC = importlib.util.spec_from_file_location("linux_image", MODULE_PATH)
linux_image = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(linux_image)


class LinuxImageTest(unittest.TestCase):
    def test_build_linux_image_places_every_component(self):
        payloads = {
            "Image": b"kernel",
            "rv32.dtb": b"dtb",
            "opensbi.bin": b"opensbi",
            "rootfs.cpio.gz": b"rootfs",
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = pathlib.Path(temporary_directory)
            inputs = {}
            for name, payload in payloads.items():
                path = directory / name
                path.write_bytes(payload)
                inputs[name] = path

            output = directory / "boot.bin"
            linux_image.build_linux_image(inputs, output)

            with output.open("rb") as image:
                for name, address, _ in linux_image.LAYOUT:
                    image.seek(address - linux_image.SDRAM_BASE)
                    self.assertEqual(image.read(len(payloads[name])), payloads[name])

            expected_size = (
                0x41000000 - linux_image.SDRAM_BASE + len(payloads["rootfs.cpio.gz"])
            )
            self.assertEqual(output.stat().st_size, (expected_size + 3) & ~3)

    def test_build_linux_image_rejects_overlapping_component(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = pathlib.Path(temporary_directory)
            inputs = {}
            for name, start, end in linux_image.LAYOUT:
                path = directory / name
                path.write_bytes(b"x")
                inputs[name] = path

            inputs["rv32.dtb"].write_bytes(b"x" * (0x10000 + 1))

            with self.assertRaisesRegex(ValueError, "slot only allows"):
                linux_image.build_linux_image(inputs, directory / "boot.bin")

            self.assertFalse((directory / "boot.bin").exists())


if __name__ == "__main__":
    unittest.main()
