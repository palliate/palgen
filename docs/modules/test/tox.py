import logging
from pathlib import Path
from typing import Iterable

from palgen.ingest.filter import Extension, Stem, Pattern
from palgen.ingest.loader import Json

from palgen.module import Module, Sources, Model
from palgen.integrations.jinja2.template import Template


class TestResult(Model):
    implementation: str
    version: str

    exit_code: int
    success: bool
    duration: float

    packages: list[str]
    maxpkglen: int

class Tox(Module):
    ''' Sources module help text. Spliced after the dot '''

    ingest: dict[str, Sources] = {
        'tox': Sources >> Extension('.json')
                       >> Stem('*-tox', unix=True)
                       >> Pattern('*/test/*', unix=True)
                       >> Json,

        'test': Sources >> Extension('.xml')
                        >> Pattern('*/test/*', unix=True)
    }

    def validate(self, data):
        yield from data

    def render_tox(self, data):
        out_path = self.root_path / 'docs' / 'test'
        logging.warning('tox')
        environments = []
        for _, content in data:
            platform = content['platform']
            tests = {}

            testenvs = content['testenvs']
            for key, node in testenvs.items():
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

                tests[key] = TestResult(
                    implementation=node['python']['implementation'],
                    version=node['python']['version'],

                    exit_code=node['result']['exit_code'],
                    success=node['result']['success'],
                    duration=node['result']['duration'],

                    packages=packages,
                    maxpkglen=maxlen
                )

            environments.append(f'{platform}-test')
            yield out_path / f'{platform}-test.rst', Template('tox.rst.in')(
                platform=platform.capitalize(),
                toxversion=content['toxversion'],
                tests=tests
            )
        yield out_path / 'index.rst', Template('index.rst.in')(environments=environments)

    def render_test(self, data: Iterable[Path]):
        out_path = self.root_path / 'docs' / 'test'

        logging.info('Generating test reports')
        for path in data:
            yield out_path / f'{path.stem}.rst', Template('test_report.rst.in')(
                target=path.stem
            )
