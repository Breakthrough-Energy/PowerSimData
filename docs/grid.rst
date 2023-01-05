
Grid Object
-----------
A ``Grid`` object contains data representing an electric power system. An object has various attributes that are listed below:

- ``data_loc`` (``str``) gives the path to the data used to create a ``Grid`` object
- ``grid_model`` (``str``) gives the name of the power system
- ``version`` (``str``) gives the version of the grid model
- ``model_immutables`` (``object``) contains static data specific to the power system
- ``zone2id`` and ``id2zone`` (``dict``) map load zone name (id) to load zone id
  (name)
- ``interconnect`` (``str``) indicates the geographical region covered
- ``bus`` (``pandas.DataFrame``) encloses the characteristics of the buses
- ``sub`` (``pandas.DataFrame``) encloses the characteristics of the substations
- ``bus2sub`` (``pandas.DataFrame``) maps buses to substations
- ``plant`` (``pandas.DataFrame``) encloses the characteristics of the plants
- ``branch`` (``pandas.DataFrame``) encloses the characteristics of the AC lines,
  transformers and transformer windings
- ``gencost`` (``dict``) encloses the generation cost curves
- ``dcline`` (``pandas.DataFrame``) encloses the characteristics of the HVDC lines
- ``storage`` (``dict``) encloses information related to storage units

Two grid models representing the `U.S. <https://arxiv.org/pdf/2002.06155.pdf>`_ and
the `European <https://arxiv.org/pdf/1806.01613.pdf>`_ power system at the transmission
network level are available at this time. In addition to the full continental U.S.
or Europe, a ``Grid`` object can represent one of the interconnection or a
combination of interconnections.

A ``Grid`` object can be created as follows for the U.S. grid model:

- U.S. grid

  .. code-block:: python

    from powersimdata import Grid
    usa = Grid("USA")

- Western interconnection

  .. code-block:: python

      from powersimdata import Grid
      western = Grid("Western")

- combination of two interconnections

  .. code-block:: python

      from powersimdata import Grid
      eastern_western = Grid(["Eastern", "Western"])
      texas_western = Grid(["Texas", "Western"])

While the for the European grid model, it can be achieved as follows:

- European grid with 128 load zones

  .. code-block:: python

    from powersimdata import Grid
    europe = Grid("Europe", source="europe_tub", reduction=128)

- Nordic interconnection

  .. code-block:: python

    from powersimdata import Grid
    europe = Grid("Nordic", source="europe_tub", reduction=128)

Any ``Grid`` object can be transformed, i.e., generators/lines can be scaled or added.
This is achieved in the scenario framework.
