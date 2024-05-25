from functools import reduce
import os
import shutil
import subprocess
from typing import List

import sys


DOCUMENT_DIR = "documents"
BEGIN_DIR = os.path.join("documents", "begin")
END_DIR = os.path.join("documents", "end")
CONTENT_DIR = os.path.join("documents", "content")


def create_pdf(slug: str, tex: str, verbose: bool) -> str:
    with open(f"out/tmp/{slug}.tex", "w") as f:
        f.write(tex)
        print(f"Rendered {slug}")

    verbose_params = ["-halt-on-error"] if verbose else ["-interaction=nonstopmode"]

    params = [
        "pdflatex",
        *verbose_params,
        "-output-directory=out/tmp",
        f"out/tmp/{slug}.tex",
    ]
    if verbose:
        subprocess.call(params)
    else:
        subprocess.call(params, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    target_path = f"out/{slug}.pdf"
    # Copy the resulting pdf to the out directory
    shutil.copy(f"out/tmp/{slug}.pdf", target_path)
    return target_path


def get_nested_dirs(dir: str, overrides: List[str]) -> List[str]:
    return [dir] + [
        nested_dir
        for override in overrides
        if os.path.isdir(os.path.join(dir, override))
        for nested_dir in get_nested_dirs(os.path.join(dir, override), overrides)
    ]


"""
Idea here:
- Get all files in the directory in the order of the prefix number
- If one of the overrides matches a nested dir in the directory, for the files in that dir, do the following:
    - Override for the same names in the parent dir
    - Inserted to the list if not in the parent dir

    
"""


def get_dir_content_with_overrides(root_dir: str, overrides: List[str]) -> str:
    # get recursively all subdirectories matching overrides
    # later overrides take precedence ä

    all_dirs = get_nested_dirs(root_dir, overrides)

    paths_by_file = {}

    for root_dir in all_dirs:
        for file in os.listdir(root_dir):
            path = os.path.join(root_dir, file)

            if not os.path.isdir(path) and path.endswith(".tex"):
                paths_by_file[file] = path


    paths = [paths_by_file[key] for key in sorted(paths_by_file.keys())]
    for path in paths:
        assert os.path.isfile(path)
        assert path.endswith(".tex")

    return "\n".join(["\input{" + path + "}" for path in paths])


def create_content(
    content_name: str, job_name: str, overrides: List[str], verbose: bool
) -> str:
    overrides = [content_name] + overrides
    content = "\n\n".join(
        get_dir_content_with_overrides(dir, overrides)
        for dir in [BEGIN_DIR, CONTENT_DIR, END_DIR]
    )

    slug = f"{job_name}_{content_name}"
    export_path = create_pdf(slug, content, verbose)
    return export_path


def render_application(*parameters: str):
    overrides = list(filter(lambda x: not x.startswith("-"), parameters))

    unite = "-unite" in parameters or "-u" in parameters
    verbose = "-verbose" in parameters or "-v" in parameters

    print(f"Run verbose: {verbose}, Unite: {unite}, Overrides: {overrides}")
    job_name = "default" if len(overrides) == 0 else "-".join(overrides)

    content_names = [os.path.basename(content) for content in os.listdir(CONTENT_DIR)]

    exported_paths = [
        create_content(content_name, job_name, overrides, verbose)
        for content_name in content_names
    ]

    if unite:
        subprocess.call(
            [
                "pdfunite",
                *exported_paths,
                # *references,
                f"documents/out/{job_name}_application.pdf",
            ],
        )


if __name__ == "__main__":
    render_application(*sys.argv[1:])
