FROM alpine

RUN apk --update add bash openssl

COPY . /usr/src/ssl

CMD /usr/src/ssl/ssl-gen.sh
