from src.testing.test_projections import *

Base.metadata.drop_all(test_engine)
Base.metadata.create_all(test_engine)