FROM python:3.12-slim

RUN pip install --no-cache-dir \
        bcrypt==4.2.0 \
        argon2-cffi==23.1.0 \
        matplotlib==3.9.2 \
        psutil==6.0.0

RUN useradd -m -s /bin/bash runner

WORKDIR /benchmark
COPY benchmark.py plot.py ./
RUN mkdir -p /benchmark/results /benchmark/charts && \
    chown -R runner:runner /benchmark

USER runner

CMD ["bash", "-c", "python benchmark.py && python plot.py"]
