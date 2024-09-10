#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import calendar
import logging
import time
from datetime import datetime, timedelta
from pprint import pformat
from typing import Union, List

import gspread
from gspread import Client, Spreadsheet, Worksheet
from gspread.utils import ValueRenderOption, ValueInputOption, GridRangeType

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.auth.transport.requests

import pandas as pd
import pprintpp as pp
from alive_progress import alive_bar

from core.config import settings, GoogleSheetsSettings
from utils.utils import get_current_datetime, dt_formatted

pp = pp.PrettyPrinter(indent=4)
gs: GoogleSheetsSettings = settings.gs

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]


def get_client() -> Client:
    """
    Retrieve credentials for logging into a Google Drive account.

    Returns:
        Client: A gspread Client instance for interacting with Google Sheets.
    """
    return gspread.service_account(filename=gs.credentials, scopes=SCOPES)


async def get_credentials():
    """Получение реквизитов для входа в аккаунт Google Drive
    """
    return Credentials.from_service_account_file(filename=gs.credentials, scopes=SCOPES)


async def authorize():
    """Авторизация на Google Drive"""
    credentials = await get_credentials()
    return gspread.authorize(credentials)


async def google_authorize_token():
    credentials = await get_credentials()
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


async def get_spreadsheet(book_id: str, version_6: bool = True) -> Spreadsheet:
    """Открыть таблицу.

    :param version_6: gspread version > 6*
    :param book_id: id гугл таблицы
    """
    if version_6:
        gc = get_client()
    else:
        gc = await authorize()
    return gc.open_by_key(book_id)


async def getting_all_values(ws: Worksheet, to_dict: bool = False) -> list[list] | list[dict]:
    if to_dict:
        return ws.get_all_records()
    return ws.get_all_values()


async def google_revenue(book_id: str, sheet_name: str) -> str:
    """`Выручка за день` из гугл таблицы.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    """
    ss: Spreadsheet = await get_spreadsheet(book_id)
    values = ss.worksheet(sheet_name).get_values('A2:B7')
    return '\n'.join([f'{v[0]} {v[1]}' for v in values if any(v) and v[0] != '']).replace('Итого', '<b>Итого</b>')


async def google_safe(book_id: str, sheet_name: str, boss: bool = False) -> str | list:
    """`Выручка за день` из гугл таблицы.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    :param boss: строка для отчета остатки в сейфе
    """
    ss: Spreadsheet = await get_spreadsheet(book_id)
    if boss:
        values = ss.worksheet(sheet_name).get_values('A2:B7')
        return '\n'.join([f'{v[0]} {v[1]}' for v in values if any(v) and v[0] != '']).replace('Итого', '<b>Итого</b>')
    return ss.worksheet(sheet_name).get_values('A2:B6')


async def google_exit(book_id: str, sheet_name: str, period: int = 1, staff_array: bool = False) -> [list, None]:
    """`Выход сотрудника` за период из гугл таблицы.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    :param period: (optional) 1 - сегодня; 2 - завтра.
    :param staff_array: bool
    """
    ss: Spreadsheet = await get_spreadsheet(book_id)
    values = ss.worksheet(sheet_name).get_values()
    if values:
        df = pd.DataFrame(values, index=None)
        df = df.rename(columns=df.iloc[0])
        df = df.drop(index=[0])
        df['Дата'] = pd.to_datetime(df['Дата'])

        if period == 1:
            date_start = get_current_datetime()
            date_start = datetime(date_start.year, date_start.month, date_start.day)
            date_end = get_current_datetime(1)
            date_end = datetime(date_end.year, date_end.month, date_end.day)
            df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]

        if period == 2:
            date_start = get_current_datetime(1)
            date_start = datetime(date_start.year, date_start.month, date_start.day)
            date_end = get_current_datetime(2)
            date_end = datetime(date_end.year, date_end.month, date_end.day)
            df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]

        df['Дата'] = df['Дата'].dt.strftime('%d.%m.%y')
        df = df[['Дата', 'Сотрудник', 'Точка', 'Смена']].sort_values(['Точка', 'Сотрудник'])

        if staff_array:
            return [i[1].split(" ")[0] for i in df.values if i[1] is not None]

        if not staff_array and len(df.values):
            return [f'Дата: {i[0]}\nСотрудник: {i[1]}\nТочка: {i[2]}\nСмена: {i[3]} часов' for i in df.values]
    else:
        return None


