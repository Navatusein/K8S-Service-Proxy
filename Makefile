.PHONY: venv install run add clean pyinstaller-install build

build:
	pyinstaller --onefile main.py --name k8s-sp --specpath dist
