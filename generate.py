import os
import shutil
import subprocess
from typing import List
from pypdf import PdfWriter

import sys


DOCUMENT_DIR = "documents"
BEGIN_DIR = os.path.join("documents", "begin")
END_DIR = os.path.join("documents", "end")
CONTENT_DIR = os.path.join("documents", "content")

SUPPLEMENTS_DIR = "supplements"

OUTPUT_DIR = "out"

TMP_DIR = f"{OUTPUT_DIR}/tmp"


def create_pdf(slug: str, tex: str, verbose: bool) -> str:
    tex_path = os.path.join(TMP_DIR, f"{slug}.tex")
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    with open(tex_path, "w") as f:
        f.write(tex)
        print(f"Rendered {slug}")

    verbose_params = ["-halt-on-error"] if verbose else ["-interaction=nonstopmode"]

    params = [
        "pdflatex",
        *verbose_params,
        "-output-directory=out/tmp",
        tex_path,
    ]
    if verbose:
        subprocess.call(params)
    else:
        subprocess.call(params, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    tmp_pdf_path = os.path.join(TMP_DIR, f"{slug}.pdf")
    target_path = os.path.join(OUTPUT_DIR, f"{slug}.pdf")
    # Copy the resulting pdf to the out directory
    shutil.copy(tmp_pdf_path, target_path)
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

    return "\n".join(["\\input{" + path + "}" for path in paths])


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


def get_supplements_paths(overrides: List[str]) -> List[str]:

    possible_config_paths = [os.path.join(SUPPLEMENTS_DIR, "supplements")] + [
        os.path.join(SUPPLEMENTS_DIR, f"supplements-{override}") for override in overrides
    ]

    config_paths = list(filter(os.path.isfile, possible_config_paths))

    if len(config_paths) == 0:
        print("No supplements found")
        return []
    # last one takes precedence
    config = config_paths[-1]
    print("Using the config %s" % config)

    with open(config, "r") as f:
        supplement_file_names = f.read().strip().split("\n")
    supplement_paths = [
        os.path.join(SUPPLEMENTS_DIR, file) for file in supplement_file_names
    ]

    return list(filter(os.path.isfile, supplement_paths))


def create_united_content(
    job_name: str, exported_paths: List[str], supplements: List[str]
):

    with PdfWriter() as writer:
        for pdf in exported_paths + supplements:
            writer.append(pdf)

        path = os.path.join(OUTPUT_DIR, f"{job_name}_application.pdf")
        writer.write(path)


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
        supplements = get_supplements_paths(overrides)
        create_united_content(job_name, exported_paths, supplements)


if __name__ == "__main__":
    render_application(*sys.argv[1:])
