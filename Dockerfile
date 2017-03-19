FROM guitarmind/openface
MAINTAINER Mark Peng <markpeng73@msn.com>

EXPOSE 8000 9000
ENV HOME=/root/face_learner

WORKDIR ${HOME}
COPY . .
RUN chmod -R 777 ${HOME}

# TODO: build Dlib with release mode and USE_AVX_INSTRUCTIONS
# https://gist.github.com/ageitgey/629d75c1baac34dfa5ca2a1928a7aeaf
# mkdir build; cd build; cmake .. -DDLIB_USE_CUDA=0 -DUSE_AVX_INSTRUCTIONS=1; sudo cmake --build . --config Release
# cd ..
# python setup.py install --yes USE_AVX_INSTRUCTIONS --no DLIB_USE_CUDA

CMD /bin/bash -l -c '/root/face_learner/web/start-servers.sh'
