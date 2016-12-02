from __future__ import print_function
import sys
from mock import patch
from tests.mock_consul_server import serve_consul

def test_main():
    from powerconsul.__main__ import main

    # Start the mock server
    serve_consul()

    # Test arguments
    test_args = {
        'service_standalone': ['check', 'service', '-s', 'example', '-S', 'example']
    }

    with patch.object(sys, 'argv', test_args['service_standalone']):
        main()
