import numpy as np
import pandas as pd

from powersimdata.input.converter.reise_to_grid import format_gencost, link


def test_format_gencost_polynomial_only_same_n():
    df_input = pd.DataFrame(
        {
            0: [2, 2, 2],
            1: [0.0, 0.0, 0.0],
            2: [0.0, 0.0, 0.0],
            3: [4, 4, 4],
            4: [1.1, 1.2, 1.3],
            5: [2.7] * 3,
            6: [0.1, 0.2, 0.3],
            7: [1.0, 1.0, 2.0],
        },
        index=[1, 2, 3],
    )
    df_output = format_gencost(df_input)
    assert np.array_equal(
        df_output.columns, ["type", "startup", "shutdown", "n", "c3", "c2", "c1", "c0"]
    )
    assert np.array_equal(
        df_output.loc[1, ["c0", "c1", "c2", "c3"]].values, [1.0, 0.1, 2.7, 1.1]
    )


def test_format_gencost_polynomial_only_different_n():
    df_input = pd.DataFrame(
        {
            0: [2, 2, 2, 2],
            1: [0.0, 0.0, 0.0, 0.0],
            2: [0.0, 0.0, 0.0, 0.0],
            3: [4, 2, 3, 2],
            4: [1.1, 0.2, 1.1, 0.4],
            5: [2.7, 1.0, 0.3, 1.0],
            6: [0.1, 0.0, 2.0, 0.0],
            7: [1.0, 0.0, 0.0, 0.0],
        },
        index=[1, 2, 3, 4],
    )
    df_output = format_gencost(df_input)
    assert np.array_equal(
        df_output.columns, ["type", "startup", "shutdown", "n", "c3", "c2", "c1", "c0"]
    )
    assert np.array_equal(
        df_output.loc[1, ["c0", "c1", "c2", "c3"]].values, [1.0, 0.1, 2.7, 1.1]
    )
    assert np.array_equal(
        df_output.loc[2, ["c0", "c1", "c2", "c3"]].values, [1.0, 0.2, 0.0, 0.0]
    )
    assert np.array_equal(
        df_output.loc[3, ["c0", "c1", "c2", "c3"]].values, [2.0, 0.3, 1.1, 0.0]
    )
    assert np.array_equal(
        df_output.loc[4, ["c0", "c1", "c2", "c3"]].values, [1.0, 0.4, 0.0, 0.0]
    )


def test_format_gencost_piece_wise_linear_only_same_n():
    df_input = pd.DataFrame(
        {
            0: [1, 1, 1],
            1: [0.0, 0.0, 0.0],
            2: [0.0, 0.0, 0.0],
            3: [3, 3, 3],
            4: [1.0, 2.0, 3.0],
            5: [2.7, 2.1, 2.5],
            6: [2.0, 3.0, 4.0],
            7: [4.8, 5.4, 7.3],
            8: [3.0, 4.0, 5.0],
            9: [10.6, 9.4, 17.7],
        },
        index=[1, 2, 3],
    )
    df_output = format_gencost(df_input)
    assert np.array_equal(
        df_output.columns,
        ["type", "startup", "shutdown", "n", "p1", "f1", "p2", "f2", "p3", "f3"],
    )


def test_format_gencost_piece_wise_linear_only_different_n():
    df_input = pd.DataFrame(
        {
            0: [1, 1, 1],
            1: [0.0, 0.0, 0.0],
            2: [0.0, 0.0, 0.0],
            3: [4, 3, 2],
            4: [1.0, 2.0, 3.0],
            5: [2.7, 2.1, 2.5],
            6: [2.0, 3.0, 4.0],
            7: [4.8, 5.4, 7.3],
            8: [3.0, 4.0, 0.0],
            9: [10.6, 9.4, 0.0],
            10: [4.0, 0.0, 0.0],
            11: [15.1, 0.0, 0.0],
        },
        index=[1, 2, 3],
    )
    df_output = format_gencost(df_input)
    assert np.array_equal(
        df_output.columns,
        [
            "type",
            "startup",
            "shutdown",
            "n",
            "p1",
            "f1",
            "p2",
            "f2",
            "p3",
            "f3",
            "p4",
            "f4",
        ],
    )
    assert np.array_equal(
        df_output.loc[1, ["p1", "f1", "p2", "f2", "p3", "f3", "p4", "f4"]].values,
        [1.0, 2.7, 2.0, 4.8, 3.0, 10.6, 4.0, 15.1],
    )
    assert np.array_equal(
        df_output.loc[2, ["p1", "f1", "p2", "f2", "p3", "f3", "p4", "f4"]].values,
        [2.0, 2.1, 3.0, 5.4, 4.0, 9.4, 0.0, 0.0],
    )
    assert np.array_equal(
        df_output.loc[3, ["p1", "f1", "p2", "f2", "p3", "f3", "p4", "f4"]].values,
        [3.0, 2.5, 4.0, 7.3, 0.0, 0.0, 0.0, 0.0],
    )


