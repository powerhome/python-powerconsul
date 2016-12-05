
# Consul Docker image
FROM consul:0.7.1

# Required packages
RUN apk add --update git python python-dev py-pip build-base python3 file bash
RUN pip install virtualenv python-consul tox mock
RUN rm -rf /var/cache/apk/*

# Add source code
RUN mkdir -p /src
RUN cd /src && git clone -b feature/unit_tests https://github.com/powerhome/python-powerconsul.git

# Install Python3.5
RUN apk add --update python3

# Upgrade PIP
RUN pip2 install --upgrade pip
RUN pip3 install --upgrade pip

# Download/install Python 3.4
RUN mkdir -p /src && cd /src && curl https://www.python.org/ftp/python/3.4.5/Python-3.4.5.tgz > Python-3.4.5.tgz && tar xzf Python-3.4.5.tgz
RUN cd /src/Python-3.4.5 && ./configure && make && make install

# PowerConsul / Consul configuration
RUN cp /src/python-powerconsul/docs/example.consul.conf /consul/config/config.json
RUN cp /src/python-powerconsul/docs/example.powerconsul.conf /root/.powerconsul.conf
RUN chown consul:consul /consul/config/config.json

# Reload Consul
RUN consul reload

# Run build commands
#RUN cd /src/python-powerconsul && tox
