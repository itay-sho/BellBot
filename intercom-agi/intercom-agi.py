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
import os


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
    with open(pathlib.Path(os.environ.get('AST_AGI_DIR', '')) / pathlib.Path(r'./BellBot/intercom-agi/secrets.json')) as f:
        return json.loads(f.read())


def init_agi() -> typing.Union[AGI, None]:
    if not os.environ.get('AST_AGI_DIR', ''):
        return None

    my_agi = AGI()
    my_agi.verbose("python agi started")

    return my_agi


def init_telegram_bot(secrets_dict: dict, my_agi: AGI) -> telebot.TeleBot:
    tb = telebot.TeleBot(secrets_dict['token'])
    tb.threaded = False

    @tb.message_handler(chat_ids=[secrets_dict['chat_id']], commands=['open'])
    def open_door(message):
        tb.reply_to(message, 'DTMF 5 sent. Door should be open')
        tb.stop_polling()

        if agi is not None:
            agi.appexec('SendDTMF', '55555')

    @tb.message_handler(chat_ids=[secrets_dict['chat_id']], commands=['reject'])
    def reject(message):
        tb.reply_to(message, 'rejected')
        tb.stop_polling()

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

    my_agi = init_agi()
    tb = init_telegram_bot(secrets_dict, my_agi)

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

        try:
            tb.infinity_polling(skip_pending=True)
        finally:
            tb.send_message(secrets_dict['chat_id'], 'Session is over')

    except FileNotFoundError:
        return ReturnValues.RECORD_FILENAME_NOT_FOUND.value

    except UnknownExtensionError:
        return ReturnValues.UNKNOWN_RECORD_FILE_SUFFIX.value

    return ReturnValues.SUCCESS.value


if __name__ == '__main__':
    main()
