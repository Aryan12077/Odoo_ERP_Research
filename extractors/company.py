"""
Company Master Extractor

Equivalent SQL:

SELECT

    LPAD(
        COALESCE(parent_company.id, company.id)::TEXT,
        2,
        '0'
    ) AS GROUP_COMPANY_CODE,

    COALESCE(parent_company.name, company.name)
        AS GROUP_COMPANY_NAME,

    LPAD(company.id::TEXT,2,'0')
        AS COMPANY_CODE,

    company.name
        AS COMPANY_NAME,

    currency.name
        AS BASE_CURRENCY_CODE,

    CURRENT_TIMESTAMP
        AS SNAPSHOT_DT

FROM res_company
"""

from datetime import datetime


def extract(client):
    """
    Extract Company Master from Odoo.

    Parameters
    ----------
    client : OdooClient

    Returns
    -------
    list[dict]
    """

    companies = client.search_read(
        model="res.company",
        fields=[
            "id",
            "name",
            "parent_id",
            "currency_id"
        ]
    )

    rows = []

    snapshot = datetime.now()

    for company in companies:

        parent = company.get("parent_id")
        currency = company.get("currency_id")

        rows.append({

            "GROUP_COMPANY_CODE":
                str(parent[0] if parent else company["id"]).zfill(2),

            "GROUP_COMPANY_NAME":
                parent[1] if parent else company["name"],

            "COMPANY_CODE":
                str(company["id"]).zfill(2),

            "COMPANY_NAME":
                company["name"],

            "BASE_CURRENCY_CODE":
                currency[1] if currency else None,

            "SNAPSHOT_DT":
                snapshot
        })

    return rows