from argparse import ArgumentParser
from restify_me import restify
import glob, os


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


def restify_text_peps(pep_repo_path):
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
    for filename in text_peps(pep_repo_path):
        try:
            restify(filename)
        except Exception as e:
            failed.append((filename, e))

        else:
            success.append(filename)

    print("Found {} PEPs still in plain text".format(len(failed) + len(success)))
    print("{} text PEPs converted :D".format(len(success)))
    print("Failed to reSTify {} PEPs :(".format(len(failed)))
    for filename, error in failed:
        print("{} because: {} :(".format(
            filename, error))


if __name__ == '__main__':
    parser = ArgumentParser(description="Collect plain text PEPs")
    parser.add_argument("pep_path")
    args = parser.parse_args()
    restify_text_peps(args.pep_path)
