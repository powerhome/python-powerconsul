from __future__ import print_function

def test_main():
    from powerconsul.__main__ import main

    # Standalone service check
    main(['powerconsul', 'check', 'service', '-s', 'example', '-S', 'example'])
