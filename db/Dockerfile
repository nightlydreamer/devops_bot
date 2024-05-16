FROM postgres:15
COPY init.sql /docker-entrypoint-initdb.d/init.sql

RUN echo "listen_addresses = '*'" >> postgresql.conf
RUN mkdir -p /var/log/postgres
RUN chmod 777 /var/log/postgres
