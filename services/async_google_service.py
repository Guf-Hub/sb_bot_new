import logging
from datetime import datetime, timedelta, time
from pprint import pformat
from typing import List, Union
import calendar

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import google.auth.transport.requests

from gspread.utils import ValueRenderOption, ValueInputOption

from gspread_asyncio import (
    AsyncioGspreadClientManager,
    AsyncioGspreadClient,
    AsyncioGspreadSpreadsheet,
    AsyncioGspreadWorksheet,
)

from core.config import settings, GoogleSheetsSettings
from utils.utils import get_current_datetime

gs: GoogleSheetsSettings = settings.gs

# https://pypi.org/project/gspread-asyncio/


SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]


class GoogleSheetAsyncClient:
    def __init__(self):
        self.table_id = None
        self.sheet_name = None
        self.agcm = None
        self.agc = None
        self.ss = None
        self.ws = None

    @staticmethod
    def __get_credentials():
        return Credentials.from_service_account_file(filename=gs.credentials).with_scopes(
            SCOPES)  # gs.credentials

    async def __aenter__(self) -> AsyncioGspreadClient:
        self.agcm = AsyncioGspreadClientManager(self.__get_credentials)
        self.agc = await self.agcm.authorize()
        # self.ss = await self.agc.open_by_key(self.table_id)
        # self.ws = await self.ss.worksheet(self.sheet_name)
        return self.agc

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.agc = None
        self.agcm = None
    #
    # async def spreadsheet(self, table_id):
    #     self.table_id = table_id
    #     self.ss = await self.agc.open_by_key(self.table_id)
    #     return self
    #
    # async def worksheet(self, table_id, sheet_name):
    #     self.table_id = table_id
    #     self.sheet_name = sheet_name
    #     self.ss = await self.agc.open_by_key(self.table_id)
    #     self.ws = await self.ss.worksheet(self.sheet_name)
    #     return self
    #
    # async def create_spreadsheet(self, name):
    #     ss = await self.agc.create(name)
    #     print("Spreadsheet URL: https://docs.google.com/spreadsheets/d/{0}".format(ss.id))
    #     await self.agc.insert_permission(ss.id, None, perm_type="anyone", role="writer")
    #
    # async def add_worksheet(self, name, rows, cols):
    #     ws = await self.ss.add_worksheet(name, rows, cols)
    #     return ws
    #
    # async def worksheets(self):
    #     return await self.ss.worksheets()
    #
    # async def update_cells(self, row, col, value):
    #     await self.ws.update_cell(row, col, value)
    #
    # async def append_row(self, row: Union[list, tuple], input_option: str = 'USER_ENTERED') -> None:
    #     await self.ws.append_row(row, value_input_option=input_option, nowait=True)
    #
    # async def append_rows(self, rows: list[Union[list, tuple]], input_option: str = 'USER_ENTERED') -> None:
    #     await self.ws.append_rows(rows, value_input_option=input_option)
    #
    # async def insert_rows(self, rows: Union[list, tuple], input_option: str = 'USER_ENTERED') -> None:
    #     await self.ws.insert_rows(rows, value_input_option=input_option)
    #
    # async def delete_rows(self, index: int, end_index: int) -> None:
    #     await self.ws.delete_rows(index, end_index, nowait=True)
    #
    # async def get_all_records(self) -> List[dict]:
    #     return await self.ws.get_all_records()
    #
    # async def get_all_values(self) -> List[List[str]]:
    #     return await self.ws.get_all_values()
    #
    # async def get_values(self, range_name: str = None, ) -> List[List[str]]:
    #     return await self.ws.get_values(range_name)
    #
    # async def clear(self) -> None:
    #     await self.ws.clear()


async def google_safe(boss: bool = False) -> str | list:
    """`Выручка за день` из гугл таблицы.
    :param boss: строка для отчета остатки в сейфе
    """
    async with GoogleSheetAsyncClient() as client:
        # ws = await client.worksheet(gs.BOOK_SALARY, gs.SHEET_SAFE)

        ss = await client.open_by_key(gs.BOOK_SALARY)
        ws = await ss.worksheet(gs.SHEET_SAFE)

        values = await ws.get_values('A2:B7')
    if boss:
        return '\n'.join([f'{v[0]} {v[1]}' for v in values if any(v) and v[0] != '']).replace('Итого', '<b>Итого</b>')
    return values[:-1]


