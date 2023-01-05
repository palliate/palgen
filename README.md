# codegen
Code generation utility

## Project structure

- no builtin templates, all generation is user-defined
- optional toml-schema for `# coding: toml-schema` support
- optional pydantic schemas

## Minimum required project settings

Every project must include a file called `palgen.toml` at its project root.

Builtin settings:
```toml
[project]
  name = "ProjectName"
  version = "v0.1"
  folders = ["src"]

[templates] # optional
  folders = ["templates"] # optional
```

## Template definition
TODO decide whether templates should be defined in-source or in another directory
### Python
Create a parser, you can name it whatever you want but the file extension must be `.py`. You must define exactly one parser class which inherits from `palgen.parser.Parser`, its name does not matter.

TODO decide whether class name, file name or parent folder name should indicate what data we care about

Let's define a template called `test`. First define a parser, let's put that in `parser.py`
```py
from palgen.parser import Parser

class Test(Parser):
  class Settings(BaseModel):
    ''' Template settings. Must be provided from `palgen.toml` '''
    name: str

  class Config(BaseModel):
    ''' Template input. Can be provided from multiple `config.toml` '''

    class Types(str, Enum):
      APPLICATION = "application"
      LIBRARY = "library"
      PLUGIN = "plugin"

    type: Types
    description: Optional[str] = ""

  def prepare(self):
    ''' Transform input to data ready to be rendered '''
    pass

  def render(self):
    ''' Render the template '''
    pass
```
note that you can load schemas from `.toml` files as well:
```py
from palgen.parser import Parser

class Test(Parser):
  Schemas = "schema.toml"

  ...
```

TODO inline toml?

now define a template to render data into, let's call that `test.h.in`
```cpp
#pragma once
#include <string_view>

namespace Tests {
struct Test {
  std::string_view name;
  std::string_view type;
  std::string_view description;
};

static const Test @name; = {
  .name = "@name;",
  .type = "@type;",
@{- if description }
  .description = "@description;",
@{- endif }
};
}
```

### TOML
If you do not need to do transformations on input data or custom rendering you can simply define schemas and a template definition.

Let's reuse the template definition `test.h.in` from the previous example. First define some schemas.

Let's put this in `schema.toml`
```toml
[Settings]
  # ...
[Config]
  # ...
[Test]
  template = "test.h.in"
  output = "test.h" # optional
```

## Template rendering workflow
Preparation
- Load and parse `palgen.toml`
- Load templates, construct all enabled ones with settings from `palgen.toml`
- Find all `config.toml` files in the configured source folder
- Collect data

Rendering - this will be done for all enabled templates
- call `prepare()` of template
- call `render()` of template
- call `write()` of template
- call `finish()` of template

## Glossary
| Term    | Meaning |
|---------|---------|
| template | User-defined transformations to usable data
| setting | Template settings, defined in one `palgen.toml` per project |
| config  | Template inputs, defined in possibly multiple `config.toml` within the project's source tree |