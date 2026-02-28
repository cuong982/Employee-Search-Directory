import json
from datetime import datetime, timezone

from app.db.sqlite import get_connection


EMPLOYEES = [
    {
        "organization_id": "org_1",
        "name": "Alice Nguyen",
        "email": "alice.nguyen@org1.example",
        "department": "Engineering",
        "location": "HCM",
        "position": "Senior Backend Engineer",
        "phone": "+84-111-111",
    },
    {
        "organization_id": "org_1",
        "name": "Bob Tran",
        "email": "bob.tran@org1.example",
        "department": "HR",
        "location": "Hanoi",
        "position": "HRBP",
        "phone": "+84-222-222",
    },
    {
        "organization_id": "org_1",
        "name": "Carol Le",
        "email": "carol.le@org1.example",
        "department": "Engineering",
        "location": "HCM",
        "position": "Backend Engineer",
        "phone": "+84-333-333",
    },
    {
        "organization_id": "org_2",
        "name": "David Pham",
        "email": "david.pham@org2.example",
        "department": "Engineering",
        "location": "Singapore",
        "position": "Tech Lead",
        "phone": "+65-111-111",
    },
    {
        "organization_id": "org_2",
        "name": "Emma Vo",
        "email": "emma.vo@org2.example",
        "department": "Operations",
        "location": "Singapore",
        "position": "Ops Manager",
        "phone": "+65-222-222",
    },
]

ORG_COLUMN_CONFIG = {
    "org_1": ["name", "email", "department", "location", "position"],
    "org_2": ["name", "department", "position"],
}


def seed_data_if_empty(db_path: str) -> None:
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(1) AS total FROM employees")
        total = cursor.fetchone()["total"]
        if total > 0:
            return

        now = datetime.now(timezone.utc).isoformat()

        for row in EMPLOYEES:
            cursor.execute(
                """
                INSERT INTO employees (
                    organization_id,
                    name,
                    email,
                    department,
                    location,
                    position,
                    phone,
                    created_at
                ) VALUES (
                    :organization_id,
                    :name,
                    :email,
                    :department,
                    :location,
                    :position,
                    :phone,
                    :created_at
                )
                """,
                {**row, "created_at": now},
            )

        for org_id, columns in ORG_COLUMN_CONFIG.items():
            cursor.execute(
                """
                INSERT OR REPLACE INTO organization_column_config (
                    organization_id,
                    columns_json
                ) VALUES (:organization_id, :columns_json)
                """,
                {
                    "organization_id": org_id,
                    "columns_json": json.dumps(columns),
                },
            )

        connection.commit()
    finally:
        connection.close()
