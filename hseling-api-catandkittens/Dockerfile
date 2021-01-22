FROM hseling/hseling-api-base:python3.6-alpine3.7

LABEL maintainer="Sergey Sobko <ssobko@hse.ru>"

RUN mkdir /dependencies
RUN apk add gfortran g++ build-base wget freetype-dev libpng-dev openblas-dev
RUN pip install numpy==1.15.4
RUN pip install scipy==0.18.1
COPY ./requirements.txt /dependencies/requirements.txt
COPY ./setup.py /dependencies/setup.py
COPY ./hseling_api_catandkittens /dependencies/hseling_api_catandkittens
RUN pip install -r /dependencies/requirements.txt
RUN pip install /dependencies
RUN mkdir /data
COPY ./app /app
