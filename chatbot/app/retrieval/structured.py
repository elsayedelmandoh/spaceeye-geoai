from typing import Any

from chatbot.app.database.connection import get_db_connection


RULE_TRANSLATIONS = {
    "التسليم": ["delivery", "handover"],
    "التأخير": ["delay", "late"],
    "التأخر": ["delay", "late"],
    "الاسترداد": ["refund"],
    "الاسترجاع": ["refund"],
    "الغرامة": ["fine", "penalty"],
    "المخالفة": ["violation"],
    "الضمان": ["financial cover", "cover"],
    "التغطية المالية": ["financial cover"],
    "نسبة التقدم": ["progress"],
    "البناء": ["construction", "building"],
}


def _fetch_dicts(cursor: Any) -> list[dict]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_compound_profile(code: str) -> dict | None:
    con = get_db_connection()

    try:
        rows = _fetch_dicts(
            con.execute(
                """
                SELECT *
                FROM real_compounds
                WHERE UPPER(code) = UPPER(?)
                """,
                [code.strip()],
            )
        )
        return rows[0] if rows else None
    finally:
        con.close()


def get_kpi(code: str, quarter: str | None = None) -> dict | None:
    con = get_db_connection()

    try:
        if quarter:
            query = """
                SELECT *
                FROM real_kpi_values
                WHERE UPPER(code) = UPPER(?)
                  AND UPPER(quarter) = UPPER(?)
            """
            params = [code.strip(), quarter.strip()]
        else:
            query = """
                SELECT *
                FROM real_kpi_values
                WHERE UPPER(code) = UPPER(?)
                ORDER BY quarter DESC
                LIMIT 1
            """
            params = [code.strip()]

        rows = _fetch_dicts(con.execute(query, params))

        if not rows:
            return None

        result = rows[0]
        result["data_type"] = "Derived"
        result["description"] = (
            "Calculated KPI indicators, not raw field measurements."
        )
        return result

    finally:
        con.close()


def get_inspection_priorities(
    quarter: str | None = None,
) -> list[dict]:
    con = get_db_connection()

    try:
        if quarter:
            query = """
                SELECT *
                FROM inspection_cycle_list
                WHERE UPPER(quarter) = UPPER(?)
                ORDER BY cycle_rank
            """
            params = [quarter.strip()]
        else:
            query = """
                SELECT *
                FROM inspection_cycle_list
                ORDER BY cycle_rank
            """
            params = []

        results = _fetch_dicts(con.execute(query, params))

        for item in results:
            item["data_type"] = item.get("origin", "unknown")

        return results

    finally:
        con.close()


def search_rules(keyword: str) -> list[dict]:
    keyword = keyword.strip()

    if not keyword:
        return []

    search_terms = [keyword]

    for arabic_term, translations in RULE_TRANSLATIONS.items():
        if arabic_term in keyword:
            search_terms.extend(translations)

    search_terms = list(dict.fromkeys(search_terms))
    conditions = []
    params = []

    for term in search_terms:
        pattern = f"%{term}%"
        conditions.append(
            "(rule ILIKE ? OR article ILIKE ? OR source ILIKE ? OR rule_id ILIKE ?)"
        )
        params.extend([pattern] * 4)

    con = get_db_connection()

    try:
        query = f"""
            SELECT *
            FROM real_rules
            WHERE {" OR ".join(conditions)}
            ORDER BY rule_id
        """

        results = _fetch_dicts(con.execute(query, params))

        for item in results:
            item["data_type"] = item.get("origin", "unknown")
            item["content_type"] = "Rule summary, not original legal text"

        return results

    finally:
        con.close()


def search_statements(
    keyword: str,
    code: str | None = None,
) -> list[dict]:
    keyword = keyword.strip()

    if not keyword:
        return []

    con = get_db_connection()

    try:
        query = """
            SELECT *
            FROM real_statements
            WHERE (
                detail ILIKE ?
                OR kind ILIKE ?
                OR subtype ILIKE ?
                OR qualifier ILIKE ?
                OR record_id ILIKE ?
                OR statement_id ILIKE ?
                OR CAST(value AS VARCHAR) ILIKE ?
                OR CAST(period_start AS VARCHAR) ILIKE ?
                OR CAST(period_end AS VARCHAR) ILIKE ?
            )
        """

        pattern = f"%{keyword}%"
        params = [pattern] * 9

        if code:
            query += " AND UPPER(code) = UPPER(?)"
            params.append(code.strip())

        query += " ORDER BY published_date DESC"

        results = _fetch_dicts(con.execute(query, params))

        for item in results:
            item["data_type"] = item.get("origin", "unknown")
            item["source_record"] = item.get("record_id")

        return results

    finally:
        con.close()