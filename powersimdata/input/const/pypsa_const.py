pypsa_const = {
    "bus": {
        "rename": {
            "lat": "y",
            "lon": "x",
            "baseKV": "v_nom",
            "type": "control",
            "Gs": "g_pu",
            "Bs": "b_pu",
        },
        "rename_t": {
            "Pd": "p",
            "Qd": "q",
            "Vm": "v_mag_pu",
            "Va": "v_ang",
        },
        "default_drop_cols": [
            "Vmax",
            "Vmin",
            "lam_P",
            "lam_Q",
            "mu_Vmax",
            "mu_Vmin",
            "GenFuelCost",
        ],
    },
    "generator": {
        "rename": {
            "bus_id": "bus",
            "Pmax": "p_nom",
            "Pmin": "p_min_pu",
            "startup_cost": "start_up_cost",  # not used here nor in pypsa_to_grid;
            "shutdown_cost": "shut_down_cost",  # not used here nor in pypsa_to_grid
            "ramp_30": "ramp_limit",  # in pypsa_to_grid: ramp_limit_up
            "type": "carrier",
        },
        "rename_t": {
            "Pg": "p",
            "Qg": "q",
            "status": "status",
        },
        "default_drop_cols": [
            "ramp_10",
            "mu_Pmax",
            "mu_Pmin",
            "mu_Qmax",
            "mu_Qmin",
            "ramp_agc",
            "Pc1",
            "Pc2",
            "Qc1min",
            "Qc1max",
            "Qc2min",
            "Qc2max",
            "GenIOB",
            "GenIOC",
            "GenIOD",
        ],
    },
    "gencost": {
        "rename": {
            "startup": "start_up_cost",
            "shutdown": "shut_down_cost",
            "c1": "marginal_cost",
        }
    },
    "branch": {
        "rename": {
            "from_bus_id": "bus0",
            "to_bus_id": "bus1",
            "rateA": "s_nom",
            "ratio": "tap_ratio",
            "x": "x_pu",
            "r": "r_pu",
            "g": "g_pu",  # not used in pypsa_to_grid
            "b": "b_pu",
        },
        "rename_t": {
            "Pf": "p0",
            "Qf": "q0",
            "Pt": "p1",
            "Qt": "q1",
        },
        "default_drop_cols": [
            "rateB",
            "rateC",
            "mu_St",
            "mu_angmin",
            "mu_angmax",
        ],
    },
    "link": {
        "rename": {
            "from_bus_id": "bus0",
            "to_bus_id": "bus1",
            "rateA": "s_nom",
            "ratio": "tap_ratio",
            "x": "x_pu",
            "r": "r_pu",
            "g": "g_pu",
            "b": "b_pu",
            "Pmin": "p_min_pu",
            "Pmax": "p_nom",
        },
        "rename_t": {
            "Pf": "p0",
            "Qf": "q0",
            "Pt": "p1",
            "Qt": "q1",
        },
        "default_drop_cols": [
            "QminF",
            "QmaxF",
            "QminT",
            "QmaxT",
            "muPmin",
            "muPmax",
            "muQminF",
            "muQmaxF",
            "muQminT",
            "muQmaxT",
        ],
    },
    "storage_gen": {
        "rename": {
            "bus_id": "bus",
            "Pg": "p",
            "Qg": "q",
        },
    },
    "storage_gencost": {
        "rename": {"c1": "marginal_cost"},
    },
    "storage_storagedata": {
        "rename": {
            "OutEff": "efficiency_dispatch",
            "InEff": "efficiency_store",
            "LossFactor": "standing_loss",
        },
    },
}
