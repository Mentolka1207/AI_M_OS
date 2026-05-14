BIN     := aifs-daemon

CLI     := aifs

PREFIX  := /usr/local/bin



.PHONY: all build install clean



all: build



build:

	cd daemon && go build -o ../build/$(BIN) .

	cp cli/aifs.py build/$(CLI)

	chmod +x build/$(CLI)



install: build

	install -Dm755 build/$(BIN) $(PREFIX)/$(BIN)

	install -Dm755 build/$(CLI) $(PREFIX)/$(CLI)

	install -Dm644 systemd/aimos-aifs.service /etc/systemd/system/aimos-aifs.service

	systemctl daemon-reload

	@echo "Run: systemctl enable --now aimos-aifs"



clean:

	rm -rf build/

