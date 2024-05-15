FROM python:3.8

RUN mkdir /app

#WORKDIR /app

#COPY . .
COPY . /app
WORKDIR /app

ARG TOKEN
ARG RM_USER
ENV TOKEN ${TOKEN}

RUN apt-get update
RUN apt-get install -y python3 python3-pip build-essential python3-venv
RUN apt-get install -y openssh-client openssh-server
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN echo "PubkeyAuthentication no" >> /etc/ssh/sshd_config
RUN service ssh restart
RUN pip3 install -r requirements.txt
RUN chmod +x /app/main.py

CMD python3 /app/main.py;