def test_format_gencost_both_model_same_n():
    df_input = pd.DataFrame(
        {
            0: [1, 2, 1, 2, 2],
            1: [0.0, 0.0, 0.0, 0.0, 0.0],
            2: [0.0, 0.0, 0.0, 0.0, 0.0],
            3: [4, 3, 2, 5, 2],
            4: [1.0, 1.3, 2.0, 2.8, 1.1],
            5: [2.7, 2.1, 2.5, 4.5, 6.4],
            6: [2.0, 3.8, 3.0, 7.3, 0.0],
            7: [4.8, 0.0, 7.3, 10.0, 0.0],
            8: [3.0, 0.0, 0.0, 14.3, 0.0],
            9: [10.6, 0.0, 0.0, 0.0, 0.0],
            10: [4.0, 0.0, 0.0, 0.0, 0.0],
            11: [15.1, 0.0, 0.0, 0.0, 0.0],
        },
        index=[1, 2, 3, 4, 5],
    )
    df_output = format_gencost(df_input)
    assert np.array_equal(
        df_output.columns,
        [
            "type",
            "startup",
            "shutdown",
            "n",
            "c4",
            "c3",
            "c2",
            "c1",
            "c0",
            "p1",
            "f1",
            "p2",
            "f2",
            "p3",
            "f3",
            "p4",
            "f4",
        ],
    )
    assert np.array_equal(
        df_output.loc[
            1,
            [
                "c4",
                "c3",
                "c2",
                "c1",
                "c0",
                "p1",
                "f1",
                "p2",
                "f2",
                "p3",
                "f3",
                "p4",
                "f4",
            ],
        ].values,
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.7, 2.0, 4.8, 3.0, 10.6, 4.0, 15.1],
    )
    assert np.array_equal(
        df_output.loc[
            2,
            [
                "c4",
                "c3",
                "c2",
                "c1",
                "c0",
                "p1",
                "f1",
                "p2",
                "f2",
                "p3",
                "f3",
                "p4",
                "f4",
            ],
        ].values,
        [0.0, 0.0, 1.3, 2.1, 3.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    )
    assert np.array_equal(
        df_output.loc[
            3,
            [
                "c4",
                "c3",
                "c2",
                "c1",
                "c0",
                "p1",
                "f1",
                "p2",
                "f2",
                "p3",
                "f3",
                "p4",
                "f4",
            ],
        ].values,
        [0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 2.5, 3.0, 7.3, 0.0, 0.0, 0.0, 0.0],
    )
    assert np.array_equal(
        df_output.loc[
            4,
            [
                "c4",
                "c3",
                "c2",
                "c1",
                "c0",
                "p1",
                "f1",
                "p2",
                "f2",
                "p3",
                "f3",
                "p4",
                "f4",
            ],
        ].values,
        [2.8, 4.5, 7.3, 10.0, 14.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    )
    assert np.array_equal(
        df_output.loc[
            5,
            [
                "c4",
                "c3",
                "c2",
                "c1",
                "c0",
                "p1",
                "f1",
                "p2",
                "f2",
                "p3",
                "f3",
                "p4",
                "f4",
            ],
        ].values,
        [0.0, 0.0, 0.0, 1.1, 6.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    )


def test_link():
    keys = ["a", "b", "c", "d", "e"]
    values = [1, 2, 3, 4, 5]
    output = link(keys, values)
    assert np.array_equal(list(output.keys()), keys)
    assert np.array_equal(list(output.values()), values)
    assert np.array_equal(output["a"], values[0])
    assert np.array_equal(output["c"], values[2])
