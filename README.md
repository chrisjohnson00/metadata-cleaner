# metadata-cleaner
A video metadata cleaner that reads from a Kafka topic

## PyPi Dependency updates

    pip install --upgrade pip
    pip install --upgrade pip kafka-python pygogo python-consul
    pip freeze > requirements.txt
    sed -i '/pkg-resources/d' requirements.txt
