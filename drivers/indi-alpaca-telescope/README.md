# INDI Alpaca telescope timed-guide extension

These files are replacements for:

```text
drivers/telescope/indi_alpaca_telescope.cpp
drivers/telescope/indi_alpaca_telescope.h
```

in the official INDI source tree at tag `v2.2.5` (commit `1dd9b34` on the
reference build). They add `TELESCOPE_TIMED_GUIDE_NS` and
`TELESCOPE_TIMED_GUIDE_WE` and translate guide directions to the Alpaca
`pulseguide` API.

Build and install with `../../scripts/build-indi-driver.sh`. Do not install a
binary built from an arbitrary newer INDI branch against v2.2.5 libraries;
that combination previously failed because of an ABI mismatch.

