FROM guitarmind/dlib-face-recognition
MAINTAINER Mark Peng <markpeng73@msn.com>

EXPOSE 8000 9000
ENV TERM=xterm \
    HOME=/opt/app

WORKDIR ${HOME}

RUN apt-get update && apt-get install -y supervisor htop && \
    mkdir -p /var/log/supervisor && \
    chmod -R 777 /var/log/supervisor && \
    chmod 777 /run && \
    cp -r /root/dlib . && \
    ln /dev/null /dev/raw1394

RUN pip install autobahn txaio zope.interface \
    twisted pyopenssl cryptography service_identity \
    scipy tornado Click Pillow pyaudio requests && \
    touch /usr/local/lib/python2.7/site-packages/zope/__init__.py

ENV PYTHONPATH $PYTHONPATH:/usr/local/lib/python2.7/site-packages:/opt/app/dlib/dist

COPY . .
RUN chmod -R 777 /opt/app

RUN echo "[unix_http_server]" > /etc/supervisor/conf.d/supervisord.conf && \
    echo "file=/var/run/supervisor.sock" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "chmod=0770" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[supervisord]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:web_server]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "priority=100" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=/usr/bin/python /opt/app/web-server.py" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:websocker_server]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "priority=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=/usr/bin/python /opt/app/websocket-server.py" >> /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
