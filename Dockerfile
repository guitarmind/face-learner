FROM guitarmind/openface
MAINTAINER Mark Peng <markpeng73@msn.com>

EXPOSE 8000 9000
ENV HOME=/root/face_learner

WORKDIR ${HOME}
COPY . .

CMD /bin/bash -l -c 'web/start-servers.sh'
