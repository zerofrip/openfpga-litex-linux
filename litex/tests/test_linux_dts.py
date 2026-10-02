import importlib.util
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock


MODULE_PATH = pathlib.Path(__file__).parents[1] / "linux_dts.py"
SPEC = importlib.util.spec_from_file_location("linux_dts", MODULE_PATH)
linux_dts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(linux_dts)


class LinuxDtsTest(unittest.TestCase):
    def test_generate_linux_dts_uses_non_polling_litex_configuration(self):
        calls = []

        def fake_generate_dts(csr_data, **kwargs):
            calls.append((csr_data, kwargs))
            return "/dts-v1/;\n"

        litex_module = types.ModuleType("litex")
        tools_module = types.ModuleType("litex.tools")
        generator_module = types.ModuleType("litex.tools.litex_json2dts_linux")
        generator_module.generate_dts = fake_generate_dts

        modules = {
            "vendor": types.ModuleType("vendor"),
            "litex": litex_module,
            "litex.tools": tools_module,
            "litex.tools.litex_json2dts_linux": generator_module,
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = pathlib.Path(temporary_directory)
            csr_json = temporary_path / "csr.json"
            dts = temporary_path / "output" / "pocket.dts"
            csr_json.write_text(json.dumps({"constants": {"config_cpu_count": 1}}))

            with mock.patch.dict(sys.modules, modules):
                linux_dts.generate_linux_dts(csr_json, dts, "enabled", "ram0")

            self.assertEqual(dts.read_text(), "/dts-v1/;\n")
            self.assertEqual(
                calls,
                [
                    (
                        {"constants": {"config_cpu_count": 1}},
                        {"initrd": "enabled", "polling": False, "root_device": "ram0"},
                    )
                ],
            )

    def test_compile_dts_invokes_dtc_without_a_shell(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = pathlib.Path(temporary_directory)
            dts = temporary_path / "pocket.dts"
            dtb = temporary_path / "output" / "pocket.dtb"

            with mock.patch.object(linux_dts.subprocess, "run") as run:
                linux_dts.compile_dts(dts, dtb)

            run.assert_called_once_with(
                ["dtc", "-O", "dtb", "-o", dtb, dts],
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
