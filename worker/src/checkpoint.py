import os

from langgraph.checkpoint.base import BaseCheckpointSaver


def get_checkpointer() -> BaseCheckpointSaver:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        from langgraph.checkpoint.postgres import PostgresSaver

        saver = PostgresSaver.from_conn_string(database_url)
        saver.setup()
        return saver

    from langgraph.checkpoint.sqlite import SqliteSaver

    return SqliteSaver.from_conn_string("apv_worker_dev.sqlite")
