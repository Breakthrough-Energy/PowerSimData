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


class Branch(AbstractGridField):
    """
    Class for branch data which includes data validation, dictionary of valid data
    transformations, and utility functionss
    """
    def __init__(self, data):
        """
        :param pandas.DataFrame data: dataframe for the branch field
        """
        name = 'branch'
        transform = {}
        super().__init__(data, name, transform)


class Bus(AbstractGridField):
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


class GenCost(AbstractGridField):
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


class Plant(AbstractGridField):
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


class Sub(AbstractGridField):
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