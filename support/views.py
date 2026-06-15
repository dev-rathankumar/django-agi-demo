from django.shortcuts import get_object_or_404, render
import json
from django.http import JsonResponse, StreamingHttpResponse
import time

from orders.models import Order
from support.agents import run_support_agent
from support.models import Conversation, Message, AgentLog
from django.contrib.admin.views.decorators import staff_member_required
from .event_queue import subscribe, unsubscribe, publish
import threading


def chat(request, order_id):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)

        # time.sleep(5)

        # Get the order — make sure it belongs to logged in user
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Get or create conversation
        # Created on first message — not when Help is clicked
        conversation, created = Conversation.objects.get_or_create(user=request.user, order=order)

        # Save user message to database
        Message.objects.create(conversation=conversation, role="user", content=user_message)

        # Publish message to chat transcript
        event = {"type": "user_message", "message": user_message, "name": request.user.first_name}
        publish(conversation.id, event)

        # Get reply from agent
        reply = run_support_agent(user_message, conversation.id, order.id, request.user.id)

        # Save agent reply to database
        Message.objects.create(conversation=conversation, role="assistant", content=reply)
        return JsonResponse({"reply": reply})

    return JsonResponse({"error": "Invalid method"}, status=405)
        


@staff_member_required
def dashboard(request):
    conversations = Conversation.objects.all().order_by("-created_at")
    print('convers==>', conversations)
    return render(request, "support/dashboard.html", {
        "conversations": conversations
    })


@staff_member_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = conversation.messages.order_by("created_at")
    agentlogs = conversation.agentlogs.order_by("created_at")

    context = {
        "conversation": conversation,
        "messages": messages,
        "agentlogs": agentlogs
    }
    return render(request, "support/conversation_detail.html", context)


@staff_member_required
def conversation_stream(request, conversation_id):
    print("SSE running in thread: ", threading.current_thread().name)
    def event_stream(conversation_id):

        # Subscribe to this conversation's events
        q = subscribe(conversation_id)

        try:
            while True:
                event = q.get() # Wait for next event from queue
                
                # if event.get("type") == "done":
                #     break
    
                # Send event to browser
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            # Always unsubscribe when done
            unsubscribe(conversation_id, q)

    return StreamingHttpResponse(event_stream(conversation_id), content_type="text/event-stream")