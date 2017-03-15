FROM guitarmind/openface
MAINTAINER Mark Peng <markpeng73@msn.com>

EXPOSE 8000 9000
ENV HOME=/root/face_learner

WORKDIR ${HOME}
COPY . .
RUN chmod -R 777 ${HOME}

CMD /bin/bash -l -c '/root/face_learner/web/start-servers.sh'
