# metadata-cleaner
A video metadata cleaner that reads from a Kafka topic

## PyPi Dependency updates

    pip install --upgrade pip
    pip install --upgrade pulsar-client pygogo python-consul
    pip freeze > requirements.txt
    sed -i '/pkg_resources/d' requirements.txt

## Running locally

Hacky hacky, but update `app.py` to call `test_main()` instead of `main()` and put your message updates in that method.
This will skip all Kafka logic.

    docker build . -t mds
    docker run -it --rm -v ${PWD}:/movies mds
