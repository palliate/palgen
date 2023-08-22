from hashlib import md5
from pathlib import Path
from typing import Iterable

from palgen import Extension, Sources, max_jobs
from palgen.ingest import Suffixes, Relative, Raw
from palgen.template.string import Template

# extension class must inherit from palgen.Extension


class Embed(Extension):
    ''' Converts arbitrary files to C arrays '''

    ingest = (Sources                       # Paths to all files
              >> Suffixes('.embed', position=0)  # Select files with .embed as first extension (ie foo.embed.bar)
              >> Relative                       # Convert paths to relative paths
              >> Raw)                           # Read in files as raw bytes

    def transform(self, data: Iterable[tuple[Path, bytes]]):
        for file, content in data:
            # remove the `.embed` suffix
            path = file.with_stem(file.name[: -len(''.join(file.suffixes))])

            # add `.hpp` suffix
            outpath = path.with_suffix(''.join([*file.suffixes[1:], '.hpp']))

            # hash the input path without the `.embed` suffix
            filehash = md5(bytes(str(path), encoding="utf-8")).hexdigest()

            # pass this along to the next step
            yield outpath, filehash, Template("resource.tpl.hpp")(hash = filehash,
                                                                  data = ','.join([hex(value)for value in content]),
                                                                  path = path)

    # this collects all previous results, so limit this to 1 job
    @max_jobs(1)
    def render(self, data: Iterable[tuple[Path, str, str]]):
        includes = []
        pairs = []
        for file, filehash, content in data:
            includes.append(f"Embed::r{filehash}")
            pairs.append(f"#include <{file}>")
            yield file, content

        indent = " " * 16
        yield Path('src') / 'embed.hpp', Template("embed.tpl.hpp")(amount   = len(pairs),
                                                                   pairs    = f',\n{indent}'.join(pairs),
                                                                   includes = '\n'.join(includes))
