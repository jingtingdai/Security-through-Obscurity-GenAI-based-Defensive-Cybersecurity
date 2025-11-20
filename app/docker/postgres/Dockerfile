FROM postgres:15

# Install pgAudit
RUN apt-get update && \
    apt-get install -y postgresql-15-pgaudit && \
    rm -rf /var/lib/apt/lists/*

# Enable pgAudit and logging options
RUN echo "shared_preload_libraries = 'pgaudit'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "pgaudit.log = 'read, write, ddl'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "logging_collector = on" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_directory = '/var/log/postgresql'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_filename = 'postgresql.log'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_line_prefix='%m [%p] user=%u,db=%d,app=%a,client=%h '" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_statement = 'all'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_connections = on" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_disconnections = on" >> /usr/share/postgresql/postgresql.conf.sample

