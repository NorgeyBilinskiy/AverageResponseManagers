from datetime import timedelta

import pandas as pd
from loguru import logger

class ChatResponseAnalyzer:
    """
    A class to analyze chat messages and calculate average response times for managers.
    """

    def __init__(
        self,
        work_start: timedelta,
        work_end: timedelta,
        utc_offset: timedelta,
        ):
        """
        Initialize the analyzer with working hours and output settings.

        Args:
            work_start (timedelta): Start of the working day in UTC.
            work_end (timedelta): End of the working day in UTC.
            utc_offset (timedelta): Offset for Moscow timezone.
        """
        # Время старта и окончания рабочего дня переводим из МСК в 0-ой пояс
        self.work_start = work_start - utc_offset
        self.work_end = work_end - utc_offset

    def _preprocess_messages(
        self,
        df_chat_messages: pd.DataFrame
        ) -> pd.DataFrame:
        """
        Preprocess chat messages by converting timestamps and sorting.

        Args:
            df_chat_messages (pd.DataFrame): Dataframe containing chat messages.

        Returns:
            pd.DataFrame: Preprocessed dataframe.
        """
        # Преобразование временных меток в формат datetime
        df_chat_messages["created_at"] = pd.to_datetime(
            df_chat_messages["created_at"], unit="s", utc=True
            )

        # Сортировка сообщений по entity_id (по клиентам) и времени
        # отправки сообщения в порядке возрастания
        df_chat_messages.sort_values(by=["entity_id", "created_at"], inplace=True)

        return df_chat_messages

    def _filter_messages(self, df_chat_messages: pd.DataFrame) -> pd.DataFrame:
        """
        Filter first messages in each conversation block.

        Args:
            df_chat_messages (pd.DataFrame): Preprocessed chat messages dataframe.

        Returns:
            pd.DataFrame: Filtered dataframe.
        """
        # Создадим новое поле с булевыми значениями, куда занесём метки начала
        # блока сообщений
        df_chat_messages["is_first_in_block"] = (
            # Если в чате с одним клиентом тип сообщения (отправлен клиентом или
            # отправлен менеджером) на текущей строке не равен типу на предыдущей
            (df_chat_messages["type"] != df_chat_messages["type"].shift())
            # ИЛИ
            |
            # Если начался чат с другим клиентом
            (df_chat_messages["entity_id"] != df_chat_messages["entity_id"].shift())
        )
        # Возвращаем отфильтрованный дата-фрейм, где is_first_in_block == True.
        # В результате мы получаем DataFrame, содержащий только первые сообщения
        # из каждого блока, где:
        # - Изменился тип сообщения.
        # Или
        # - Изменился идентификатор сделки.
        return df_chat_messages[df_chat_messages["is_first_in_block"]]

    def _calculate_response_times(
        self,
        filtered_messages: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate response times for outgoing messages.

        Args:
            filtered_messages (pd.DataFrame): Filtered chat messages dataframe.

        Returns:
            pd.DataFrame: Dataframe containing response times.
        """
        responses = []

        # Группируем сообщения по entity_id (ID сделки)
        for _, group in filtered_messages.groupby("entity_id"):

            # Обход сообщений внутри группы
            for i in range(1, len(group)):
                # Предыдущее сообщение
                prev_row = group.iloc[i - 1].copy()
                # Текущее сообщение
                curr_row = group.iloc[i].copy()

                # Время ответа рассчитывается только если:
                # Предыдущее сообщение было входящим, от клиента.
                # Текущее сообщение — исходящее, от менеджера клиенту.
                if (
                    prev_row["type"] == "incoming_chat_message"
                    and
                    curr_row["type"] == "outgoing_chat_message"
                ):

                    # Определение границ рабочего дня на дату отправки сообщения клиентом
                    start_of_day = prev_row["created_at"].replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                        )
                    # К 00.00 прибавляем время начала и окончания данного рабочего дня (по UTC=0)
                    work_start_time = start_of_day + self.work_start
                    work_end_time = start_of_day + self.work_end
                    # Получим значение начала следующего рабочего дня
                    next_work_start_time = work_start_time + timedelta(days=1)

                    # Если сообщение от клиента в рамках текущего рабочего дня
                    if work_start_time <= prev_row["created_at"] <= work_end_time:

                        # И ответ менеджера в рамках рабочего дня
                        if  work_start_time <= curr_row["created_at"] <= work_end_time:
                            # Просто вычитаем разницу во времени
                            adjusted_response_time = curr_row["created_at"] - prev_row["created_at"]

                        # Если менеджер ответил на это сообщение после окончания текущего рабочего дня
                        else:

                            # И после начала следующего рабочего дня
                            if next_work_start_time <= curr_row["created_at"]:
                                # Cчитаем время ответа менеджера, как сумму:
                                adjusted_response_time = (
                                    # Разницы окончания рабочего дня, когда клиент
                                    # задал вопрос, и времени сообщения клиента
                                    (work_end_time - prev_row["created_at"])
                                    +
                                    # Разницы ответа менеджера и начала следующего рабочего дня
                                    (curr_row["created_at"] - next_work_start_time)
                                )

                            # Если менеджер ответил в нерабочее время
                            if  work_end_time < curr_row["created_at"] < next_work_start_time:
                                # Находим разницу между окончанием рабочего дня,
                                # когда клиент написал вопрос, и сообщением клиента
                                # Время ответа менеджера после окончения рабочего дня не учитываем
                                # Так как менеджер проявил инциативу, ответив в нерабочее время:)
                                adjusted_response_time = work_end_time - prev_row["created_at"]

                    # Если же сообщение от клиента в НЕрабочее время
                    else:

                        # Сначала рассмотрим случаи, когда сообщение клиента
                        # и менеджера приходятся на одни сутки для пояса utc=0

                        # И ответ менеджера до начала рабочего дня
                        if curr_row["created_at"] < work_start_time:
                            # Считаем время ответа 0, т.к. менеджер начал работу ещё до рабочего дня
                            adjusted_response_time = timedelta(0)

                        # И ответ менеджера после начала рабочего дня
                        if work_start_time <= curr_row["created_at"] <= work_end_time:
                            # Находим время ответа как разницу между сообщением
                            # менеджера и временем начала рабочего дня
                            adjusted_response_time = curr_row["created_at"] - work_start_time

                        # Теперь рассмотрим случаи, когда сообщение клиента
                        # и менеджера приходятся на разные сутки для пояса utc=0

                        # И ответ менеджера до начала рабочего дня
                        if curr_row["created_at"] < next_work_start_time:
                            # Считаем время ответа 0, т.к. менеджер начал работу ещё до рабочего дня
                            adjusted_response_time = timedelta(0)

                        # И ответ менеджера после начала рабочего дня
                        if next_work_start_time <= curr_row["created_at"]:
                            # Находим время ответа как разницу между сообщением
                            # менеджера и временем начала рабочего дня
                            adjusted_response_time = curr_row["created_at"] - next_work_start_time

                    # Возвращаем ID сделки, менеджера и время ответа
                    responses.append({
                        "entity_id": curr_row["entity_id"],
                        "manager_id": curr_row["created_by"],
                        "response_time": adjusted_response_time
                    })

        responses_df = pd.DataFrame(responses)
        # Преобразование время ответа в минуты
        responses_df["response_time"] = responses_df["response_time"].dt.total_seconds() / 60

        return responses_df

    def _calculate_average_response_time(
        self,
        responses_df: pd.DataFrame,
        df_managers: pd.DataFrame
        ) -> pd.DataFrame:
        """
        Calculate the average response time for each manager.

        Args:
            responses_df (pd.DataFrame): Dataframe with response times.
            df_managers (pd.DataFrame): Dataframe with manager details.

        Returns:
            pd.DataFrame: Dataframe with average response time per manager.
        """
        # Объединение с таблицей менеджеров
        responses_df = responses_df.merge(df_managers, left_on="manager_id", right_on="mop_id")

        # Расчёт среднего времени ответа для каждого менеджера
        average_response_time = responses_df.groupby("name_mop")["response_time"].mean().reset_index()
        # Переименовываем столбец и округляем
        average_response_time.rename(columns={"response_time": "avg_response_time_minutes"}, inplace=True)
        average_response_time["avg_response_time_minutes"] = average_response_time["avg_response_time_minutes"].round(2)

        average_response_time.sort_values(by="avg_response_time_minutes", inplace=True)
        average_response_time = average_response_time.reset_index(drop=True)

        return average_response_time

    def analyze_result(
        self,
        df_chat_messages: pd.DataFrame,
        df_managers: pd.DataFrame,
        df_rops: pd.DataFrame
        ) -> pd.DataFrame:
        """
        Analyze chat messages, calculate average response times

        Args:
            df_chat_messages (pd.DataFrame): Dataframe containing chat messages.
            df_managers (pd.DataFrame): Dataframe containing manager details.
            df_rops (pd.DataFrame): Dataframe containing additional rop details.

        Returns:
            pd.DataFrame: Dataframe with average response time per manager.
        """
        df_chat_messages = self._preprocess_messages(df_chat_messages)
        filtered_messages = self._filter_messages(df_chat_messages)
        responses_df = self._calculate_response_times(filtered_messages)
        average_response_time = self._calculate_average_response_time(responses_df, df_managers)

        df_managers['rop_id'] = df_managers['rop_id'].astype(str)
        merged_df = average_response_time.merge(df_managers[['name_mop', 'rop_id']], on='name_mop', how='left')

        df_rops['rop_id'] = df_rops['rop_id'].astype(str)
        merged_df = merged_df.merge(df_rops[['rop_id', 'rop_name']], on='rop_id', how='left')
        average_response_time = merged_df.drop(columns=['rop_id'])
        average_response_time['rop_name'] = merged_df['rop_name']

        logger.info("The calculations have been carried out successfully.")

        return average_response_time
