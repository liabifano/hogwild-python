FROM python:3.6.3

RUN python3 -m pip install pip --upgrade

COPY /src /hogwild-python/src/
COPY /resources /hogwild-python/resources/
#TODO: REMOVE AND FIX IT
COPY conda.txt bootstrap-python-env.sh setup.py run-local.sh /hogwild-python/

RUN cd /hogwild-python/ && pip install -e .

CMD python hogwild-python/src/hogwild/coordinator.py
