import dataclasses
import datetime

from django.apps import apps
from django.conf import settings
from django.db import connections
from django.views.generic import TemplateView

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta


@dataclasses.dataclass
class TableInfo:
    name: str
    engine: str
    rows: int
    data_length: int
    index_length: int
    comment: str | None
    stale: bool
    last_vacuum: datetime.datetime | None
    last_autovacuum: datetime.datetime | None
    last_analyze: datetime.datetime | None
    last_autoanalyze: datetime.datetime | None
    live_tuples: int
    dead_tuples: int
    dead_tuples_pct: float | None = None
    total_size_share: float | None = None


class DatabaseTableInfoBaseView(AdminExtraViewMixin, TemplateView):
    """
    A base admin extra view to display database table information for PostgreSQL databases.
    """

    meta = AdminExtraMeta(name='Database Table Info', app_label='db-table-info')
    template_name = 'db_table_info/db_table_info.html'
    db_names: list[str] | None = None

    def get_db_names(self) -> list[str]:
        if self.db_names is not None:
            return self.db_names
        return sorted(settings.DATABASES.keys())

    def get_installed_tables(self) -> list[str]:
        installed_models = apps.get_models(include_auto_created=True)

        installed_tables = {m._meta.db_table for m in installed_models}

        # django_migrations table is not installed, but shouldn't be considered stale:
        installed_tables |= {'django_migrations'}

        return sorted(installed_tables)

    def get_context_data(self, **context) -> dict:
        table_infos = {}
        skipped_dbs = {}
        installed_tables = self.get_installed_tables()

        for cn in self.get_db_names():
            conn = connections[cn]
            if conn.vendor != 'postgresql':
                skipped_dbs[conn.alias] = conn.vendor
                continue

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                        SELECT
                          c.relname AS "name",
                          CASE c.relkind
                            WHEN 'r' THEN 'table'
                            WHEN 'm' THEN 'materialized view'
                            ELSE 'view'
                          END AS "engine",
                          c.reltuples::int as "rows",
                          pg_relation_size(c.oid) AS "data_length",
                          pg_total_relation_size(c.oid) - pg_relation_size(c.oid) AS "index_length",
                          obj_description(c.oid, 'pg_class') AS "comment",
                          NOT(c.relname = ANY(%s)) AS "stale",
                          s.last_vacuum,
                          s.last_autovacuum,
                          s.last_analyze,
                          s.last_autoanalyze,
                          s.n_live_tup AS live_tuples,
                          s.n_dead_tup AS dead_tuples,
                          COALESCE(100.0 * s.n_dead_tup / NULLIF(s.n_live_tup + s.n_dead_tup, 0), 0.0) AS dead_ratio_pct
                        FROM pg_class c
                        JOIN pg_namespace n ON (n.nspname = current_schema() AND n.oid = c.relnamespace)
                        JOIN pg_stat_user_tables s ON (s.relid = c.oid)
                        WHERE relkind IN ('r', 'm', 'v', 'f', 'p')
                        ORDER BY c.relname;
                    """,
                    [installed_tables],
                )
                rows = [TableInfo(*row) for row in cursor]
                table_infos[conn.alias] = rows

                total_live = sum(t.live_tuples for t in rows)
                total_dead = sum(t.dead_tuples for t in rows)
                total_dead_pct = (total_dead / (total_live + total_dead) * 100) if (total_live + total_dead) else 0.0
                total_row = TableInfo(
                    name='TOTAL',
                    engine='',
                    rows=sum(t.rows for t in rows),
                    data_length=sum(t.data_length for t in rows),
                    index_length=sum(t.index_length for t in rows),
                    comment=None,
                    stale=False,
                    last_vacuum=max((t.last_vacuum for t in rows if t.last_vacuum), default=None),
                    last_autovacuum=max((t.last_autovacuum for t in rows if t.last_autovacuum), default=None),
                    last_analyze=max((t.last_analyze for t in rows if t.last_analyze), default=None),
                    last_autoanalyze=max((t.last_autoanalyze for t in rows if t.last_autoanalyze), default=None),
                    live_tuples=total_live,
                    dead_tuples=total_dead,
                    dead_tuples_pct=total_dead_pct,
                )
                total_size = total_row.data_length + total_row.index_length
                for t in rows:
                    t.total_size_share = ((t.data_length + t.index_length) / total_size * 100) if total_size else 0.0
                rows.append(total_row)

        return {
            **super().get_context_data(**context),
            'table_infos': table_infos,
            'skipped_dbs': skipped_dbs,
        }
