# Systemd syntax parser and writer

<!--toc:start-->

- [Systemd syntax parser and writer](#systemd-syntax-parser-and-writer)
  - [Reader](#reader)
    - [Features](#features)
    - [Example](#example)
    - [TODO](#todo)
  - [Writer](#writer)
    - [Features](#features-1)
<!--toc:end-->

Most feature-complete python systemd parser.
More information on Systemd file syntax here:
<https://www.freedesktop.org/software/systemd/man/devel/systemd.syntax.html>.

## Reader

`systemd_config.reader.parse()`

### Features

- beginning and trailing whitespace is ignored
- inline comments are not supported (as systemd syntax defines)
- comments inside multiline values are supported (as systemd syntax defines)
- multiline values are concatenated into a single string (excluding comments)
- duplicate sections become a `list` of sections contents under a single key
- duplicate keys become a `list` of values under a single key
- empty value resets previously set values
- empty section (header with no keys) will be ignored
- section and key comparison is [caseless](https://docs.python.org/3/library/stdtypes.html#str.casefold), but preserving case;
  first occurence met in file will be used as a key
- comments can be collected and returned as a second structure, to be passed
  later to `writer.dump()` function

### Limitations

- character quoting is not currently implemented
- comments are always kept with the next significant line: section or key,
  if you write comments after keys or section names -- this may lead to
  unexpected results
- comments after the last section will always be kept at the end of file
- comments inside multiline values will be written before corresponding key

### Example

```python
with open("wireguard.netdev") as fp:
    config = parse(
        fp,
        # force-convert WireguardPeer section to list
        {"Wireguardpeer": lambda v: v if isinstance(v, list) else [v]},
        # split AllowedIPs by ','
        {"allowedips": lambda v: v if isinstance(v, list) else list(filter(None, v.split(','))),
        # convert ListenPort to `int`
        'listenport': int},
    )
```

### TODO

Implement Quoting support: <https://www.freedesktop.org/software/systemd/man/devel/systemd.syntax.html>

## Writer

`systemd_config.writer.dump()`

### Features

- Writes provided `structure` as Systemd config file.
- Adds comments to output, if `comments` structure is provided.

### TODO

- Implement proper Quoting
