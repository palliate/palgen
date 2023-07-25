from hashlib import md5
from pathlib import Path
from typing import Iterable

from palgen.ext import Extension, Sources, max_jobs
from palgen.ingest import Suffixes, Relative, Raw
from palgen.template.string import Template

# extension class must inherit from palgen.ext.Extension


class Embed(Extension):
    ''' Converts arbitrary files to C arrays '''

    ingest = (Sources                       # Paths to all files
          >> Suffixes('.embed', position=0) # Select files with .embed as first extension (ie foo.embed.bar)
          >> Relative                       # Convert paths to relative paths
          >> Raw)                           # Read in files as raw bytes

    @max_jobs(1)
    def render(self, data: Iterable[tuple[Path, bytes]]):
        collection: dict[str, Path] = {}
        for file, content in data:
            # remove the `.embed` suffix
            path = file.with_stem(file.name[: -len(''.join(file.suffixes))])
            # add `.hpp` suffix
            outpath = path.with_suffix(''.join([*file.suffixes[1:], '.hpp']))
            filehash = md5(bytes(str(path), encoding="utf-8")).hexdigest()

            collection[filehash] = outpath
            yield outpath, Template("resource.tpl.hpp")(hash=filehash,
                                                        data=','.join([hex(value) for value in content]),
                                                        path=path)
        indent = " " * 16

        pairs = f',\n{indent}'.join([f"Embed::r{_hash}" for _hash in collection])
        includes = '\n'.join([f"#include <{path}>" for path in collection.values()])

        yield Path('src') / 'embed.hpp', Template("embed.tpl.hpp")(amount=len(collection),
                                                                   pairs=pairs,
                                                                   includes=includes)
