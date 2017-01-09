import os
from argparse import ArgumentParser
import re

PEP_HEADERS = [
    "PEP",
    "Title",
    "Version",
    "Last-Modified",
    "Author",
    "BDFL-Delegate",
    "Discussions-To",
    "Status",
    "Type",
    "Content-Type",
    "Requires",
    "Created",
    "Python-Version",
    "Post-History",
    "Replaces",
    "Superseded-By",
    "Resolution"
]

INLINE_LITERALS = []
with open("./inline-literals.txt") as file:
    INLINE_LITERALS = [line.strip() for line in file.readlines()]


NUMBERED_LIST_PATTERN = re.compile("\d+\. +")

class LineObj:
    """
    Represents a line in a PEP file
    """

    def __init__(self, line):
        self.original_line = line
        self.line = line
        self.is_code_block = False
        self.list_item_overflow = False
        self.list_item_prefix = None

    @property
    def indentation(self):
        return len(self.line) - len(self.line.lstrip())

    @property
    def is_indented(self):
        return self.indentation > 0

    @property
    def indentation_level(self):
        return int(self.indentation / 4)

    @property
    def is_blank(self):
        return len(self.line.strip()) == 0

    @property
    def is_pep_type_header(self):
        return self.line.lower().startswith("Type: ".lower())

    @property
    def is_content_type_header(self):
        return self.line.lower().startswith("Content-Type: ".lower())

    @property
    def deindent(self):
        if self.is_code_block:
            multiplier = 4
        else:
            multiplier = 3
        if self.indentation_level >= 1:
            if self.list_item_overflow:
                return "{}{}{}{}".format(" " * multiplier * (self.indentation_level -1),
                                 self.list_item_prefix,
                                 self.output.strip(),
                                 os.linesep)
            else:
                return "{}{}{}".format(" " * multiplier * (self.indentation_level -1),
                                 self.output.strip(),
                                 os.linesep)
        else:
            return self.output

    @property
    def is_local_vars(self):
        return self.line.strip().lower() == 'Local Variables:'.lower()

    @property
    def ends_with_colon(self):
        return self.line.rstrip().endswith(':')

    @property
    def output(self):
        try:
            if not self.is_code_block:
                if "*" in self.line \
                    and self.line.count("*") == 1 \
                    and len(self.line) > (self.line.index("*") + 1) \
                    and self.line[self.line.index("*") + 1] != " ":
                    self.line = self.line.replace("*", "\*")
                for inline_literal in INLINE_LITERALS:
                    if inline_literal in self.line and not self.is_pep_header:
                        self.line = self.line.replace(
                            inline_literal, "``{}``".format(inline_literal))

            if self.ends_with_colon \
                    and not self.is_pep_header \
                    and not self.is_code_block:
                return "{}:{}{}".format(self.line, os.linesep, os.linesep)
            else:
                return "{}{}".format(self.line, os.linesep)
        except Exception as e:
            print(f"failed at line {self.line} :(")
            raise e

    @property
    def section_header_underline(self):
        """
        underline for a section header
        """
        if self.indentation_level == 0:
            return "=" * len(self.line.strip(':'))
        elif self.indentation_level == 1:
            return "-" * len(self.line.strip(':'))
        else:
            return "'" * len(self.line.strip(':'))

    @property
    def is_pep_header(self):
        """
        returns True if line is a PEP header
        """
        stripped = self.line.lstrip()
        if ":" in stripped and stripped.index(":") > 0:
            text = stripped[:stripped.index(':')]
            if text in PEP_HEADERS:
                return True
        return False

    @property
    def is_list_item(self):
        """
        :return:
        """
        stripped = self.line.lstrip()
        if stripped.startswith('- ') or stripped.startswith('* '):
            self.list_item_prefix = '  '
            return True
        numbered_list = NUMBERED_LIST_PATTERN.match(stripped)
        if numbered_list:

            self.list_item_prefix = len(numbered_list.group())*" "
            return True




