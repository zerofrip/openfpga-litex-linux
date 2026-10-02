build2:
	python3 ./analogue_pocket.py --build
	cp ./build/litex/software/include/generated/regions.ld ../lang/linker/regions.ld
	cp ./build/litex/software/include/generated/output_format.ld ../lang/linker/output_format.ld

linux:
	python3 ./analogue_pocket.py --linux --build

linux-dts:
	python3 ./linux_dts.py
