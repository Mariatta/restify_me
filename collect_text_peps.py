from argparse import ArgumentParser
from operator import itemgetter
from restify_me import restify

import glob, os
import shutil

BACKUPS_DIR = "./backups"
MAX_TO_COPY = 1
def clear_output_dir():
    """
    remove output from previous run
    """
    files = glob.glob(os.path.join(os.getcwd(), 'output', 'pep-*.txt'))
    for f in files:
        os.remove(f)


def text_peps(pep_repo_path):
    """
    return PEPs still in plain text
    """
    for filename in glob.glob(os.path.join(pep_repo_path, "pep-*.txt")):
        with open(filename, 'r') as pep_file:
            has_content_type = False
            for line in pep_file.readlines():
                if line.lower().startswith("Content-Type:".lower()):
                    has_content_type = True
                    if "text/plain" in line:
                        yield filename
            if not has_content_type:
                yield filename


def restify_text_peps(pep_repo_path, copy_to_origin=False):
    """
    1. find all plain text PEPs
    2. restify
    TODO:
    3. run pep2html.py
    4. open with webbrowser
    """
    failed = []
    success = []
    clear_output_dir()
    if copy_to_origin:
        if not os.path.exists("./backups"):
            os.makedirs("./backups")
    for filename in text_peps(pep_repo_path):
        try:
            restify(filename)
        except Exception as e:
            failed.append((filename, e))

        else:
            success.append(filename)

    print("Found {} PEPs still in plain text".format(len(failed) + len(success)))
    print("{} text PEPs converted :D".format(len(success)))
    if failed:
        print("Failed to reSTify {} PEPs :(".format(len(failed)))
        for filename, error in failed:
            print("{} because: {} :(".format(
                filename, error))

    files_and_length = []
    for s in success:
        output_filename = s.replace("../peps", "./output")
        with open(output_filename) as output_file:
            file_length = len(output_file.readlines())
            files_and_length.append({'filename': output_filename,
                                     'file_length': file_length,
                                     'original_filename': s
                                     })

    sorted_list = sorted(files_and_length, key=itemgetter('file_length'))

    num_to_copy = 0
    for item in sorted_list:
        print(f"{item['filename']}, {item['file_length']} lines")
        if copy_to_origin and num_to_copy < 1:
            origin_path = item['original_filename']
            backup_path = origin_path.replace("../peps", BACKUPS_DIR)
            shutil.copy(origin_path, backup_path)
            shutil.copy(item['filename'], origin_path)
            print(f"backed up and copied {item['filename']}")
            num_to_copy = num_to_copy + 1


if __name__ == '__main__':
    parser = ArgumentParser(description="Collect plain text PEPs")
    parser.add_argument("pep_path")
    parser.add_argument('--copy', dest='copy', action='store_true')
    parser.set_defaults(feature=True)
    args = parser.parse_args()
    restify_text_peps(args.pep_path, args.copy)


