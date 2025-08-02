# Spoofy Archiver

Tool to archive from streaming service Spoofy. Does not work with a free account.

[![Check](https://github.com/kism/spoofy-archiver/actions/workflows/check.yml/badge.svg)](https://github.com/kism/spoofy-archiver/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/spoofy-archiver/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/spoofy-archiver/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/spoofy-archiver/actions/workflows/test.yml/badge.svg)](https://github.com/kism/spoofy-archiver/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/spoofy-archiver/graph/badge.svg?token=aXeqc3G5Rp)](https://codecov.io/gh/kism/spoofy-archiver)

## Install

Install via [uv](https://docs.astral.sh/uv/getting-started/installation/) or [pipx](https://pipx.pypa.io/stable/installation/):

```bash
uv tool install spoofy-archiver
```

```bash
pipx install spoofy-archiver
```

If your system default python is not 3.11+

```bash
pipx install --python python3.11 spoofy-archiver
```

Pip works but I don't recommend it oustide of a virtual environment.

```bash
pip install spoofy-archiver
```

## Run

```bash
spoofy-archiver --help
```

Download your liked albums to a directory, if you don't specify a directory it will default to `<current dir>/output`:

```bash
spoofy-archiver -o /path/to/your/dir
```

Download a an item from a URL:

```bash
spoofy-archiver -o /path/to/your/dir <url>
```

Run the cli in interactive mode:

```bash
spoofy-archiver --interactive -o /path/to/your/dir
```

## Uninstall

```bash
uv tool uninstall spoofy-archiver
```

```bash
pipx uninstall spoofy-archiver
```

```bash
pip uninstall spoofy-archiver
```