async def google_revenue() -> str:
    """`Выручка за день` из гугл таблицы."""
    async with GoogleSheetAsyncClient() as client:
        # ws = await client.worksheet(gs.BOOK_SALARY, gs.SHEET_SALARY)

        ss = await client.open_by_key(gs.BOOK_SALARY)
        ws = await ss.worksheet(gs.SHEET_SALARY)

        values = await ws.get_values('A2:B7')

    return '\n'.join([f'{v[0]} {v[1]}' for v in values if any(v) and v[0] != '']).replace('Итого', '<b>Итого</b>')


async def google_exits(
        offset: int = 0,
        employee: str = None,
        scheduled: bool = False,
        boss: bool = False,
) -> Union[list, tuple, str, None]:
    """`Выходы сотрудников` за период из гугл таблицы.

    :param scheduled: bool возвращает список сотрудников по графику
    :param employee: (optional) сотрудник, используется вместе с offset
    :param offset: (optional)
            0 - сегодня;
            1 - завтра;
            7 - неделя;
            30 - месяц;
            7 + employee - неделя, по сотруднику;
            30 + employee - месяц, по сотруднику.
    :param boss: True, если отчет для администратора
    """

    async with GoogleSheetAsyncClient() as client:
        # ws = await client.worksheet(gs.BOOK_TABLE_ID, gs.SHEET_EXITS)

        ss = await client.open_by_key(gs.BOOK_TABLE_ID)
        ws = await ss.worksheet(gs.SHEET_EXITS)

        values = await ws.get_values()

    if values:

        df = pd.DataFrame(values[1:], columns=values[0])
        df['Дата'] = pd.to_datetime(df['Дата'])
        date_start = None
        date_end = None

        if offset == 0:
            # сегодня
            date_start = datetime.combine(datetime.now(), time(0, 0))
            date_end = datetime.combine(date_start + timedelta(days=1), time(0, 0))

        elif offset == 1:
            # завтра
            date_start = datetime.combine(datetime.now() + timedelta(days=1), time(0, 0))
            date_end = datetime.combine(date_start + timedelta(days=1), time(0, 0))

        elif offset == 30:
            # месяц по сотруднику
            date = get_current_datetime()
            date_start = datetime(date.year, date.month, 1)
            date_end = datetime(date.year, date.month, 1) + timedelta(
                days=calendar.monthrange(date.year, date.month)[1])

        elif offset == 7:
            date_start = datetime.combine(datetime.now(), time(0, 0))
            date_end = datetime.combine(date_start + timedelta(days=7), time(0, 0))

        df = df.loc[
            (df['Сотрудник'] == employee) & (df['Дата'] >= date_start) & (df['Дата'] < date_end)] if employee else \
            df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]

        df['Дата'] = df['Дата'].dt.strftime('%d.%m.%y')
        df = df[['Дата', 'Сотрудник', 'Точка', 'Смена']].sort_values(['Точка', 'Сотрудник'])

        if scheduled:
            return [i[1].split(" ")[0] for i in df.values if i[1] is not None]
        elif not scheduled and not boss and not employee and len(df.values):
            return tuple(f'Дата: {i[0]}\nСотрудник: {i[1]}\nТочка: {i[2]}\nСмена: {i[3]} часов' for i in df.values)
        else:

            if boss:
                data = tuple(f'Дата: {i[0]}\nСотрудник: {i[1]}\nТочка: {i[2]}\nСмена: {i[3]} часов' for i in df.values)
            else:
                data = tuple(f'Дата: {i[0]}\nТочка: {i[2]}\nСмена: {i[3]} часов' for i in df.values)

            if len(data):
                return f'\n{"*" * 15}\n'.join(data)
            else:
                return 'Не могу найти график 😕'
    else:
        return None


