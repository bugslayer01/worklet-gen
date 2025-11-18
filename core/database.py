from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure
from core.config import settings

MONGO_URI = settings.DATABASE_URL
client = MongoClient(MONGO_URI)
db = client[settings.DATABASE_NAME]


thread_schema = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "thread_id",
            "thread_name",
            "cluster_id",
            "count",
            "worklets",
            "created_at",
        ],
        "properties": {
            "thread_id": {
                "bsonType": "string",
                "description": "Unique thread identifier",
            },
            "thread_name": {
                "bsonType": "string",
                "description": "Name of the thread",
            },
            "cluster_id": {
                "bsonType": "string",
                "description": "Identifier of the cluster this thread belongs to",
            },
            "custom_prompt": {
                "bsonType": ["string", "null"],
                "description": "Optional custom prompt text",
            },
            "count": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Count value (non-negative integer)",
            },
            "links": {
                "bsonType": ["array", "null"],
                "items": {"bsonType": "string"},
                "description": "List of related links",
            },
            "files": {
                "bsonType": ["array", "null"],
                "items": {"bsonType": "string"},
                "description": "List of file references",
            },
            "generated": {
                "bsonType": "bool",
                "description": "Flag to indicate whether worklets have been generated for this thread",
            },
            "created_at": {
                "bsonType": "date",
                "description": "Date and time when the thread was created",
            },
            "worklets": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": [
                        "worklet_id",
                        "selected_iteration_index",
                        "iterations",
                    ],
                    "properties": {
                        "worklet_id": {"bsonType": "string"},
                        "selected_iteration_index": {"bsonType": "int"},
                        "iterations": {
                            "bsonType": "array",
                            "items": {
                                "bsonType": "object",
                                "required": [
                                    "iteration_id",
                                    "created_at",
                                    "title",
                                    "problem_statement",
                                    "description",
                                    "challenge_use_case",
                                    "deliverables",
                                    "kpis",
                                    "prerequisites",
                                    "infrastructure_requirements",
                                    "tech_stack",
                                    "milestones",
                                    "references",
                                ],
                                "properties": {
                                    "iteration_id": {"bsonType": "string"},
                                    "created_at": {"bsonType": "date"},
                                    "worklet_id": {"bsonType": "string"},
                                    "reasoning": {"bsonType": ["string", "null"]},
                                    "title": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {"bsonType": "string"},
                                            },
                                        },
                                    },
                                    "problem_statement": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {"bsonType": "string"},
                                            },
                                        },
                                    },
                                    "description": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {"bsonType": "string"},
                                            },
                                        },
                                    },
                                    "challenge_use_case": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {"bsonType": "string"},
                                            },
                                        },
                                    },
                                    "deliverables": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {
                                                    "bsonType": "array",
                                                    "items": {"bsonType": "string"},
                                                },
                                            },
                                        },
                                    },
                                    "kpis": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {
                                                    "bsonType": "array",
                                                    "items": {"bsonType": "string"},
                                                },
                                            },
                                        },
                                    },
                                    "prerequisites": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {
                                                    "bsonType": "array",
                                                    "items": {"bsonType": "string"},
                                                },
                                            },
                                        },
                                    },
                                    "infrastructure_requirements": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {"bsonType": "string"},
                                            },
                                        },
                                    },
                                    "tech_stack": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {"bsonType": "string"},
                                            },
                                        },
                                    },
                                    "milestones": {
                                        "bsonType": "object",
                                        "required": ["selected_index", "iterations"],
                                        "properties": {
                                            "selected_index": {"bsonType": "int"},
                                            "iterations": {
                                                "bsonType": "array",
                                                "items": {"bsonType": "object"},
                                            },
                                        },
                                    },
                                    "references": {
                                        "bsonType": "array",
                                        "items": {
                                            "bsonType": "object",
                                            "required": [
                                                "title",
                                                "link",
                                                "description",
                                                "tag",
                                            ],
                                            "properties": {
                                                "title": {"bsonType": "string"},
                                                "link": {"bsonType": "string"},
                                                "description": {"bsonType": "string"},
                                                "tag": {"bsonType": "string"},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }
}


cluster_schema = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["cluster_id", "name", "created_at"],
        "properties": {
            "cluster_id": {
                "bsonType": "string",
                "description": "Unique cluster identifier",
            },
            "name": {
                "bsonType": "string",
                "description": "Display name for the cluster",
            },
            "created_at": {
                "bsonType": "date",
                "description": "Creation timestamp for the cluster",
            },
            "updated_at": {
                "bsonType": ["date", "null"],
                "description": "Last updated timestamp for the cluster",
            },
        },
    }
}


def _ensure_collection(name, schema, index_builders):
    created = False
    try:
        db.create_collection(name, validator=schema)
        created = True
        print(f"Collection '{name}' created with schema validation.")
    except CollectionInvalid:
        try:
            db.command("collMod", name, validator=schema)
        except OperationFailure as exc:
            print(f"Warning: could not update validator for '{name}': {exc}")
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"Error creating collection '{name}': {exc}")

    for builder in index_builders:
        try:
            builder()
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"Warning: failed creating index on '{name}': {exc}")

    return created


_ensure_collection(
    "threads",
    thread_schema,
    [
        lambda: db.threads.create_index("thread_id", unique=True),
        lambda: db.threads.create_index("cluster_id"),
    ],
)

_ensure_collection(
    "clusters",
    cluster_schema,
    [
        lambda: db.clusters.create_index("cluster_id", unique=True),
        lambda: db.clusters.create_index("name"),
    ],
)