async def google_exits_by_point(book_id: str, sheet_name: str, point: str, s_date: int = 1, e_date: int = 2) -> list:
    """`Chat_id` сотрудников, которые в смене на точке из гугл таблицы.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    :param point: точка
    :param s_date: тип даты старт 0 (сегодня), 1 (завтра)
    :param e_date: тип даты старт 1 (завтра), 2 (послезавтра)
    """
    ss: Spreadsheet = await get_spreadsheet(book_id)
    values = ss.worksheet(sheet_name).get_values()

    df = pd.DataFrame(values, index=None)
    df = df.rename(columns=df.iloc[0])
    df = df.drop(index=[0])
    df['Дата'] = pd.to_datetime(df['Дата'])

    date_start = get_current_datetime(s_date)
    date_start = datetime(date_start.year, date_start.month, date_start.day)
    date_end = get_current_datetime(e_date)
    date_end = datetime(date_end.year, date_end.month, date_end.day)
    df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end) & (df['Точка'] == point)]
    df = df[['chat_id']].sort_values(['chat_id'])

    if len(df.values):
        return [int(i[0]) for i in df.values if i[0] is not None]


async def exits_google(book_id: str, sheet_name: str, employee: str = None, period: int = 1, boss: bool = False) -> str:
    """`Выходы сотрудников` за период из гугл таблицы.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    :param employee: (optional) сотрудник, не обязательный
    :param period: (optional) 1 - за месяц, по сотруднику; 2 - 7 дн., по сотруднику; 3 - сегодня; 4 - завтра; 5 - 7 дн.
    :param boss: True, если отчет для администратора
    """
    ss: Spreadsheet = await get_spreadsheet(book_id)
    values = ss.worksheet(sheet_name).get_values()

    df = pd.DataFrame(values, index=None)
    df = df.rename(columns=df.iloc[0])
    df = df.drop(index=[0])
    df['Дата'] = pd.to_datetime(df['Дата'])

    if period == 1:
        date = get_current_datetime()
        date_start = datetime(date.year, date.month, 1)
        date_end = datetime(date.year, date.month, 1) + timedelta(days=calendar.monthrange(date.year, date.month)[1])
        df = df.loc[(df['Сотрудник'] == employee) & (df['Дата'] >= date_start) & (df['Дата'] < date_end)]

    if period == 2:
        date_start = get_current_datetime()
        date_start = datetime(date_start.year, date_start.month, date_start.day)
        date_end = get_current_datetime(7)
        date_end = datetime(date_end.year, date_end.month, date_end.day)
        df = df.loc[(df['Сотрудник'] == employee) & (df['Дата'] >= date_start) & (df['Дата'] < date_end)]

    if period == 3:
        date_start = get_current_datetime()
        date_start = datetime(date_start.year, date_start.month, date_start.day)
        date_end = get_current_datetime(1)
        date_end = datetime(date_end.year, date_end.month, date_end.day)
        df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]

    if period == 4:
        date_start = get_current_datetime(1)
        date_start = datetime(date_start.year, date_start.month, date_start.day)
        date_end = get_current_datetime(2)
        date_end = datetime(date_end.year, date_end.month, date_end.day)
        df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]

    if period == 5:
        date_start = get_current_datetime()
        date_start = datetime(date_start.year, date_start.month, date_start.day)
        date_end = get_current_datetime(7)
        date_end = datetime(date_end.year, date_end.month, date_end.day)
        df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]

    df['Дата'] = df['Дата'].dt.strftime('%d.%m.%y')
    df = df[['Дата', 'Сотрудник', 'Точка', 'Смена']].sort_values(['Дата'])

    if boss:
        data = tuple(f'Дата: {i[0]}\nСотрудник: {i[1]}\nТочка: {i[2]}\nСмена: {i[3]} часов' for i in df.values)
    else:
        data = tuple(f'Дата: {i[0]}\nТочка: {i[2]}\nСмена: {i[3]} часов' for i in df.values)

    if len(data):
        return f'\n{"*" * 15}\n'.join(data)
    else:
        return 'Не могу найти график 😕'


