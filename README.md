# Spoofy Archiver

[![Check](https://github.com/kism/spoofy-archiver/actions/workflows/check.yml/badge.svg)](https://github.com/kism/spoofy-archiver/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/spoofy-archiver/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/spoofy-archiver/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/spoofy-archiver/actions/workflows/test.yml/badge.svg)](https://github.com/kism/spoofy-archiver/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/spoofy-archiver/graph/badge.svg?token=aXeqc3G5Rp)](https://codecov.io/gh/kism/spoofy-archiver)

## Install

Install via [uv](https://docs.astral.sh/uv/getting-started/installation/) or [pipx](https://pipx.pypa.io/stable/installation/):

```bash
uv tool install git+https://github.com/kism/spoofy-archiver
```

```bash
pipx install git+https://github.com/kism/spoofy-archiver
```

If your system default python is not 3.12+

```bash
pipx install --python python3.12 git+https://github.com/kism/spoofy-archiver
```

## Run

```bash
spoofyarchiver --help
```

Download your liked albums to a directory, if you don't specify a directory it will default to `<current dir>/output`:

```bash
spoofyarchiver -o /path/to/your/dir
```

Download a an item from a URL:

```bash
spoofyarchiver -o /path/to/your/dir <url>
```

Run the cli in interactive mode:

```bash
spoofyarchiver --interactive -o /path/to/your/dir
```

## Uninstall

```bash
uv tool uninstall spoofyarchiver
```

```bash
pipx uninstall spoofyarchiver
```
