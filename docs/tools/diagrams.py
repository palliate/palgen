import contextlib
import logging
from multiprocessing import Process
import os
from pathlib import Path
from typing import Iterable
from pylint.pyreverse.main import Run
import pydot

from palgen.ingest import Suffix, Folder, Relative, Absolute
from palgen import Extension, Sources, max_jobs
from palgen.loaders.ast_helper import AST

def run_pyreverse(cwd: Path, args):
    cwd.mkdir(exist_ok=True, parents=True)
    os.chdir(cwd)
    Run(args)

class Diagrams(Extension):
    """Generate pretty diagrams using pyreverse.
       This is internal to palgen, you can find its implementation in docs/modules
    """

    def get_ast(self, data):
        for file in data:
            with contextlib.suppress(Exception):
                yield AST.load(file)

    ingest = Sources >> Relative >> Folder('src') >> Suffix('.py') >> Absolute >> get_ast

    def validate(self, data):
        yield from data

    @max_jobs(1)
    def transform(self, data: list[AST]):
        classes: list[str] = []
        for ast in data:
            if not ast.path:
                continue
            path = ast.path.relative_to(self.root_path / 'src')
            name = path.parts[:-1]

            if path.name != '__init__.py':
                name = [*name, path.stem]
            classes.extend('.'.join([*name, class_.name]) for class_ in ast.classes)

        #TODO get project name
        args = ['-o', 'dot',
                str(self.root_path / 'src' / 'palgen')]

        for class_ in classes:
            args.extend(('-c', class_))

        proc = Process(target=run_pyreverse, args=(self.out_path / "diagrams", args))
        proc.start()
        proc.join()
        yield from classes

    def render(self, classes: Iterable[str]):
        for class_ in classes:
            file: Path = self.out_path / "diagrams" / f"{class_}.dot"
            graphs = pydot.graph_from_dot_file(file, 'utf-8')
            if not graphs:
                continue

            if len(graphs) != 1:
                logging.warning("%s defines more than one graph.", file)
                continue

            graph: pydot.Graph = graphs[0]

            if not graph:
                continue

            for node in graph.get_nodes():
                assert isinstance(node, pydot.Node)
                attributes: dict[str, str] = node.get_attributes()

                # fix colors
                for field in 'color', 'fontcolor':
                    if field in attributes and attributes[field] == '"black"':
                        attributes[field] = '"var(--color-content-foreground)"'

                if (name := node.get_name()).startswith('"palgen.'):
                    # documentation links
                    attributes['xref'] = f'":py:class:`{name[1:-1]}`"'
                elif 'label' in attributes:
                    # remove extra data, only print name
                    del attributes['label']

                # fix text overlapping the box
                attributes['margin'] = '"0.2,0.1"'

            graph.del_node('"\\n"')

            for edge in graph.get_edges():
                assert isinstance(edge, pydot.Edge)
                attributes: dict[str, str] = edge.get_attributes()
                attributes['stroke'] = '"var(--color-content-foreground)"'

            yield file, graph.to_string()
