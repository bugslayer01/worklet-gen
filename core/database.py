from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from core.config import settings

MONGO_URI = settings.DATABASE_URL
client = MongoClient(MONGO_URI)
db = client[settings.DATABASE_NAME]


thread_schema = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["thread_id", "thread_name", "count", "worklets", "created_at"],
        "properties": {
            "thread_id": {
                "bsonType": "string",
                "description": "Unique thread identifier",
            },
            "thread_name": {
                "bsonType": "string",
                "description": "Name of the thread",
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
                        "worklet_id": {"bsonType": "string"},
                        "title": {"bsonType": "string"},
                        "problem_statement": {"bsonType": "string"},
                        "description": {"bsonType": "string"},
                        "challenge_use_case": {"bsonType": "string"},
                        "deliverables": {"bsonType": "string"},
                        "kpis": {"bsonType": "array", "items": {"bsonType": "string"}},
                        "prerequisites": {
                            "bsonType": "array",
                            "items": {"bsonType": "string"},
                        },
                        "infrastructure_requirements": {"bsonType": "string"},
                        "tech_stack": {"bsonType": "string"},
                        "milestones": {
                            "bsonType": "object",
                            "description": "Milestones over a 6-month period (key-value pairs)",
                        },
                        "references": {
                            "bsonType": "array",
                            "items": {
                                "bsonType": "object",
                                "required": ["title", "link", "description", "tag"],
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
    }
}


try:
    db.create_collection("threads", validator=thread_schema)
    db.threads.create_index("thread_id", unique=True)
    print("Collection 'threads' created with schema validation.")
except CollectionInvalid:
    print("Collection 'threads' already exists.")
except Exception as e:
    print("Error creating collection:", e)
