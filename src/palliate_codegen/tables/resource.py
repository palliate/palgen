from palliate_codegen.parser import parser
from pathlib import Path


class resource(parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _resolve_path(self, name, resource):
        # default to relative path
        path = self.source_map[name] \
            if 'relative' not in resource or resource['relative'] \
            else self.root_path
        path /= resource['path']
        return path.resolve().absolute()

    def validate(self):
        for name, resource in self.table.items():
            if 'path' not in resource:
                raise KeyError(f"Resource {name} does not specify a path.")

            resource["path"] = self._resolve_path(name, resource)
            if not resource["path"].exists():
                raise FileNotFoundError(
                    f"File for resource {name} (located at {resource['path']}) not found.")
            if not resource["path"].is_file():
                raise IOError(
                    f"Path for resource {name} (located at {resource['path']}) does not point to a file.")

    def render(self):
        template = self.env.get_template("resource.h.in")
        mapping = []
        for name, resource in self.table.items():
            data = ""
            with open(resource["path"], 'rb') as file:
                indent = 6
                count = 0
                while byte := file.read(1):
                    tmp = f"{ord(byte)}, "
                    count += len(tmp)
                    if count >= 80:
                        count = indent
                        data += f"\n{' ' * indent}"

                    data += tmp
            mapping.append({"name": name, "data": data})

        self.output[self.out_path /
                    "resource.h"] = template.render({"resources": mapping})
