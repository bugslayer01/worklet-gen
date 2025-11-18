import asyncio
import json
from app.socket_handler import sio
from core.constants import SWITCHES

pending_responses = {}


async def get_approved_items(domains, keywords, thread_id: str):

    future = asyncio.get_event_loop().create_future()
    pending_responses[thread_id] = future

    @sio.on(f"{thread_id}/topic_response")
    async def handle_query_response(sid, data):
        if thread_id in pending_responses and not pending_responses[thread_id].done():
            pending_responses[thread_id].set_result(data)

    if not SWITCHES["EXTRACT_KEYWORDS_DOMAINS"]:
        message = "Keyword and domain extraction is disabled."
    else:
        message = "Please review and approve the following domains and keywords for the worklet generation process."

    await sio.emit(
        f"{thread_id}/topic_approval",
        # {"domains": domains, "keywords": keywords},
        {"domains": domains, "keywords": keywords, "message": message},
    )
    try:
        response = await asyncio.wait_for(future, timeout=300)  # 5 minutes timeout

        print(response)
        approved_domains = response.get("domains", {}) if response else {}
        approved_keywords = response.get("keywords", {}) if response else {}
    except asyncio.TimeoutError:
        print(
            f"Timeout: No response received from client {thread_id} after 30 minutes."
        )
        approved_domains = {}
        approved_keywords = {}
    except Exception as e:
        print(
            f"An error occurred while waiting for response from client {thread_id}: {e}"
        )
        approved_domains = {}
        approved_keywords = {}
    finally:
        pending_responses.pop(thread_id, None)
        sio.handlers.get("/", {}).pop(f"{thread_id}/topic_response", None)

    final_domains = [
        domain
        for domain_list in approved_domains.values()
        for domain in domain_list
        if domain.strip()
    ]
    final_keywords = [
        keyword
        for keyword_list in approved_keywords.values()
        for keyword in keyword_list
        if keyword.strip()
    ]

    return final_domains, final_keywords
