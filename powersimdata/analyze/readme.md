## Qualities of the BranchDeviceType Feature 
Vicky Hunt, 5/30/19

This notebook (Test_branchdevicetype.ipynb) demonstrates qualitites that differentiate the categories of BranchDeviceType: Transformer, TransformerWinding, and Line. 

1. Transformer and TransformerWinding have mean ratios of approximately 1. The variation around the mean value of 1 is greater for Transformers.
2. Lines have ratio values of 0
3. TransformerWindings show a consistent pattern of having 3 from_bus_id nodes connected to 1 to_bus_id node. This is shown using a network visualization.
