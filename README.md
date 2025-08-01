# Spoofy Archiver

## Install

Install via [uv](https://docs.astral.sh/uv/getting-started/installation/) or [pipx](https://pipx.pypa.io/stable/installation/):

```bash
uv tool install git+https://github.com/kism/spoofy-archiver
```

```bash
pipx install git+https://github.com/kism/spoofy-archiver
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
