from collections import defaultdict
import logging
from pathlib import Path
from typing import Any, Iterable

from palgen.ingest.filter import Suffix, Suffixes, Pattern
from palgen.ingest.loader import Json

from palgen.ext import Extension, Sources, Model
from palgen.template.jinja import Template


class TestResult(Model):
    implementation: str
    version: str

    exit_code: int
    success: bool
    duration: float

    packages: list[str]
    maxpkglen: int

class Tox(Extension):
    """ Generate pretty test reports from tox and pytest output.
    This is internal to palgen, you can find its implementation in docs/modules
    """

    ingest: dict[str, Sources] = {
        'tox': Sources >> Suffixes('.json') # TODO change json name so they have only one suffix
                       >> Pattern('*/test/*', unix=True)
                       >> Json,

        'test': Sources >> Suffix('.xml')
                        >> Pattern('*/test/*', unix=True)
    }

    def validate(self, data):
        yield from data

    def render_tox(self, data: list[tuple[Path, Any]]):
        out_path = self.root / 'docs' / 'test'

        tox_version = None
        tests: dict[str, dict[str, TestResult]] =  defaultdict(dict)

        for _, content in data:
            platform = content['platform']

            if tox_version is None:
                tox_version = content['toxversion']
            elif tox_version != content['toxversion']:
                logging.warning("Not all runs were executed with the same tox version")


            for key, node in content['testenvs'].items():
                if key == '.pkg':
                    continue
                if 'test' not in node:
                    continue

                packages = {}
                for package in node['installed_packages']:
                    if package.find(' @ ') != -1:
                        packages[package.split(' @ ')[0]] = 'local'
                        continue

                    name, value = package.split('==')
                    packages[name] = value

                maxlen = len(max(packages.keys(), key=len))
                packages = [f"``{pkg}``{' '*(maxlen - len(pkg) + 2)} {ver}"
                            for pkg, ver in packages.items()]

                tests[platform][key] = TestResult(
                    implementation=node['python']['implementation'],
                    version=node['python']['version'],

                    exit_code=node['result']['exit_code'],
                    success=node['result']['success'],
                    duration=node['result']['duration'],

                    packages=packages,
                    maxpkglen=maxlen)


        for platform, results in tests.items():
            yield out_path / f'{platform}.rst', Template('tox.rst.in').render(
                platform=platform.capitalize(),
                toxversion=tox_version,
                tests=results)

        yield out_path / 'index.rst', Template('index.rst.in').render(environments=tests.keys())

    def render_test(self, data: Iterable[Path]):
        out_path = self.root / 'docs' / 'test'

        for path in data:
            yield out_path / f'{path.stem}.rst', Template('test_report.rst.in').render(target=path.stem)
