import os
from argparse import ArgumentParser


class LineObj:
    """
    Represents a line in a PEP file
    """

    def __init__(self, line):
        self.line = line

    @property
    def indentation(self):
        return len(self.line) - len(self.line.strip())

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
        return self.line.startswith("Type: ")

    @property
    def is_content_type_header(self):
        return self.line.startswith("Content-Type: ")

    @property
    def deindent(self):
        if self.indentation_level >= 1:
            return "{}{}{}".format(" " * 3 * (self.indentation_level -1),
                                 self.output.strip(),
                                 os.linesep)
        else:
            return self.output

    @property
    def is_local_vars(self):
        return self.line == 'Local Variables:'

    @property
    def is_literal_block(self):
        return self.line.endswith(':')

    @property
    def output(self):
        if "*" in self.line and self.line.count("*") == 1 and \
                        self.line[self.line.index("*") + 1] != " ":
            self.line = self.line.replace("*", "``*``")

        if self.is_literal_block:
            return "{}:{}{}".format(self.line, os.linesep, os.linesep)
        else:
            return "{}{}".format(self.line, os.linesep)

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


def is_section_heading(current_line, prev_line, next_line):
    """
    Detects first level section heading, which is
    A line that has empty line before and after is a section heading
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


class TextToRest:
    """
    Read a text file and attempt to convert it to reST
    """
    temp_output_filename = "./result.rst"

    output = []
    all_lines = []

    is_references_section = False

    references = []

    last_ref_id = ""

    def __init__(self, path):
        self.path = path
        with open(self.path, 'r') as file:
            self.all_lines = file.readlines()

    def handle_content_type_header(self, current_line, prev_line):
        """
        if content type is missing, add it
        if content type is present, ensure it is rst
        :param current_line:
        :param prev_line:
        :return:
        """
        if current_line.is_content_type_header:
            # ensure it is reST
            self.output.append("Content-Type: text/x-rst")
            self.output.append(os.linesep)
        elif is_missing_content_type_header(
                current_line,
                prev_line):
            # content type header is missing, inject it
            self.output.append("Content-Type: text/x-rst")
            self.output.append(os.linesep)

    def process_local_vars(self):
        """ take care of Local variables at the end of PEP """
        local_vars = self.all_lines[
                     self.all_lines.index("Local Variables:\n"):]
        self.output.append("..")
        self.output.append(os.linesep)
        for line in local_vars:
            self.output.append("  {}".format(line))

    def process_reference_line(self, line_obj):
        stripped_text = line_obj.output.strip()
        if line_obj.is_blank:
            self.output.append(os.linesep)
        elif stripped_text.startswith('['):
            # figure out the reference number so we know how to indent
            self.last_ref_id = \
                stripped_text[stripped_text.index("[")+1:stripped_text.index("]")]
            self.references.append(self.last_ref_id)
            self.output.append(
                ".. {}".format(
                    stripped_text))
            self.output.append(os.linesep)
        else:
            self.output.append(
                "{}{}".format(
                    " " * (6 + len(self.last_ref_id)),
                    stripped_text))
            self.output.append(os.linesep)

    def handle_paragraph(self, line_obj):
        if line_obj.is_indented:
            self.output.append(line_obj.deindent)
        else:
            self.output.append(line_obj.output)

    def convert(self):
        """
        read all lines in file, and process them one by one
        """

        for index, line in enumerate(self.all_lines):
            if index == 0:
                # this is the first line of the file, eg PEP: XXX header
                # just print it out as is
                self.output.append(line)
            else:
                prev_line_obj = LineObj(self.all_lines[index-1].rstrip())
                current_line_obj = LineObj(line.rstrip())
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

                    self.output.append(stripped)
                    self.output.append(os.linesep)
                    self.output.append(
                        current_line_obj.section_header_underline)
                    self.output.append(os.linesep)
                    if stripped == "References":
                        self.is_references_section = True
                    elif self.is_references_section:
                        # we were in references section, and now moved on
                        self.is_references_section = False
                        self.last_ref_id = ""

                elif current_line_obj.is_local_vars:
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
        ref_section_index = self.output.index("References")
        for index, line in enumerate(self.output):
            for ref in self.references:
                potential_ref_link = "[{}]".format(ref)
                if potential_ref_link in line and index < ref_section_index:
                    line = line.replace(
                        potential_ref_link,
                        "{}_".format(potential_ref_link))
                    self.output[index] = line

    def writeout(self):
        """
        write to result.rst
        :return:
        """
        with open(self.temp_output_filename, 'w') as file:
            file.writelines(self.output)


if __name__ == '__main__':
    parser = ArgumentParser(description="convert text to reST")
    parser.add_argument("filename")
    args = parser.parse_args()
    text_to_rest = TextToRest(args.filename)
    text_to_rest.convert()
    text_to_rest.process_local_vars()
    text_to_rest.link_references()
    text_to_rest.writeout()