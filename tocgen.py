# from https://gist.github.com/elfnor/bc2176b3fad8581c678b771afb1e3b3e
# -*- coding: utf-8 -*-
"""
Generate a file tree table of contents for a directory of markdown files

run from command line:

    $ python md_file_tree.py

will generate a  markdown index of all markdown files in the current working
directory and its sub folders and insert it into  a file `index.md`.
If a previous index exists in the file it will be replaced,
otherwise a new index will be created at the end of the file
or a new file created.

The index will be linked to the files
eg.
`  - [how_to_take_notes.md](./notetaking/how_to_take_notes.md)`
for a link to a file `how_to_take_notes.md` in the sub-folder `notetaking`

Options:
the filename can be explicitly specified
 $ python md_file_tree.py README.md

-f:  The headers in each file will be listed under the file link
-w:  Wikilink syntax `[[./notetaking/how_to_take_notes.md]]`
     will be used instead of common markdown

author: elfnor <elfnor.com>
credit : the code in get_headers comes from
         https://github.com/amaiorano/md-to-toc
"""
import re
import os
import argparse

TOC_LIST_PREFIX = "-"
HEADER_LINE_RE = re.compile("^(#+)\s*(.*?)\s*(#+$|$)", re.IGNORECASE)
HEADER1_UNDERLINE_RE = re.compile("^-+$")
HEADER2_UNDERLINE_RE = re.compile("^=+$")


def toggles_block_quote(line):
    """Returns true if line toggles block quotes on or off
    (i.e. finds odd number of ```)"""
    n_block_quote = line.count("```")
    return n_block_quote > 0 and line.count("```") % 2 != 0


def get_headers(filename):
    """code  from https://github.com/amaiorano/md-to-toc"""
    in_block_quote = False
    results = []  # list of (header level, title, anchor) tuples
    last_line = ""

    with open(filename) as file:
        for line in file.readlines():

            if toggles_block_quote(line):
                in_block_quote = not in_block_quote

            if in_block_quote:
                continue

            found_header = False
            header_level = 0

            match = HEADER_LINE_RE.match(line)
            if match is not None:
                header_level = len(match.group(1))
                title = match.group(2)
                found_header = True

            if not found_header:
                match = HEADER1_UNDERLINE_RE.match(line)
                if match is not None:
                    header_level = 1
                    title = last_line.rstrip()
                    found_header = True

            if not found_header:
                match = HEADER2_UNDERLINE_RE.match(line)
                if match is not None:
                    header_level = 2
                    title = last_line.rstrip()
                    found_header = True

            if found_header:
                results.append((header_level, title))

            last_line = line
    return results


def create_index(cwd, headings=False, wikilinks=False):
    """ create markdown index of all markdown files in cwd and sub folders

    """
    base_len = len(cwd)
    base_level = cwd.count(os.sep)
    md_lines = []
    md_exts = ['.markdown', '.mdown', '.mkdn', '.mkd', '.md']
    md_lines.append('<!-- filetree -->\n\n')
    for root, dirs, files in os.walk(cwd):
        files = sorted([f for f in files if not f[0] == '.' and os.path.splitext(f)[-1] in md_exts])
        dirs[:] = sorted([d for d in dirs if not d[0] == '.'])
        if len(files) > 0:
            level = root.count(os.sep) - base_level
            indent = '  ' * level
            if root != cwd:
                indent = '  ' * (level - 1)
                md_lines.append('{0} {2} **{1}/**\n'.format(indent,
                                                            os.path.basename(root),
                                                            TOC_LIST_PREFIX))
            rel_dir = '.{1}{0}'.format(os.sep, root[base_len:])
            for md_filename in files:
                indent = '  ' * level
                if wikilinks:
                    md_lines.append('{0} {3} [[{2}{1}]]\n'.format(indent,
                                                                  os.path.splitext(md_filename)[0],
                                                                  rel_dir,
                                                                  TOC_LIST_PREFIX))
                else:
                    md_lines.append('{0} {3} [{1}]({2}{1})\n'.format(indent,
                                                                     md_filename,
                                                                     rel_dir,
                                                                     TOC_LIST_PREFIX))
                if headings:
                    results = get_headers(os.path.join(root, md_filename))
                    if len(results) > 0:
                        min_header_level = min(results, key=lambda e: e[0])[0]
                        for header in results:
                            header_level = header[0] - min_header_level + level + 2
                            indent = '  ' * header_level
                            md_lines.append("{}{} {}\n".format(indent, TOC_LIST_PREFIX, header[1]))

    md_lines.append('\n<!-- filetreestop -->\n')
    return md_lines


def replace_index(filename, new_index):
    """ finds the old index in filename and replaces it with the lines in new_index
    if no existing index places new index at end of file
    if file doesn't exist creates it and adds new index
    will only replace the first index block in file  (why would you have more?)
    """

    pre_index = []
    post_index = []
    pre = True
    post = False
    try:
        with open(filename, 'r') as md_in:
            for line in md_in:
                if '<!-- filetree' in line:
                    pre = False
                if '<!-- filetreestop' in line:
                    post = True
                if pre:
                    pre_index.append(line)
                if post:
                    post_index.append(line)
    except IOError:
        pass

    with open(filename, 'w') as md_out:
        md_out.writelines(pre_index)
        md_out.writelines(new_index)
        md_out.writelines(post_index[1:])


def main():
    """generate index optional cmd line arguments"""
    parser = argparse.ArgumentParser(
        description=('generate a markdown index tree of markdown files'
                     'in current working directory and its sub folders'))

    parser.add_argument('filename',
                        nargs='?',
                        default='index.md',
                        help="markdown output file")
    parser.add_argument('--full', '-f',
                        action='store_true',
                        help='list headers in files')
    parser.add_argument('--wikilinks', '-w',
                        action='store_true',
                        help='use [[link]] instead of [link.md](./link.md)')

    args = parser.parse_args()

    cwd = os.getcwd()
    md_lines = create_index(cwd, headings=args.full, wikilinks=args.wikilinks)

    md_out_fn = os.path.join(cwd, args.filename)
    replace_index(md_out_fn, md_lines)


if __name__ == "__main__":
    main()
