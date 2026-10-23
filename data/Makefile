# Oasis District synthetic data kit
.PHONY: all data docs labs check clean
all:            ## data + docs + Day 1 labs (same as: python -m oasis_datakit build)
	python -m generator build
data:
	python -m generator data
check:          ## rebuild and compare checksums with the committed ones
	cp data/lite_checksums.sha256 /tmp/oasis_prev.sha256 && python -m generator data && diff /tmp/oasis_prev.sha256 data/lite_checksums.sha256 && echo "identical ✓"
clean:
	rm -rf data/lite docs/validation_report.html