async def google_write_off(book_id: str, sheet_name: str, cols: list) -> list:
    """``Файл списания`` получить массив данных для создания файла списания.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    :param cols: названия столбцов, результирующего отчета
    """
    ss: Spreadsheet = await get_spreadsheet(book_id)
    values = ss.worksheet(sheet_name).get_values()
    logging.info('Write off values\n%s', pformat(values))

    # df = pd.DataFrame(values, index=None)
    # pd.set_option("display.max.columns", None)
    # df = df.rename(columns=df.iloc[0])
    # df = df.drop(index=[0])
    # df['Дата'] = pd.to_datetime(df['Дата'])
    #
    # return df[cols].sort_values(['Сотрудник', 'Дата']).values

    df = pd.DataFrame(values[1:], columns=values[0])
    df['Дата'] = pd.to_datetime(df['Дата'])
    return df[cols].sort_values(['Сотрудник', 'Дата']).values


async def google_get_all_records(book_id: str, sheet_name: str) -> List[dict]:
    """Получить все записи со страницы из гугл таблицы.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    """
    ss: Spreadsheet = await get_spreadsheet(book_id)
    return ss.worksheet(sheet_name).get_all_records(value_render_option=ValueRenderOption.unformatted)


async def google_add_row(book_id: str, sheet_name: str, array: Union[list, tuple]) -> None:
    """`Добавляет строку с данными` на лист (sheet_name) таблицы по book_id.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    :param array: массив данных
    """
    cur_date = dt_formatted(3)
    ss: Spreadsheet = await get_spreadsheet(book_id)

    try:
        if sheet_name == '':
            try:
                worksheet: Worksheet = ss.add_worksheet(title=f'{cur_date}', rows=100, cols=9)
            except Exception as e:
                logging.warning(f'{e}')
                worksheet: Worksheet = ss.worksheet(f'{cur_date}')
        else:
            worksheet: Worksheet = ss.worksheet(sheet_name)

        worksheet.append_row(values=array, value_input_option=ValueInputOption.user_entered)  # добавить на лист ниже
        logging.info('Данные добавлены %s:\n%s', worksheet.title, pformat(array))
    except Exception as ex:
        logging.warning('Google add row:', exc_info=ex)


async def google_add_rows(book_id: str, sheet_name: str, array: Union[list, tuple]) -> None:
    """`Добавляет строку с данными` на лист (sheet_name) таблицы по book_id.

    :param array: массив данных
    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    """

    ss: Spreadsheet = await get_spreadsheet(book_id)

    try:
        worksheet: Worksheet = ss.worksheet(sheet_name)
        worksheet.append_rows(values=array, value_input_option=ValueInputOption.user_entered)  # добавить на лист ниже
        logging.info('Данные добавлены %s:\n%s', worksheet.title, pformat(array))
    except Exception as ex:
        logging.warning('Google add rows:', exc_info=ex)


async def google_worksheet_update(book_id: str, sheet_name: str, array: List[dict]) -> None:
    """`Заменяет данные` на листе (sheet_name) таблицы по book_id.
    `Лист перед вставкой очищается.`
    https://docs.gspread.org/en/v5.3.2/user-guide.html#updating-cells

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    :param array: массив содержащий словарь значений для добавления
    """
    ss: Spreadsheet = await get_spreadsheet(book_id)
    worksheet: Worksheet = ss.worksheet(sheet_name)
    data = pd.DataFrame(array)
    worksheet.clear()
    worksheet.update(values=[data.columns.values.tolist()] + data.values.tolist(),
                     value_input_option=ValueInputOption.user_entered)


async def google_update_row(book_id: str, sheet_name: str, array: Union[list, tuple], query: str,
                            col: int = 1, col_s: str = 'A', col_f: str = 'H') -> bool:
    """`Добавляет строку с данными` на лист (sheet_name) таблицы по book_id.

    :param array: массив
    :param query: данные для поиска в столбце n
    :param col: номер столбца для поиска
    :param col_s: вставка с столбца
    :param col_f: вставка по столбец
    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    """
    try:
        ss: Spreadsheet = await get_spreadsheet(book_id)
        worksheet: Worksheet = ss.worksheet(sheet_name)
        cells = worksheet.findall(query, in_column=col)

        for cell in cells:
            worksheet.update(values=array, range_name=f'{col_s}{cell.row}:{col_f}{cell.row}',
                             value_input_option=ValueInputOption.user_entered)  # обновить значение

            logging.info('Обновили лист %s содержащую %s, для %s:\n%s', worksheet.title, query, f"({col_s}{cell.row}:{col_f}{cell.row})", array)

        return True
    except Exception as ex:
        logging.warning('Google update row:', exc_info=ex)
        return False


