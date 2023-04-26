import pytest
from testing.test_database import *
from testing.test_projections import *
from testing.test_graphing import test_product_graph
# from testing.test_graphing import test_graph_conversion

Base.metadata.drop_all(test_engine)
Base.metadata.create_all(test_engine)