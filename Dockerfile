
# Ubuntu Docker image
FROM ubuntu:14.04

# Update apt cache
RUN apt-get update

# Python software properties
RUN apt-get install software-properties-common -y

# Python 3.5 PPA
RUN add-apt-repository ppa:fkrull/deadsnakes -y

# Update apt cache
RUN apt-get update

# Install required packages
RUN apt-get install -y wget python2.7 python-pip python3-pip python3.5 git unzip

# Add source code
RUN mkdir -p /src
RUN cd /src && git clone -b feature/unit_tests https://github.com/powerhome/python-powerconsul.git

# Download and install Consul
RUN cd /src && wget https://releases.hashicorp.com/consul/0.7.0/consul_0.7.0_linux_amd64.zip
RUN cd /src && unzip consul_0.7.0_linux_amd64.zip && mv consul /usr/local/bin/. && rm -f consul_0.7.0_linux_amd64.zip

# Consul directories and files
RUN mkdir -p /etc/consul /opt/consul /var/run/consul
RUN cp /src/python-powerconsul/docs/example.consul.conf /etc/consul/config.json && chmod 660 /etc/consul/config.json

# Install service scripts
RUN cp /src/python-powerconsul/docs/init/consul.conf /etc/init/consul.conf && chmod 444 /etc/init/consul.conf
RUN ln -s /lib/init/upstart-job /etc/init.d/consul

# PowerConsul / Consul configuration
#RUN cp /src/python-powerconsul/docs/example.consul.conf /consul/config/config.json
#RUN cp /src/python-powerconsul/docs/example.powerconsul.conf /root/.powerconsul.conf
#RUN chown consul:consul /consul/config/config.json

# Reload Consul
#RUN consul reload

# Run build commands
#RUN cd /src/python-powerconsul && tox
