from powersimdata.utility.helpers import PrintManager

import pytest


def test_print_is_disabled(capsys):
    pm = PrintManager()
    pm.block_print()
    print("printout are disabled")
    captured = capsys.readouterr()
    assert captured.out == ""

    pm.enable_print()
    print("printout are enabled")
    captured = capsys.readouterr()
    assert captured.out == "printout are enabled\n"
