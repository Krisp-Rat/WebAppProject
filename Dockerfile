FROM python:3.8

ENV HOME /root
WORKDIR /root

# Install Node
RUN apt-get update --fix-missing
RUN apt-get install -y nodejs
RUN apt-get install -y npm

COPY . .

# Download dependancies
RUN pip3 install -r requirements.txt

EXPOSE 8080

CMD python3 -u server.py
