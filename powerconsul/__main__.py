from sys import argv
from powerconsul import PowerConsul
from powerconsul.common import init_powerconsul

# Launch Power Consul command line utilities
def main(args=argv):

    # Initialize Power Consul commons
    init_powerconsul(args)

    # Run Power Consul
    PowerConsul.run()

# Common line invocation
if __name__ == '__main__':
    main()
