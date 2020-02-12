# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2020 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import re
import io

# for type annotations:
if False: from typing import (  # noqa, pylint: disable=all
    Callable, Dict, Iterable, List, Optional, Tuple,
)


# helper functions

def prep_decision_string(code):
    # remove whitespace and eventual comments for the analysis, mitigate the chance of collision with variable names
    return " " + (code.strip().split("//")[0].split("/*")[0])


def is_a_branch_statement(code):
    return any(s in prep_decision_string(code) for s in (" if(", " if (", " case ", " default:"))


def is_a_oneline_branch(code):
    return re.match(r"^[^;]+{.+;+.+}$", prep_decision_string(code)) is not None


def is_a_compact_branch(code):
    return (is_a_branch_statement(code) and is_a_oneline_branch(code))


def is_a_loop(code):
    compare_string = prep_decision_string(code)
    if any(s in compare_string for s in (" while(", " while (", "}while(", " for ", " for(")):
        return True


def get_branch_type(code):
    compare_string = prep_decision_string(code)
    if any(s in compare_string for s in (" if(", " if (")):
        return "if"
    elif any(s in compare_string for s in (" case ", " default:")):
        return "switch"
    return ""


class DecisionParser(object):
    r"""Parses the decisions of a source file.

    Args:
        fname:
            File name of the active source file.
        covdata:
            Reference to the active coverage data.
        options:
            Active options of the instance
        logger:
            The logger to which decision analysis logs should be written to.
    """

    def __init__(self, fname, coverage, options, logger):
        self.fname = fname
        self.coverage = coverage
        self.options = options
        self.logger = logger
        self.source_lines = []

        # status variables for decision analysis
        self.decision_analysis_active = False  # set to True, once we're in the process of analyzing a branch
        self.last_decision_line = 0
        self.last_decision_line_exec_count = 0
        self.last_decision_type = "if"  # can be: "if" or "switch"
        self.decision_analysis_open_brackets = 0

    def parse_all_lines(self):
        self.logger.verbose_msg("Starting the decision analysis")

        # load all the lines of the source file
        with io.open(self.fname, 'r', encoding=self.options.source_encoding,
                     errors='replace') as source_file:
            for ctr, line in enumerate(source_file, 1):
                self.source_lines.append(line.rstrip())

        # start to iterate through the lines
        for lineno, code in enumerate(self.source_lines, 1):
            exec_count = self.coverage.line(lineno).count

            if not self.coverage.line(lineno).noncode:
                line_coverage = self.coverage.line(lineno)
                # analysis if a if-/else if-/else-branch is active
                if self.decision_analysis_active:
                    if self.decision_analysis_open_brackets == 0:
                        self.coverage.line(self.last_decision_line).decision(0).count = exec_count
                        self.coverage.line(self.last_decision_line).decision(1).count = self.last_decision_line_exec_count - exec_count

                        # disable the current decision analysis
                        self.decision_analysis_active = False
                        self.decision_analysis_open_brackets = 0

                    else:
                        # count amount of open/closed brackets to track when we can start checking if the block is executed
                        self.decision_analysis_open_brackets += prep_decision_string(code).count("(")
                        self.decision_analysis_open_brackets -= prep_decision_string(code).count(")")

                if not self.decision_analysis_active and (is_a_branch_statement(code) or is_a_loop(code)):
                    # If false, check the active line of code for a branch statement (if, else-if, switch)
                    if len(line_coverage.branches.items()) > 0:
                        if (is_a_compact_branch(code) or is_a_loop(code)):
                            # If it's a compact decision, we can only use the fallback to analyze simple decisions via branch calls
                            if len(line_coverage.branches.items()) == 2:
                                line_coverage.decision(0).update_count(line_coverage.branch(0).count)
                                line_coverage.decision(1).update_count(line_coverage.branch(1).count)
                            else:
                                line_coverage.decision(0).update_uncheckable(True)
                                line_coverage.decision(1).update_uncheckable(True)
                                self.logger.verbose_msg("Uncheckable decision at line {line}", line=lineno)
                        else:
                            # normal (non-compact) branch, analyze execution of following lines
                            self.decision_analysis_active = True
                            self.last_decision_line = lineno
                            self.last_decision_line_exec_count = line_coverage.count
                            self.last_decision_type = get_branch_type(code)
                            # count brakcets to make sure we're outside of the decision expression
                            self.decision_analysis_open_brackets += ("(" + prep_decision_string(code).split(" if(")[-1].split(" if (")[-1]).count("(")
                            self.decision_analysis_open_brackets -= ("(" + prep_decision_string(code).split(" if(")[-1].split(" if (")[-1]).count(")")
                    elif get_branch_type(code) == "switch":
                        # just use execution counts of case lines
                        line_coverage.decision(0).count = line_coverage.count

        self.logger.verbose_msg("Decision Analysis finished!")
