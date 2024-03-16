
import pytest
import os
import sys
from tcpping.tcpping import real_tcpping

def test_tcpping_001():
    """ positive test """
    with pytest.raises(SystemExit) as sampler:
            #bypass click
            assert real_tcpping('google.com', 443 , 1 , 0 , 1) == 0
    assert sampler.type == SystemExit
    assert sampler.value.code == 0
    print('{"module":"tcpping","function":"test_tcpping_001","type","positive test","result":"pass"}')

def test_tcpping_002():
    """ negative test """
    with pytest.raises(SystemExit) as sampler:
            #bypass click
            real_tcpping('foobar.google.com', 443 , 1 , 0 , 1)
    assert sampler.type == SystemExit
    assert sampler.value.code == 1
    print('{"module":"tcpping","function":"test_tcpping_002","type","negative test","result":"pass"}')

