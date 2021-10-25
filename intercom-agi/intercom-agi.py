#!/usr/bin/python3
import typing

from asterisk.agi import *
import telebot
import ffmpeg
import sys
import enum
import pathlib
import tempfile
import json


class UnknownExtensionError(Exception):
    pass


@enum.unique
class Arguments(enum.Enum):
    PROGRAM = 0
    RECORD_FILENAME = enum.auto()


@enum.unique
class ReturnValues(enum.Enum):
    SUCCESS = 0
    UNKNOWN_ERROR = enum.auto()
    RECORD_FILENAME_NOT_FOUND = enum.auto()
    UNKNOWN_RECORD_FILE_SUFFIX = enum.auto()


def load_secrets() -> dict:
    with open('../intercom-agi/secrets.json') as f:
        return json.loads(f.read())


def init_agi() -> None:
    agi = AGI()
    agi.verbose("python agi started")


def init_telegram_bot(secrets_dict: dict) -> telebot.TeleBot:
    tb = telebot.TeleBot(secrets_dict['token'])
    tb.send_message(secrets_dict['chat_id'], 'Bot is up')

    return tb


def send_telegram_recording(tb: telebot.TeleBot, chat_id: int, recording: typing.BinaryIO) -> None:
    tb.send_voice(chat_id, voice=recording)


def get_record_filename_as_m4a() -> str:
    original_filename = sys.argv[Arguments.RECORD_FILENAME.value]

    match pathlib.Path(original_filename).suffix:
        case '.wav':
            _, output_mp4_filename = tempfile.mkstemp(suffix='.m4a')

            out, _ = (
                ffmpeg
                .input(original_filename)
                .output(output_mp4_filename)
                .overwrite_output()
                .run(capture_stdout=True)
            )

            return output_mp4_filename
        case ('.m4a' | '.mp3'):
            return original_filename
        case _:
            raise UnknownExtensionError()


def main() -> int:
    secrets_dict = load_secrets()

    # init_agi()
    tb = init_telegram_bot(secrets_dict)

    try:
        recording_filename = get_record_filename_as_m4a()

        with open(recording_filename, 'rb') as f:
            send_telegram_recording(tb, secrets_dict['chat_id'], f)

    except FileNotFoundError:
        return ReturnValues.RECORD_FILENAME_NOT_FOUND.value

    except UnknownExtensionError:
        return ReturnValues.UNKNOWN_RECORD_FILE_SUFFIX.value

    return ReturnValues.SUCCESS.value


if __name__ == '__main__':
    main()
