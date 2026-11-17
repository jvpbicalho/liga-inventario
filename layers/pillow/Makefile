# O CloudShell é x86_64, mas as Lambdas rodam em arm64: baixamos os pacotes já compilados para arm64.
build-PillowLayer:
	pip3 install pillow \
		--platform manylinux2014_aarch64 --platform manylinux_2_28_aarch64 \
		--only-binary=:all: --python-version 3.13 --implementation cp \
		--target "$(ARTIFACTS_DIR)/python"