async def google_exits_by_point(point: str, s_date: int = 1, e_date: int = 2) -> list:
    """`Chat_id` сотрудников, которые в смене на точке из гугл таблицы.

    :param point: точка
    :param s_date: тип даты старт 0 (сегодня), 1 (завтра)
    :param e_date: тип даты старт 1 (завтра), 2 (послезавтра)
    """
    async with GoogleSheetAsyncClient() as client:
        # ws = await client.worksheet(gs.BOOK_TABLE_ID, gs.SHEET_EXITS)

        ss = await client.open_by_key(gs.BOOK_TABLE_ID)
        ws = await ss.worksheet(gs.SHEET_EXITS)

        values = await ws.get_values()

    df = pd.DataFrame(values[1:], columns=values[0])
    df['Дата'] = pd.to_datetime(df['Дата'])

    # date_start = get_current_datetime(s_date)
    # date_start = datetime(date_start.year, date_start.month, date_start.day)
    # date_end = get_current_datetime(e_date)
    # date_end = datetime(date_end.year, date_end.month, date_end.day)

    date_start = datetime.combine(datetime.now() + timedelta(days=s_date), time(0, 0))
    date_end = datetime.combine(datetime.now() + timedelta(days=e_date), time(0, 0))

    df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end) & (df['Точка'] == point)]
    df = df[['chat_id']].sort_values(['chat_id'])

    if len(df.values):
        return [int(i[0]) for i in df.values if i[0] is not None]


# async def google_exits(employee: str = None, period: int = 1, boss: bool = False) -> str:
#     """`Выходы сотрудников` за период из гугл таблицы.
#
#     :param employee: (optional) сотрудник, не обязательный
#     :param period: (optional) 1 - за месяц, по сотруднику; 2 - 7 дн., по сотруднику; 3 - сегодня; 4 - завтра; 5 - 7 дн.
#     :param boss: True, если отчет для администратора
#     """
#     async with GoogleSheetAsyncClient() as client:
#         # ws = await client.worksheet(gs.BOOK_TABLE_ID, gs.SHEET_EXITS)
#
#         ss = await client.open_by_key(gs.BOOK_TABLE_ID)
#         ws = await ss.worksheet(gs.SHEET_EXITS)
#
#         values = await ws.get_values()
#
#     df = pd.DataFrame(values[1:], columns=values[0])
#     df['Дата'] = pd.to_datetime(df['Дата'])
#
#     if period == 1:
#         date = get_current_datetime()
#         date_start = datetime(date.year, date.month, 1)
#         date_end = datetime(date.year, date.month, 1) + timedelta(days=calendar.monthrange(date.year, date.month)[1])
#         df = df.loc[(df['Сотрудник'] == employee) & (df['Дата'] >= date_start) & (df['Дата'] < date_end)]
#
#     if period == 2:
#         date_start = get_current_datetime()
#         date_start = datetime(date_start.year, date_start.month, date_start.day)
#         date_end = get_current_datetime(7)
#         date_end = datetime(date_end.year, date_end.month, date_end.day)
#         df = df.loc[(df['Сотрудник'] == employee) & (df['Дата'] >= date_start) & (df['Дата'] < date_end)]
#
#     if period == 3:
#         date_start = get_current_datetime()
#         date_start = datetime(date_start.year, date_start.month, date_start.day)
#         date_end = get_current_datetime(1)
#         date_end = datetime(date_end.year, date_end.month, date_end.day)
#         df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]
#
#     if period == 4:
#         date_start = get_current_datetime(1)
#         date_start = datetime(date_start.year, date_start.month, date_start.day)
#         date_end = get_current_datetime(2)
#         date_end = datetime(date_end.year, date_end.month, date_end.day)
#         df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]
#
#     if period == 5:
#         date_start = get_current_datetime()
#         date_start = datetime(date_start.year, date_start.month, date_start.day)
#         date_end = get_current_datetime(7)
#         date_end = datetime(date_end.year, date_end.month, date_end.day)
#         df = df.loc[(df['Дата'] >= date_start) & (df['Дата'] < date_end)]
#
#     df['Дата'] = df['Дата'].dt.strftime('%d.%m.%y')
#     df = df[['Дата', 'Сотрудник', 'Точка', 'Смена']].sort_values(['Дата'])
#
#     if boss:
#         data = tuple(f'Дата: {i[0]}\nСотрудник: {i[1]}\nТочка: {i[2]}\nСмена: {i[3]} часов' for i in df.values)
#     else:
#         data = tuple(f'Дата: {i[0]}\nТочка: {i[2]}\nСмена: {i[3]} часов' for i in df.values)
#
#     if len(data):
#         return f'\n{"*" * 15}\n'.join(data)
#     else:
#         return 'Не могу найти график 😕'


