FROM postgres:15
COPY init.sql /docker-entrypoint-initdb.d/init.sql

RUN echo "listen_addresses = '*'" >> postgresql.conf
