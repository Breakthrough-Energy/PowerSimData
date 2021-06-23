def _reindex_as_necessary(df1, df2, check_columns):
    """Check for indices with mismatched entries in specified columns. If any entries
    don't match, reindex based on these columns such that there are no shared indices
    with mismatched entries in these columns.

    :param pandas.DataFrame df1: data frame containing ``check_columns``.
    :param pandas.DataFrame df2: data frame containing ``check_columns``.
    :param iterable check_columns: column
    :return: (*tuple*) -- data frames, reindexed as necessary.
    """
    # Coerce to list for safety, since pandas interprets lists and tuples differently
    check_columns_list = list(check_columns)
    shared_indices = set(df1.index) & set(df2.index)
    check1 = df1.loc[shared_indices, check_columns_list]
    check2 = df2.loc[shared_indices, check_columns_list]
    if not check1.equals(check2):
        df1 = df1.set_index(keys=check_columns_list, drop=False, append=True)
        df2 = df2.set_index(keys=check_columns_list, drop=False, append=True)
    return df1, df2