async def google_write_off(sheet_name: str, cols: list) -> list:
    """``Файл списания`` получить массив данных для создания файла списания.

    :param sheet_name: имя листа гугл таблицы
    :param cols: названия столбцов, результирующего отчета
    """
    async with GoogleSheetAsyncClient() as client:
        # ws = await client.worksheet(gs.BOOK_WRITE_OFF_ID, sheet_name)

        ss = await client.open_by_key(gs.BOOK_WRITE_OFF_ID)
        ws = await ss.worksheet(sheet_name)

        values = await ws.get_values()

    df = pd.DataFrame(values[1:], columns=values[0])
    df['Дата'] = pd.to_datetime(df['Дата'])
    return df[cols].sort_values(['Сотрудник', 'Дата']).values


async def google_get_all_records(book_id: str, sheet_name: str) -> List[dict]:
    """Получить все записи со страницы из гугл таблицы.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    """
    async with GoogleSheetAsyncClient() as client:
        ss = await client.open_by_key(book_id)
        ws = await ss.worksheet(sheet_name)
        return await ws.get_all_records(value_render_option=ValueRenderOption.unformatted)


async def google_add_row(book_id: str, sheet_name: str, array: Union[list, tuple]) -> None:
    """`Добавляет строку с данными в конец таблицы` на лист (sheet_name) таблицы по book_id.

    :param book_id: id гугл таблицы
    :param sheet_name: имя листа гугл таблицы
    :param array: массив данных
    """

    async with GoogleSheetAsyncClient() as client:
        ss = await client.open_by_key(book_id)
        ws = await ss.worksheet(sheet_name)
        try:
            await ws.append_row(values=array, value_input_option=ValueInputOption.user_entered, nowait=True)
            logging.info('Google add row: %s:\n%s', ws.title, pformat(array))
        except Exception as ex:
            logging.warning('Google add row:', exc_info=ex)


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

        async with GoogleSheetAsyncClient() as client:
            ss: AsyncioGspreadSpreadsheet = await client.open_by_key(book_id)
            ws: AsyncioGspreadWorksheet = await ss.worksheet(sheet_name)

            cells = await ws.findall(query, in_column=col)

            for cell in cells:
                await ws.update(
                    values=array,
                    range_name=f'{col_s}{cell.row}:{col_f}{cell.row}',
                    value_input_option=ValueInputOption.user_entered,
                    nowait=True
                )  # обновить значение

                logging.info('Google update row: %s!%s %s: %s', ws.title,
                             f"{col_s}{cell.row}:{col_f}{cell.row}", query, array)

            return True
    except Exception as ex:
        logging.warning('Google update row: %s', ex)
        return False


def get_credentials():
    return Credentials.from_service_account_file(gs.credentials).with_scopes(SCOPES)


async def google_authorize_token():
    credentials = get_credentials()
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


async def google_save_file(name, file_path, parent_folder=gs.FOLDER_ID_PHOTO_SAVE, mime_type='image/png'):
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    file_metadata = {
        'name': name,
        'mimeType': mime_type,
        'parents': [parent_folder]
    }

    media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
    return service.files().create(body=file_metadata, media_body=media, fields='id').execute()['id']


