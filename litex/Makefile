.PHONY: build2 linux linux-check linux-dts linux-image linux-package

build2:
	python3 ./analogue_pocket.py --build
	cp ./build/litex/software/include/generated/regions.ld ../lang/linker/regions.ld
	cp ./build/litex/software/include/generated/output_format.ld ../lang/linker/output_format.ld

linux:
	python3 ./analogue_pocket.py --linux --build
	python3 ./linux_check.py

linux-check:
	python3 ./linux_check.py

linux-dts:
	python3 ./linux_dts.py

linux-image:
	python3 ./linux_image.py

linux-package: linux-dts
	python3 ./linux_image.py
