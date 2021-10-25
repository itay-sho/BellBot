#!/usr/local/bin/python3.10

from asterisk.agi import *
from telebot import types, AdvancedCustomFilter

import telebot
import ffmpeg
import sys
import enum
import pathlib
import tempfile
import json
import typing


class UnknownExtensionError(Exception):
    pass


class ChatFilter(AdvancedCustomFilter):
    """
    Check whether chat_id corresponds to given chat_id.
    Example:
    @bot.message_handler(chat_id=[99999])
    """

    key = 'chat_ids'

    def check(self, message, allowed_chats):
        return message.chat.id in allowed_chats


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
    with open(pathlib.Path(r'BellBot/intercom-agi/secrets.json')) as f:
        return json.loads(f.read())


def init_agi() -> None:
    agi = AGI()
    agi.verbose("python agi started")


def init_telegram_bot(secrets_dict: dict) -> telebot.TeleBot:
    tb = telebot.TeleBot(secrets_dict['token'])
    tb.threaded = False

    @tb.message_handler(chat_ids=[secrets_dict['chat_id']], commands=['open'])
    def open_door(message):
        tb.reply_to(message, '5')

    @tb.message_handler(chat_ids=[secrets_dict['chat_id']], commands=['reject'])
    def reject(message):
        tb.reply_to(message, 'rejected')

    tb.add_custom_filter(ChatFilter())

    return tb


def send_telegram_recording(tb: telebot.TeleBot, chat_id: int, recording: typing.BinaryIO) -> None:
    # TODO: maybe remove this function?
    tb.send_voice(chat_id, voice=recording)


def _get_response_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row(types.KeyboardButton('/open'), types.KeyboardButton('/reject'))

    return markup


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
                .run(capture_stdout=True, capture_stderr=True)
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

        # send the new recording to the chat
        with open(recording_filename, 'rb') as f:
            send_telegram_recording(tb, secrets_dict['chat_id'], f)

        # change output keyboard
        tb.send_message(
            secrets_dict['chat_id'],
            'Would you like to open? (20 seconds to answer):',
            reply_markup=_get_response_keyboard()
        )

        tb.infinity_polling(skip_pending=True)

    except FileNotFoundError:
        return ReturnValues.RECORD_FILENAME_NOT_FOUND.value

    except UnknownExtensionError:
        return ReturnValues.UNKNOWN_RECORD_FILE_SUFFIX.value

    return ReturnValues.SUCCESS.value


if __name__ == '__main__':
    main()
