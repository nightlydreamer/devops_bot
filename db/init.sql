DROP TABLE IF EXISTS emails;
DROP TABLE IF EXISTS phones;

CREATE TABLE emails (id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY, email VARCHAR(30));
CREATE TABLE phones (id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY, phone VARCHAR(20));

INSERT INTO emails (email) VALUES ('test@mail.ru'), ('alyona1234@gmail.net');
INSERT INTO phones (phone) VALUES ('+79012345677'), ('+79999992233');

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD '1234';
SELECT pg_create_physical_replication_slot('replication_slot');
