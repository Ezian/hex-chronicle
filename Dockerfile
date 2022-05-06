#Deriving the latest base image
FROM python:3.8-alpine

LABEL Maintainer="https://github.com/Ezian"

WORKDIR /app

COPY hexamap.py ./
COPY svg_templates ./svg_templates
COPY classes ./classes

RUN adduser -Ds /bin/sh -h /app hexchronicle

USER hexchronicle

RUN pip install python-frontmatter


CMD [ "python", "./hexamap.py"]
