FROM python:3.6.3

RUN python3 -m pip install pip --upgrade


COPY src /hogwild-python/src/
#COPY ../../resources /resources this should be in the volume of kubernetes
COPY conda.txt setup.py run-local.sh /hogwild-python/

RUN cd /hogwild-python/ && pip install -e .

CMD python src/hogwild/node.py ${PORT}
