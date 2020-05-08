class FieldHierarchicalIndex:
    """
    The class wraps indices from our grid fields simplifying the interface
    and providing context such as the dataframe the index originated from
    to aid in input validation
    """
    def __init__(self, index, index_hierarchy, origin_dataframe):
        """
        :param pandas.Series index: Pandas series with multi-level index
        :param list index_hierarchy: list hierarchy for the hierarchical index
        :param str origin_dataframe: dataframe this index originated from
        """
        self._index = index
        self.index_hierarchy = index_hierarchy
        self.origin_dataframe = origin_dataframe

    def get_idx(self, index_tuple):
        """
        returns a native single-dimensional python index from the
        groupby object
        :param tuple index_tuple: desired grouping
        :return: (*list*) -- native single-dimensional python index
        """
        return self._index.loc[index_tuple].values.tolist()

    def __getitem__(self, index_tuple):
        """
        gets a list of indices for a given tuple
        :param tuple index_tuple: desired grouping
        :return: (*list*) -- python list of indices
        """
        return self.get_idx(self, index_tuple)


class AbstractGridField:
    """
    This define base level functionality of a grid data field
    We can put general data validation and utility functions here
    """
    def __init__(self, data, name, transform):
        """
        :param pandas.DataFrame data: dataframe for this grid field
        :param str name: name of the grid field
        :param dict transform: dictionary of valid transformations on the data
        """
        self.data = data
        self.name = name
        self.transform = transform


class HierarchicalGridField(AbstractGridField):
    """
    This defines a grid field that can support hierarchical indexing
    """
    def ct_hierarchy_iterator(self, change_table, ct_hierarchy):
        """
         This function wraps validation for the static recursive Python
         generator function hierarchy_generator
         :param dict change_table: the particular level in change table
         :param list ct_hierarchy: data column hierarchy in the change table
         :raise TypeError: for inputs not of the correct type
         :raise AssertionError: for hierarchy names which are not in dataframe
         :return: (*types.GeneratorType*) -- python generator that returns
         individual changes to be performed
         """
        if type(change_table) is not dict:
            raise TypeError("change_table must be a dictionary")
        if type(ct_hierarchy) is not list:
            raise TypeError("ct_hierarchy must be a list")
        assert all(column in self.data.columns for column in ct_hierarchy), \
            'ct_hierarchy must contain columns in dataframe'
        self.ct_hierarchy_generator(change_table, ct_hierarchy)

    @staticmethod
    def ct_hierarchy_generator(change_level, ct_hierarchy, index=()):
        """
         This function creates a recursive Python generator function which
         traverses the change table hierarchy and returns a unnested list of
         changes to be implemented
         :param {dict, int, float} change_level: the particular level in
         change table
         :param list ct_hierarchy: data column hierarchy in the change table
         :param tuple index: initial starting tuple
         :raises ValueError: tuple index not compatible with hierarchy depth
         :raises TypeError: item not a valid change table type
         :return: (*types.GeneratorType*) -- python generator that returns
         individual changes to be performed
        """
        if isinstance(change_level, dict):
            for current_level, next_level in change_level.items():
                yield from HierarchicalGridField.ct_hierarchy_generator(
                        next_level, ct_hierarchy, index + (current_level,))
        elif isinstance(change_level, (int, float)):
            if len(ct_hierarchy) != len(index):
                raise ValueError("Generated index must of same length as "
                                 "ct_hierarchy input")
            change_info = {"ct_hierarchy": ct_hierarchy, "index": index,
                           "scaling_value": change_level}
            yield change_info
        else:
            raise TypeError(f"{change_level} not a valid change table type")

    def get_hierarchical_index(self, index_hierarchy, base_index_column=None):
        """
        Returns a hierarchical index dataframe where the base level column
        matches the existing dataframe index. This allow sharing
        hierarchical indices between complementary dataframes, such 'plant'
        and 'gencost'.
        :param list index_hierarchy: list of the index hierarchy to be
        implemented
        :param str base_index_column: base level column for index which
        matches the index column of the dataframe to be scaled
        :return: FieldHierarchicalIndex -- set_index method index type
        """
        assert all(column in self.data.columns for column in index_hierarchy),\
            'index_hierarchy must contain columns in dataframe'
        if base_index_column is None:
            base_index_column = self.data.index.name
        assert (base_index_column not in index_hierarchy), \
            'base index column must not be index hierarchy'

        hierarchical_index = self.data[index_hierarchy] \
                                 .reset_index() \
                                 .set_index(index_hierarchy) \
                                 .sort_index()[base_index_column]

        field_idx = FieldHierarchicalIndex(hierarchical_index,
                                           index_hierarchy,
                                           self.name)
        return field_idx


class Branch(HierarchicalGridField):
    """
    Class for branch data which includes data validation, dictionary of valid
    data transformations, and utility functionss
    """
    def __init__(self, data):
        """
        :param pandas.DataFrame data: dataframe for the branch field
        """
        name = 'branch'
        transform = {}
        super().__init__(data, name, transform)


class Bus(HierarchicalGridField):
    """
    Class for bus data which includes data validation, dictionary of valid data
    transformations, and utility functions
    """
    def __init__(self, data):
        """
        :param pandas.DataFrame data: dataframe for the bus field
        """
        name = 'bus'
        transform = {}
        super().__init__(data, name, transform)


class DCLine(AbstractGridField):
    """
    Class for dcline data which includes data validation, dictionary of valid
    data transformations, and utility functions
    """
    def __init__(self, data):
        """
        :param pandas.DataFrame data: dataframe for the dcline field
        """
        name = 'dcline'
        transform = {}
        super().__init__(data, name, transform)


class GenCost(HierarchicalGridField):
    """
    Class for gencost data which includes data validation, dictionary of valid
    data transformations, and utility functions
    """
    def __init__(self, data):
        """
        :param pandas.DataFrame data: dataframe for the gencost field
        """
        name = 'gencost'
        transform = {}
        super().__init__(data, name, transform)


class Plant(HierarchicalGridField):
    """
    Class for plant data which includes data validation, dictionary of valid
    data transformations, and utility functions
    """
    def __init__(self, data):
        """
        :param pandas.DataFrame data: dataframe for the plant field
        """
        name = 'plant'
        transform = {}
        super().__init__(data, name, transform)


class Storage(AbstractGridField):
    """
    Class for storage data which includes data validation, dictionary of valid
    data transformations, and utility functions
    """
    def __init__(self, data):
        """
        :param pandas.DataFrame data: dataframe for the storage field
        """
        name = 'storage'
        transform = {}
        super().__init__(data, name, transform)


class Sub(HierarchicalGridField):
    """
    Class for sub data which includes data validation, dictionary of valid data
    transformations, and utility functions
    """
    def __init__(self, data):
        """
        :param pandas.DataFrame data: dataframe for the sub field
        """
        name = 'sub'
        transform = {}
        super().__init__(data, name, transform)