async def google_delete_row(book_id: str, sheet_name: str, query: Union[str, int], col: int = 1) -> None:
    """`Добавляет строку с данными` на лист (sheet_name) таблицы по book_id.

    :param query: данные для поиска в столбце n
    :param col: номер столбца для поиска
    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    """
    try:
        ss: Spreadsheet = await get_spreadsheet(book_id)
        worksheet: Worksheet = ss.worksheet(sheet_name)
        cell = worksheet.find(query, in_column=col)
        worksheet.delete_rows(cell.row, cell.row)  # удалить строку
        logging.info('Удалили строку %s содержащую %s, в книге %s', cell.row, query, worksheet.title)
    except Exception as ex:
        logging.warning('Google delete row:', exc_info=ex)


async def google_save_file(name: str, file_path: str, mime_type: str = 'image/png') -> str:
    """`Сохранение фотографии на` из гугл диске.

    :param name: название файла
    :param file_path: путь до файла
    :param mime_type: тип сохраняемого файла, по умолчанию 'image/png'
    :returns: id файла
    """
    credentials = await get_credentials()
    service = build('drive', 'v3', credentials=credentials, cache_discovery=False)

    file_metadata = {
        'name': name,
        'mimeType': mime_type,
        'parents': [gs.FOLDER_ID_PHOTO_SAVE]
    }

    media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
    return service.files().create(body=file_metadata, media_body=media, fields='id').execute()['id']


async def google_clear_folder(folder_id: str) -> None:
    credentials = await get_credentials()
    service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    results = service.files().list(
        pageSize=1000,
        fields="nextPageToken, files(id, name, mimeType, parents, createdTime)",
        q=f"'{folder_id}' in parents and mimeType contains 'image'").execute()

    data = []
    for i in results['files']:
        try:
            service.files().delete(fileId=i['id']).execute()
            data.append(i['id'])
        except Exception as e:
            logging.warning(f'Проблема с id {i["id"]} > {e}')
            continue

    data = "\n".join(data)
    logging.info("Удалили файлы с id:\n %s", data)


async def folder_in_google(folder_id: str) -> None:
    credentials = await get_credentials()
    service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    results = service.files().list(
        pageSize=1000,
        fields="nextPageToken, files(modifiedTime, id, name, mimeType, parents)",
        q=f"'{folder_id}' in parents").execute()

    data = []

    for i in results['files']:
        try:
            data.append(i['id'])
        except Exception as ex:
            logging.warning(f'Проблема с id: %s\n', i["id"], ex)
            continue

    with alive_bar(len(data)) as bar:
        for i in range(len(data)):
            time.sleep(.005)
            bar()


async def get_folder_info(folder_id: str) -> List:
    credentials = await get_credentials()
    service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    q = f"'{folder_id}' in parents and mimeType contains 'application/vnd.google-apps.folder'"
    results = service.files().list(pageSize=50,
                                   fields=f"nextPageToken, files(modifiedTime, id, name, mimeType, parents)",
                                   q=q).execute()
    return results.get('files', [])


async def get_folder_files_info(folder_id: str) -> List:
    credentials = await get_credentials()
    service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    contains = "in parents and (mimeType contains 'application/vnd.google-apps.document' or " \
               "mimeType contains 'pdf' " \
               "or mimeType contains 'video/mp4')"
    q = f"'{folder_id}' {contains}"
    results = service.files().list(pageSize=20,
                                   fields=f"nextPageToken, files(modifiedTime, id, name, mimeType, parents)",
                                   q=q).execute()

    next_page_token = results.get('nextPageToken')

    while next_page_token:
        next_page = service.files().list(pageSize=20,
                                         fields=f"nextPageToken, files(modifiedTime, id, name, mimeType, parents)",
                                         q=q,
                                         pageToken=next_page_token).execute()
        next_page_token = next_page.get('nextPageToken')
        results['files'] = results['files'] + next_page['files']

    return results.get('files', [])


async def google_delete_file(file_id: str) -> None:
    gc = await authorize()
    gc.del_spreadsheet(file_id)


__all__ = [
    'google_save_file',
    'google_clear_folder',
    'google_get_all_records',
    'google_exit',
    'exits_google',
    'google_write_off',
    'google_add_row',
    'google_add_rows',
    'google_update_row',
    'google_worksheet_update',
    'google_delete_row',
    'google_exits_by_point',
    'google_revenue',
    'get_folder_info',
    'get_folder_files_info',
    'google_safe',
    'google_authorize_token'
]
