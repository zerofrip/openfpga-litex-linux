import copy
import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "linux_check.py"
SPEC = importlib.util.spec_from_file_location("linux_check", MODULE_PATH)
linux_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(linux_check)


def valid_config():
    return {
        "constants": {
            **linux_check.EXPECTED_CONSTANTS,
            "config_cpu_type_vexriscv_smp": None,
            "config_cpu_variant_linux": None,
        },
        "csr_bases": dict(linux_check.EXPECTED_CSR_BASES),
        "memories": {
            name: {"base": base, "size": size}
            for name, (base, size) in linux_check.EXPECTED_MEMORIES.items()
        },
    }


class LinuxCheckTest(unittest.TestCase):
    def test_accepts_expected_linux_configuration(self):
        self.assertEqual(linux_check.validate_linux_config(valid_config()), [])

    def test_rejects_wrong_cpu_and_memory_configuration(self):
        config = copy.deepcopy(valid_config())
        config["constants"]["config_cpu_variant_standard"] = None
        del config["constants"]["config_cpu_variant_linux"]
        config["constants"]["config_cpu_isa"] = "rv32ima"
        config["memories"]["main_ram"]["size"] = 0x02000000

        errors = linux_check.validate_linux_config(config)

        self.assertTrue(any("config_cpu_variant_linux" in error for error in errors))
        self.assertTrue(any("config_cpu_isa" in error for error in errors))
        self.assertTrue(any("memory main_ram" in error for error in errors))

    def test_rejects_framebuffer_and_wrong_irq_layout(self):
        config = valid_config()
        config["constants"]["video_framebuffer_base"] = 0x40C00000
        config["constants"]["max_display_width"] = 266
        config["constants"]["max_display_height"] = 240
        config["constants"]["timer0_interrupt"] = 2
        config["csr_bases"]["uart"] = "0xf0005800"

        errors = linux_check.validate_linux_config(config)

        self.assertTrue(any("video_framebuffer_base" in error for error in errors))
        self.assertTrue(any("max_display_width" in error for error in errors))
        self.assertTrue(any("max_display_height" in error for error in errors))
        self.assertTrue(any("timer0_interrupt" in error for error in errors))
        self.assertTrue(any("CSR uart" in error for error in errors))

    def test_reports_missing_memory_fields(self):
        config = valid_config()
        del config["memories"]["plic"]["size"]

        errors = linux_check.validate_linux_config(config)

        self.assertIn("memory plic: base or size missing", errors)


if __name__ == "__main__":
    unittest.main()
