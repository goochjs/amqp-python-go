FROM golang:1.7

RUN apt-get update && apt-get install -y \
	apt-utils \
	cmake \
	cmake-curses-gui \
	uuid-dev \
	libssl-dev \
	libsasl2-2 \
	libsasl2-dev \
	libsasl2-modules \
	bsdtar

ENV QPID_PROTON_DOWNLOAD_URL https://github.com/apache/qpid-proton/archive/master.zip
#ENV QPID_PROTON_DOWNLOAD_URL https://github.com/alanconway/qpid-proton/archive/go-durable-sub.zip
#ENV QPID_PROTON_DOWNLOAD_URL https://github.com/goochjs/qpid-proton/archive/go-durable-sub.zip

# Make the build directory
RUN mkdir -p /tmp/qpid-proton/build

# Go to the `qpid-proton` directory where we will download the zip file
WORKDIR /tmp/qpid-proton

# Download the `qpid-proton` zip and extract all the contents and delete the zip
RUN curl -fsSL "$QPID_PROTON_DOWNLOAD_URL" -o /tmp/qpid-proton/qpid-proton.zip \
	&& bsdtar -xf /tmp/qpid-proton/qpid-proton.zip -s'|[^/]*/||' \
	&& rm /tmp/qpid-proton/qpid-proton.zip

# Go to build directory
WORKDIR /tmp/qpid-proton/build

# Build the qpid-proton (C language) library (and then delete `/qpid-proton` directory)
RUN cmake .. -DCMAKE_INSTALL_PREFIX=/usr -DSYSINSTALL_BINDINGS=ON \
	&& make all \
	&& make install \
	&& rm -rf /tmp/qpid-proton

# Download Go `qpid.apache.org/amqp` and `qpid.apache.org/electron` packages
RUN go-wrapper download \
	qpid.apache.org/amqp \
	qpid.apache.org/electron

# Copy application to the container
COPY . /usr/src/go-electron

# Change working directory back
WORKDIR /usr/src/go-electron