def is_section_heading(current_line, prev_line, next_line):
    """
    Detects first level section heading, which is
    a line that has empty line before and after
    """
    return (
        not current_line.is_blank
        and not current_line.is_indented
        and prev_line.is_blank
        and next_line
        and next_line.is_blank)


def is_missing_content_type_header(current_line, prev_line):
    """
    If there is a Type: header not followed by Content-type:, then
    we detects that Content type is missing from the file.
    """
    return prev_line.is_pep_type_header \
        and not current_line.is_content_type_header


class ConversionNotRequiredError(Exception):
    """
    Raised when PEP is already in text/x-rst format
    """
    def __init__(self, filename):
        self.message = "{} is already in text/x-rst format.".format(filename)


class TextToRest:
    """
    Read a text file and attempt to convert it to reST
    """

    def __init__(self, path):
        self.path = path
        self.outputs = []
        self.all_lines = []
        self.has_references_section = False
        self.has_local_vars_section = False
        self.is_references_section = False
        self.restifiable = True
        self.references = []
        self.last_ref_id = ""

        with open(self.path, 'r') as file:
            self.all_lines = file.readlines()
        if "Content-Type: text/x-rst\n".lower() in \
                map(lambda x: x.lower(), self.all_lines):
            self.restifiable = False
            raise ConversionNotRequiredError(path)

    @property
    def out_filename(self):
        return os.path.join(os.getcwd(), 'output', os.path.basename(self.path))

    def handle_content_type_header(self, current_line, prev_line):
        """
        if content type is missing, add it
        if content type is present, ensure it is rst
        """
        if current_line.is_content_type_header:
            # ensure it is reST
            self.outputs.append({"out": "Content-Type: text/x-rst"})
            self.outputs.append({"out": os.linesep})
        elif is_missing_content_type_header(
                current_line,
                prev_line):
            # content type header is missing, inject it
            self.outputs.append({"out": "Content-Type: text/x-rst"})
            self.outputs.append({"out": os.linesep})

    def process_local_vars(self):
        """ take care of Local variables at the end of PEP """
        local_vars = self.all_lines[
                     self.all_lines.index("Local Variables:\n"):]
        self.outputs.append({"out": ".."})
        self.outputs.append({"out": os.linesep})
        for line in local_vars:
            self.outputs.append({"out": "  {}".format(line),
                                 "original": line})

    def process_reference_line(self, line_obj):
        stripped_text = line_obj.output.strip()
        if line_obj.is_blank:
            self.outputs.append({"out": os.linesep})
        elif stripped_text.startswith('['):
            # figure out the reference number so we know how to indent
            self.last_ref_id = \
                stripped_text[stripped_text.index("[")+1:stripped_text.index("]")]
            self.references.append(self.last_ref_id)
            self.outputs.append(
                {"out": ".. {}".format(
                    stripped_text),
                "original": line_obj.original_line,
                "line_obj": line_obj})
            self.outputs.append({"out": os.linesep})
        else:
            self.outputs.append(
                {"out": "{}{}".format(
                    " " * (6 + len(self.last_ref_id)),
                    stripped_text),
                "original": line_obj.original_line,
                "line_obj": line_obj
                })
            self.outputs.append({"out": os.linesep})

    def handle_paragraph(self, line_obj):
        if line_obj.is_indented:
            self.outputs.append({"out": line_obj.deindent,
                                 "original": line_obj.original_line,
                                 "line_obj": line_obj})
        elif not line_obj.is_content_type_header:
            self.outputs.append({"out": line_obj.output,
                                 "original": line_obj.original_line,
                                 "line_obj": line_obj})

    def convert(self):
        """
        enumerate through all lines and process them one by one
        """
        for index, line in enumerate(self.all_lines):
            if index == 0:
                # this is the first line of the file, eg PEP: XXX header
                # just print it out as is
                self.outputs.append({"out": line})
            else:
                prev_line_obj = LineObj(self.all_lines[index-1].rstrip())
                current_line_obj = LineObj(line.rstrip())

                if not current_line_obj.is_blank:
                    found_blank_line = False

                    prev_line = self.outputs[-1]
                    prev_line_obj = LineObj(prev_line['out'])
                    if prev_line.get('line_obj'):
                        prev_line_obj = prev_line['line_obj']

                    if (prev_line_obj.is_list_item
                        or prev_line_obj.list_item_overflow) \
                            and not current_line_obj.is_list_item:
                        current_line_obj.list_item_overflow = True
                        current_line_obj.list_item_prefix = \
                            prev_line_obj.list_item_prefix

                    # look up the preceeding lines
                    # if the paragraph above is indented less than current
                    # and ends with colon,
                    # then the current line is likely a code block
                    for seen in reversed(self.outputs):
                        seen_obj = LineObj(seen['out'])
                        if seen.get('original'):
                            seen_obj = LineObj(seen['original'])

                        if not found_blank_line and seen_obj.is_blank:
                            found_blank_line = True

                        if found_blank_line and not seen_obj.is_blank \
                            and seen_obj.indentation_level \
                                        < current_line_obj.indentation_level:
                            if seen_obj.ends_with_colon:
                                current_line_obj.is_code_block = True
                            break

                else:
                    current_line_obj.list_item_overflow = False

                if index < (len(self.all_lines) - 1):
                    next_line_obj = LineObj(self.all_lines[index+1].rstrip())
                else:
                    next_line_obj = None

                self.handle_content_type_header(
                    current_line_obj, prev_line_obj)

                if is_section_heading(
                        current_line_obj,
                        prev_line_obj,
                        next_line_obj):
                    stripped = current_line_obj.line.rstrip(':')

                    # ensure there are two blank lines before section heading
                    if len(self.outputs[-2]['out'].strip()) > 0:
                        self.outputs.append({"out": os.linesep})

                    self.outputs.append({"out": stripped,
                                         "original": current_line_obj.original_line,
                                         "line_obj": current_line_obj
                                         })
                    self.outputs.append({"out": os.linesep})
                    self.outputs.append(
                        {"out": current_line_obj.section_header_underline,
                         "line_obj": current_line_obj})
                    self.outputs.append({"out": os.linesep})

                    if stripped.lower() == "References".lower():
                        self.is_references_section = True
                        self.has_references_section = True
                    elif self.is_references_section:
                        # we were in references section, and now moved on
                        self.is_references_section = False
                        self.last_ref_id = ""

                elif current_line_obj.is_local_vars:
                    self.has_local_vars_section = True
                    return

                else:
                    if self.is_references_section:
                        self.process_reference_line(current_line_obj)
                    else:
                        self.handle_paragraph(
                            current_line_obj
                        )

    def link_references(self):
        """
        go through everything one more time, updating links to references
        from
            [1]
        into
            [1]_
        """
        ref_section_index = [out['out'].lower() for out in self.outputs].index(
            "References".lower())

        for index, line in enumerate(self.outputs):

            for ref in self.references:
                potential_ref_link = "[{}]".format(ref)

                if potential_ref_link in line['out'] \
                        and index < ref_section_index:
                    line['out'] = line['out'].replace(
                        potential_ref_link,
                        "{}_".format(potential_ref_link))

                    self.outputs[index] = line

    def writeout(self):
        """
        write to result.rst
        :return:
        """
        with open(self.out_filename, 'w+') as file:
            for line_dict in self.outputs:
                file.write(line_dict['out'])


def restify(pep_filename):
    try:
        text_to_rest = TextToRest(pep_filename)
    except ConversionNotRequiredError as err:
        print(err.message)
    except FileNotFoundError:
        print("File {} is not found.".format(pep_filename))
    except Exception as e:
        print(f"Error in file {pep_filename}: {e.__repr__()} ")
        raise e
    else:
        text_to_rest.convert()
        if text_to_rest.has_local_vars_section:
            text_to_rest.process_local_vars()
        if text_to_rest.has_references_section:
            text_to_rest.link_references()
        text_to_rest.writeout()
        return text_to_rest


if __name__ == '__main__':
    parser = ArgumentParser(description="convert text to reST")
    parser.add_argument("filename")
    args = parser.parse_args()
    restify(args.filename)