async def google_clear_folder(folder_id: str) -> None:
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    results = service.files().list(
        pageSize=1000,
        fields="nextPageToken, files(id, name, mimeType, parents, createdTime)",
        q=f"'{folder_id}' in parents and mimeType contains 'image'").execute()

    # data = []
    # for file in results['files']:
    #     try:
    #         service.files().delete(fileId=file['id']).execute()
    #         data.append(file['id'])
    #     except Exception as ex:
    #         logging.warning('Google clear folder: проблема с id > %s', {file["id"]}, exc_info=ex)
    #         continue
    #
    # data = "\n".join(data)
    # logging.info("Удалили файлы с id:\n %s", data)

    data = [file['id'] for file in results['files']]
    try:
        response = service.files().batchDelete(body={'ids': data}).execute()
        success_count = response.get('deletedIds', [])
        failed_count = response.get('failedErrors', [])
        logging.info("Deleted files with ids:\n %s", '\n'.join(success_count))
        logging.warning("Failed to delete files with ids:\n %s", '\n'.join(failed_count))
    except HttpError as ex:
        if ex.resp.status == 403:
            logging.warning('Google clear folder: problem with id > %s', data, exc_info=ex)
            logging.warning("One or more files cannot be deleted due to access restrictions.")
        else:
            logging.error('Google clear folder: problem with id > %s', data, exc_info=ex)
            raise

# class Gspread:
#     def __init__(self, table_id=None, sheet_name=None):
#         self.table_id = table_id
#         self.sheet_name = sheet_name
#         self.agcm = AsyncioGspreadClientManager(get_credentials)
#         if self.table_id and self.sheet_name:
#             self.sheet = asyncio.get_event_loop().run_until_complete(
#                 get_sheet(self.agcm, self.table_id, self.sheet_name))
#
#     async def append_row(self, row: Union[list, tuple], input_option: str = 'USER_ENTERED') -> None:
#         await self.sheet.append_row(row, value_input_option=input_option, nowait=True)
#
#     async def append_rows(self, rows: list[Union[list, tuple]], input_option: str = 'USER_ENTERED') -> None:
#         await self.sheet.append_rows(rows, value_input_option=input_option)
#
#     async def insert_rows(self, rows: Union[list, tuple], input_option: str = 'USER_ENTERED') -> None:
#         await self.sheet.insert_rows(rows, value_input_option=input_option)
#
#     async def delete_row(self, index: int) -> None:
#         await self.sheet.delete_row(index, nowait=True)
#
#     async def delete_rows(self, index: int, end_index: int) -> None:
#         await self.sheet.delete_rows(index, end_index, nowait=True)
#
#     async def get_all_records(self) -> List[dict]:
#         return await self.sheet.get_all_records()
#
#     async def get_all_values(self) -> List[List[str]]:
#         return await self.sheet.get_all_values()
#
#     async def clear(self) -> None:
#         await self.sheet.clear()
#
#     # @staticmethod
#     # async def save_file(name: str, file_path: str, mime_type: str = 'image/png') -> str:
#     #     return await save_file(name, file_path, mime_type)
#
#     async def delete_file(self, file_id: str) -> None:
#         agc = await self.agcm.authorize()
#         await agc.del_spreadsheet(file_id)
#
#     # @staticmethod
#     # async def clear_folder(folder_id: str) -> None:
#     #     credentials = Credentials.from_service_account_file(g.SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#     #     service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
#     #     results = service.files().list(
#     #         pageSize=1000,
#     #         fields="nextPageToken, files(id, name, mimeType, parents, createdTime)",
#     #         q=f"'{folder_id}' in parents and mimeType contains 'image'").execute()
#     #
#     #     data = []
#     #     for i in results['files']:
#     #         try:
#     #             service.files().delete(fileId=i['id']).execute()
#     #             data.append(i['id'])
#     #         except Exception as e:
#     #             logging.warning(f'Проблема с id {i["id"]} > {e}')
#     #             continue
#     #     data = '\n'.join(data)
#     #     logging.info(f"Удалили id:\n{data}")
#
#     async def worksheet_update(self, array: list[dict]) -> None:
#         await self.sheet.clear()
#         data = (tuple(array[0].keys()),) + tuple(tuple(item.values()) for item in array)
#         await self.sheet.update(range_name=f'A1:ZZZ{str(len(data))}', values=data, value_input_option='USER_ENTERED',
#                                 nowait=True)
