import os
import consul
from json import loads
import subprocess
import os.path
import pygogo as gogo
import hashlib
import pulsar

CONFIG_PATH = "metadata-cleaner"
# logging setup
kwargs = {}
formatter = gogo.formatters.structured_formatter
logger = gogo.Gogo('struct', low_formatter=formatter).get_logger(**kwargs)


def main():
    logger.info("Starting!!")

    client = pulsar.Client(f"pulsar://{get_config('PULSAR_SERVER')}")
    consumer = client.subscribe(get_config('PULSAR_TOPIC'), get_config('PULSAR_SUBSCRIPTION'),
                                consumer_type=pulsar.ConsumerType.Shared)

    while True:
        msg = consumer.receive()
        try:
            # decode from bytes, encode with backslashes removed, decode back to a string, then load it as a dict
            message_body = loads(msg.data().decode().encode('latin1', 'backslashreplace').decode('unicode-escape'))
            logger.debug("Message body", extra={'message_body': message_body})
            if is_valid_message(message_body):
                cleanup_metadata(message_body)
            else:
                logger.warning("Message skipped due to valid check", extra={'message_body': message_body})
            # Acknowledge successful processing of the message
            consumer.acknowledge(msg)
        except:  # noqa: E722
            # Message failed to be processed
            consumer.negative_acknowledge(msg)

    client.close()


def cleanup_metadata(message_body):
    file_path = message_body['file_path']
    message_hash = get_md5_hex_hash(file_path)
    logger.info("Processing new message", extra={'message_hash': message_hash, 'message_body': message_body})
    filename, file_extension = os.path.splitext(file_path)
    command = ['exiftool', file_path]
    logger.debug("Exiftool command", extra={'message_hash': message_hash, 'command': " ".join(command)})
    completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
    logger.info("Exiftool Results", extra={'message_hash': message_hash, 'output': completed_process.stdout})
    if any(x in completed_process.stdout for x in ['Title', 'Comment']):
        # ffmpeg -i input.m4v -c copy -metadata title= -metadata comment= output.m4v
        command = ['ffmpeg', '-y', '-i', file_path, '-c', 'copy', '-metadata', 'title=', '-metadata', 'comment=',
                   "{}-tmp{}".format(filename, file_extension)]
        logger.debug("ffmpeg command", extra={'message_hash': message_hash, 'command': " ".join(command)})
        completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
        logger.debug("ffmpeg output", extra={'message_hash': message_hash, 'output': completed_process.stdout})
        command = ['mv', f"{filename}-tmp{file_extension}", file_path]
        logger.debug("mv command", extra={'message_hash': message_hash, 'command': " ".join(command)})
        subprocess.run(command, check=True, capture_output=True, text=True)
    else:
        logger.info("{} does not have a Title or Comment".format(file_path), extra={'message_hash': message_hash})
    logger.info("Done processing message", extra={'message_hash': message_hash})


def get_config(key, config_path=CONFIG_PATH):
    if os.environ.get(key):
        logger.info("found {} in an environment variable".format(key))
        return os.environ.get(key)
    logger.info("looking for {}/{} in consul".format(config_path, key))
    c = consul.Consul()
    index, data = c.kv.get("{}/{}".format(config_path, key))
    return data['Value'].decode("utf-8")


def get_md5_hex_hash(string_to_hash):
    result = hashlib.md5(string_to_hash.encode())
    return result.hexdigest()


def is_valid_message(message):
    return message['type'] is not None and message['file_path'] is not None


def test_main():
    message_body = {"type": "movie", "file_path": "/movies/Lost in Translation (2003).mkv"}
    cleanup_metadata(message_body)


if __name__ == '__main__':
    main()
    # test_main()
