#include <cstdio>
#include <format>
#include "info.h"

//workaround to fix syntax highlighting
#define f

int main() {
    puts(fR"""(Project info:
        Name:        {project_info.name}
        Version:     {project_info.version})""");
    puts(f"\
        Description: {project_info.description}");
}