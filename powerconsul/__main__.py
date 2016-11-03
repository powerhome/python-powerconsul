from powerconsul import PowerConsul
from powerconsul.common import init_powerconsul

# Launch Power Consul command line utilities
def main():

    # Initialize Power Consul commons
    init_powerconsul()

    # Run Power Consul
    PowerConsul.run()

# Common line invocation
if __name__ == '__main__':
    main()
