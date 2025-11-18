from langgraph.graph import END, StateGraph

from pipeline.graph_nodes import (
    generate_files,
    process_input,
    extract_keywords_domains,
    generate_web_search_queries,
    generate_worklets,
    rank_references,
    web_search,
    references,
)

from pipeline.state import AgentState
from core.constants import *

# Building the state graph
graph_builder = StateGraph(AgentState)

graph_builder.add_node(PROCESS_INPUT, process_input)
graph_builder.add_node(EXTRACT_KEYWORDS_DOMAINS, extract_keywords_domains)
graph_builder.add_node(GENERATE_WEB_SEARCH_QUERIES, generate_web_search_queries)
graph_builder.add_node(GENERATE_WORKLETS, generate_worklets)
graph_builder.add_node(WEB_SEARCH, web_search)
graph_builder.add_node(REFERENCES, references)
graph_builder.add_node(RANK_REFERENCES, rank_references)
graph_builder.add_node(GENERATE_FILES, generate_files)

graph_builder.set_entry_point(PROCESS_INPUT)
graph_builder.add_edge(PROCESS_INPUT, EXTRACT_KEYWORDS_DOMAINS)
graph_builder.add_edge(EXTRACT_KEYWORDS_DOMAINS, GENERATE_WEB_SEARCH_QUERIES)
graph_builder.add_edge(GENERATE_WEB_SEARCH_QUERIES, WEB_SEARCH)
graph_builder.add_edge(WEB_SEARCH, GENERATE_WORKLETS)
graph_builder.add_edge(GENERATE_WORKLETS, REFERENCES)
graph_builder.add_edge(REFERENCES, RANK_REFERENCES)
graph_builder.add_edge(RANK_REFERENCES, GENERATE_FILES)
graph_builder.add_edge(GENERATE_FILES, END)

Pipeline = graph_builder.compile()
