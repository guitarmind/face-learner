FROM guitarmind/dlib-face-recognition
MAINTAINER Mark Peng <markpeng73@msn.com>

EXPOSE 8000 9000
ENV TERM=xterm \
    HOME=/opt/app

WORKDIR ${HOME}

RUN apt-get update && apt-get install -y supervisor && \
    pip install autobahn \
    twisted pyopenssl cryptography service_identity \
    scipy tornado Click Pillow && \
    mkdir -p /var/log/supervisor && \
    chmod -R 777 /var/log/supervisor && \
    chmod 777 /run

COPY . .
RUN rm -rf /opt/app/* && \
    chmod -R 777 /opt/app && \
    chmod -R 777 /opt/face_learner

RUN echo "[unix_http_server]" > /etc/supervisor/conf.d/supervisord.conf && \
    echo "file=/var/run/supervisor.sock" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "chmod=0770" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[supervisord]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:websocker_server]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "priority=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=/usr/bin/python3 /opt/face_learner/websocket-server.py" >> /etc/supervisor/conf.d/supervisord.conf \
    echo "autostart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autorestart=unexpected" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "startsecs=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:web_server]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "priority=100" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=/usr/bin/python3 /opt/face_learner/web-server.py" >> /etc/supervisor/conf.d/supervisord.conf

WORKDIR /opt/face_learner

CMD ["/usr/bin/supervisord"]
