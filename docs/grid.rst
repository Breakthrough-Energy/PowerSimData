
Grid Object
-----------
A ``Grid`` object contains data representing an electric power system. An object has various attributes that are listed below:

- ``data_loc`` (``str``) gives the path to the data used to create a ``Grid`` object
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

Only the U.S. Test system presented `here <https://arxiv.org/pdf/2002.06155.pdf>`_  is
available at this time. Thus, a ``Grid`` object can represent in addition to the full
continental U.S., one of the three interconnections -- Eastern, Western or Texas-- or
a combination of two interconnections.

A ``Grid`` object can be created as follows:

- U.S. grid

  .. code-block:: python

    from powersimdata.input.grid import Grid
    usa = Grid("USA")

- Western interconnection

  .. code-block:: python

      from powersimdata.input.grid import Grid
      western = Grid("Western")

- combination of two interconnections

  .. code-block:: python

      from powersimdata.input.grid import Grid
      eastern_western = Grid(["Eastern", "Western"])
      texas_western = Grid(["Texas", "Western"])

A ``Grid`` object can be transformed, i.e., generators/lines can be scaled or added.
This is achieved in the scenario framework.
