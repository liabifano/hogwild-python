FROM python:3.6.3

RUN python3 -m pip install pip --upgrade


COPY src /hogwild-python/src/
COPY setup.py /hogwild-python/

RUN cd /hogwild-python/ && pip install -e .
