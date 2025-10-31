import asyncio
import json
from app.socket_handler import sio

pending_responses = {}


async def get_approved_queries(queries: list, thread_id: str) -> list:

    future = asyncio.get_event_loop().create_future()
    pending_responses[thread_id] = future

    @sio.on(f"{thread_id}/web_response")
    async def handle_query_response(sid, data):
        if thread_id in pending_responses:
            pending_responses[thread_id].set_result(data)

    print(f"Sending queries to client {thread_id} for approval: {queries}")

    await sio.emit(f"{thread_id}/web_approval", {"queries": queries})

    try:
        response = await asyncio.wait_for(future, timeout=300)  # 5 minutes timeout
        approved_queries = response.get("queries", [])
    
        print(f"Received approved queries from client {thread_id}: {approved_queries}")
    except asyncio.TimeoutError:
        print(f"Timeout waiting for response from client {thread_id} after 30 minutes.")
        approved_queries = []
    except Exception as e:
        print(
            f"An error occurred while waiting for response from client {thread_id}: {e}"
        )
        approved_queries = []
    finally:
        pending_responses.pop(thread_id, None)
        
    return approved_queries
