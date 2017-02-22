FROM rmohr/activemq

# Create the mount point for the persistence store
USER root
RUN mkdir -p /mnt/nfs-share/activemq && \
    chown activemq:activemq /mnt/nfs-share/activemq
USER activemq

# Copy config to the container
COPY ./activemq.xml /opt/activemq/conf/activemq.xml
