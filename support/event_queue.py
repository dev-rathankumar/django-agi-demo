import queue

# Store one queque per conversation
# Key: conversation_id
# Value: list of Queue objects (one per browser tab watching)


_subscribers = {}



def subscribe(conversation_id):
    # Browser opens SSE connection - create a queue for it
    q = queue.Queue()
    if conversation_id not in _subscribers:
        _subscribers[conversation_id] = []
    _subscribers[conversation_id].append(q)
    print('_subscribers==>', _subscribers)
    return q


def publish(conversation_id, event):
    # Agent publishes event - send to all subscribers
    if conversation_id in _subscribers:
        for q in _subscribers[conversation_id]:
            q.put(event)


def unsubscribe(conversation_id, q):
    # Browser closes SSE connection - remove queue
    if conversation_id in _subscribers:
        _subscribers[conversation_id].remove(q)
        if not _subscribers[conversation_id]:
            del _subscribers[conversation_id]



# Sentinel value - tells SSE stream to stop
DONE = {"type": "done"}