#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 10:15:01 2022

@author: fabian
"""
from powersimdata.input.grid import Grid
from powersimdata.input.export_data import export_to_pypsa


def assert_columns_preserved(n):
    assert "Vmax" in n.buses
    assert "ramp_10" in n.generators
    assert "rateB" in n.lines
    assert "QminF" in n.links


def assert_columns_deleted(n):
    assert "Vmax" not in n.buses
    assert "ramp_10" not in n.generators
    assert "rateB" not in n.lines
    assert "QminF" not in n.links


def test_export_grid_to_pypsa():
    grid = Grid("USA")
    
    n = export_to_pypsa(grid)
    assert len(n.snapshots) == 1
    assert not n.loads_t.p.empty
    assert not n.generators_t.p.empty
    assert len(n.buses) == len(grid.sub) + len(grid.bus)
    assert_columns_deleted(n)

    n = export_to_pypsa(grid, preserve_all_columns=True)
    assert len(n.snapshots) == 1
    assert not n.loads_t.p.empty
    assert not n.generators_t.p.empty
    assert len(n.buses) == len(grid.sub) + len(grid.bus)
    assert_columns_preserved(n)
