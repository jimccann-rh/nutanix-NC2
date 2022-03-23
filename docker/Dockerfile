ARG IMAGELOCATION='registry.access.redhat.com/ubi8/python-39'
FROM $IMAGELOCATION
ARG USERPATH='/opt/app-root/src'
USER root
#ADD app-src .

COPY requirements.txt /
RUN pip install -r /requirements.txt 
RUN yum install iputils -y

COPY *.py $USERPATH
COPY entrypoint.sh /

RUN chown -R 1001:0 $USERPATH

USER 1001
ENTRYPOINT [ "/entrypoint.sh" ]

